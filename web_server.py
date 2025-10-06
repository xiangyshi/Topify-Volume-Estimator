from flask import Flask, render_template, request, jsonify
import pandas as pd
import json
import os
import asyncio
from pathlib import Path
from model import ChatGPTVolumeEstimator
import util.response_parser as response_parser
from api_driver import fetch_keyword_data

app = Flask(__name__)

def check_existing_data(keyword: str, domain: str) -> str:
    """Check if data file already exists for keyword-domain combination."""
    # Create expected filename pattern
    clean_keyword = "".join(c for c in keyword if c.isalnum() or c in (' ', '-', '_')).rstrip()
    clean_keyword = clean_keyword.replace(' ', '_').lower()
    clean_domain = domain.replace('.', '_').lower()
    
    # Look for existing files with this pattern in data/api_responses directory
    pattern = f"data/api_responses/api_responses_{clean_keyword}_{clean_domain}_*.json"
    existing_files = list(Path('.').glob(pattern))
    
    if existing_files:
        # Return the most recent file
        return str(max(existing_files, key=os.path.getctime))
    return None

async def get_or_fetch_data(keyword: str, domain: str, token: str) -> str:
    """Get existing data file or fetch new data from API."""
    # Check if data already exists
    existing_file = check_existing_data(keyword, domain)
    
    if existing_file:
        # Validate the existing file
        try:
            with open(existing_file, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
            parsed_data = response_parser.parse_api_responses_from_dict(json_data)
            
            # Check if the file has valid SERP data
            if parsed_data["serp_df"] is not None and not parsed_data["serp_df"].empty:
                print(f"Using existing data file: {existing_file}")
                return existing_file
            else:
                print(f"Existing file {existing_file} has invalid SERP data, will refetch")
                # Delete the invalid file
                os.remove(existing_file)
                print(f"🗑️ Deleted invalid file: {existing_file}")
        except Exception as e:
            print(f"Error validating existing file {existing_file}: {e}")
            # Delete the corrupted file
            if os.path.exists(existing_file):
                os.remove(existing_file)
                print(f"🗑️ Deleted corrupted file: {existing_file}")
    
    # Fetch new data
    print(f"Fetching new data for keyword: '{keyword}', domain: '{domain}'")
    return await fetch_keyword_data(keyword, domain, token)

@app.route('/')
def index():
    """Serve the main page."""
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    """Analyze keyword and domain combination."""
    try:
        data = request.json
        keyword = data.get('keyword', '').strip()
        domain = data.get('domain', '').strip()
        token = data.get('token', '').strip()
        lambdas = data.get('lambdas', [1.5, 1.0, 1.0, 1.0, 1.0])
        alpha = data.get('alpha', 0.15)
        
        # Validate inputs
        if not keyword:
            return jsonify({'error': 'Keyword is required'}), 400
        if not domain:
            return jsonify({'error': 'Domain is required'}), 400
        if not token:
            return jsonify({'error': 'DataForSEO API token is required'}), 400
        if len(lambdas) != 5:
            return jsonify({'error': 'Must provide exactly 5 lambda values'}), 400
        
        # Get or fetch data
        try:
            data_file = asyncio.run(get_or_fetch_data(keyword, domain, token))
        except Exception as e:
            return jsonify({'error': f'Failed to fetch data: {str(e)}'}), 500
        
        # Parse the data file
        try:
            with open(data_file, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
            parsed_data = response_parser.parse_api_responses_from_dict(json_data)
            
            # Debug: Check if we have valid data
            if parsed_data["serp_df"] is None:
                return jsonify({'error': 'No SERP data found in API response. This may be due to API rate limits or account issues. Please try again later or contact DataForSEO support.'}), 500
            if parsed_data["keyword"] is None:
                return jsonify({'error': 'No keyword data found in API response. This may be due to API rate limits or account issues. Please try again later or contact DataForSEO support.'}), 500
            if parsed_data["volume"] == 0:
                return jsonify({'error': 'No search volume data found in API response. This may be due to API rate limits or account issues. Please try again later or contact DataForSEO support.'}), 500
                
        except Exception as e:
            return jsonify({'error': f'Failed to parse data: {str(e)}'}), 500
        
        # Initialize estimator with provided parameters
        estimator = ChatGPTVolumeEstimator(lambdas=lambdas, alpha=alpha)
        
        # Process data
        processed = estimator.fit_transform(parsed_data["serp_df"], parsed_data["keyword"])
        processed["ai_potential_volume"] = processed["domain_share"] * parsed_data["volume"]
        
        # Group by domain to handle duplicates
        domain_stats = processed.groupby('domain').agg({
            'rank_absolute': ['min', 'max', 'count', 'mean'],
            'logit': ['min', 'max', 'mean'],
            'domain_share': 'sum',
            'ai_potential_volume': 'sum'
        }).round(3)
        
        # Flatten column names
        domain_stats.columns = ['_'.join(col).strip() for col in domain_stats.columns]
        domain_stats = domain_stats.reset_index()
        
        # Rename columns for clarity
        domain_stats = domain_stats.rename(columns={
            'rank_absolute_min': 'best_rank',
            'rank_absolute_max': 'worst_rank', 
            'rank_absolute_count': 'appearances',
            'rank_absolute_mean': 'avg_rank',
            'logit_min': 'min_logit',
            'logit_max': 'max_logit',
            'logit_mean': 'avg_logit',
            'domain_share_sum': 'total_domain_share',
            'ai_potential_volume_sum': 'total_ai_volume'
        })
        
        # Sort by total AI potential volume
        results = domain_stats.sort_values(by="total_ai_volume", ascending=False)
        
        # Calculate summary metrics
        total_volume = results["total_ai_volume"].sum()
        top_share = results.iloc[0]['total_domain_share'] if len(results) > 0 else 0
        
        # Get target domain statistics
        target_domain_stats = None
        if domain in results['domain'].values:
            target_row = results[results['domain'] == domain].iloc[0]
            target_domain_stats = {
                'domain': target_row['domain'],
                'appearances': int(target_row['appearances']),
                'best_rank': int(target_row['best_rank']),
                'worst_rank': int(target_row['worst_rank']),
                'avg_rank': round(target_row['avg_rank'], 1),
                'total_domain_share': round(target_row['total_domain_share'], 3),
                'total_ai_volume': round(target_row['total_ai_volume'], 1),
                'avg_logit': round(target_row['avg_logit'], 2),
                'max_logit': round(target_row['max_logit'], 2),
                'min_logit': round(target_row['min_logit'], 2)
            }
        
        # Prepare normal results (individual SERP entries)
        normal_results = processed[["domain", "rank_absolute", "logit", "domain_share", "ai_potential_volume"]].copy() \
            .sort_values(by="ai_potential_volume", ascending=False)
        
        # Convert to JSON-serializable format
        results_json = results.to_dict('records')
        normal_results_json = normal_results.to_dict('records')
        
        return jsonify({
            'success': True,
            'keyword': parsed_data['keyword'],
            'domain': domain,
            'volume': parsed_data['volume'],
            'total_volume': total_volume,
            'top_share': top_share,
            'data_file': data_file,
            'results': results_json,
            'normal_results': normal_results_json,
            'target_domain_stats': target_domain_stats,
            'feature_importance': estimator.get_feature_importance()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/config', methods=['GET'])
def get_config():
    """Get default configuration."""
    return jsonify({
        'lambdas': [1.5, 1.0, 1.0, 1.0, 1.0],
        'alpha': 0.15,
        'feature_names': ['visibility', 'semantic', 'authority', 'features', 'estimated_clicks']
    })

@app.route('/api/check-data', methods=['POST'])
def check_data():
    """Check if data exists for keyword-domain combination."""
    try:
        data = request.json
        keyword = data.get('keyword', '').strip()
        domain = data.get('domain', '').strip()
        
        if not keyword or not domain:
            return jsonify({'error': 'Keyword and domain are required'}), 400
        
        existing_file = check_existing_data(keyword, domain)
        
        return jsonify({
            'exists': existing_file is not None,
            'file': existing_file,
            'message': f"Using existing data: {existing_file}" if existing_file else "Will fetch new data from API"
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    os.makedirs('templates', exist_ok=True)
    
    # Get port from environment variable (for Render.com)
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') != 'production'
    
    print(f"Starting server on port {port}")
    print(f"Debug mode: {debug}")
    
    # Run the app
    app.run(host='0.0.0.0', port=port, debug=debug)
