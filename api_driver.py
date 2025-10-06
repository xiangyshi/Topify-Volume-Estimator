import asyncio
import argparse
import sys
import os
from datetime import datetime
from util.dfs_client import DataForSEOClient
from constants.endpoints import Endpoints
import json
from typing import List, Optional

def create_unique_filename(keyword: str, domain: str, base_name: str = "api_responses") -> str:
    """Create a unique filename with timestamp and incremental ID"""
    # Clean keyword and domain for filename
    clean_keyword = "".join(c for c in keyword if c.isalnum() or c in (' ', '-', '_')).rstrip()
    clean_keyword = clean_keyword.replace(' ', '_').lower()
    clean_domain = domain.replace('.', '_').lower()
    
    # Get current timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Create base filename
    base_filename = f"{base_name}_{clean_keyword}_{clean_domain}_{timestamp}"
    
    # Ensure data/api_responses directory exists
    os.makedirs("data/api_responses", exist_ok=True)
    
    # Check if file exists and increment if needed
    filename = f"data/api_responses/{base_filename}.json"
    counter = 1
    while os.path.exists(filename):
        filename = f"data/api_responses/{base_filename}_{counter:03d}.json"
        counter += 1
    
    return filename

def save_to_json_file(filename: str, data: List[dict]) -> None:
    """Save data to a new JSON file"""
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

async def fetch_keyword_data(keyword: str, domain: str, token: str, custom_output_file: Optional[str] = None) -> str:
    """
    Fetch comprehensive keyword data from DataForSEO API
    
    Args:
        keyword: The keyword to analyze (e.g., "faceless video ai")
        domain: The target domain (e.g., "videoinu.com")
        token: DataForSEO API token (base64 encoded)
        custom_output_file: Optional custom output file path
    
    Returns:
        The filename where data was saved
    """
    client = DataForSEOClient(token)
    
    # Create unique filename if not provided
    if custom_output_file:
        output_file = custom_output_file
    else:
        output_file = create_unique_filename(keyword, domain)
    
    print(f"Output file: {output_file}")
    
    # Use the client's comprehensive analysis method
    all_data = await client.fetch_keyword_analysis(keyword, domain)
    
    # Check if we have valid data (at least SERP data is required)
    has_valid_serp = all_data.get("serp_google_organic_live_advanced") is not None
    has_valid_keyword = all_data.get("ai_keyword_search_volume") is not None
    
    if not has_valid_serp:
        print("❌ No valid SERP data collected - this is required for analysis")
        # Delete the file if it exists (in case of partial failure)
        if os.path.exists(output_file):
            os.remove(output_file)
            print(f"🗑️ Deleted invalid file: {output_file}")
        raise Exception("Failed to collect required SERP data")
    
    # Convert to the expected format for backward compatibility
    formatted_data = []
    for endpoint, data in all_data.items():
        if data is not None:
            formatted_data.append({"endpoint": endpoint, "data": data})
    
    # Save all data to the unique file
    save_to_json_file(output_file, formatted_data)
    
    if has_valid_keyword:
        print(f"\n🎉 Data collection complete! Results saved to '{output_file}'")
    else:
        print(f"\n⚠️ Partial data collection complete (no keyword volume data). Results saved to '{output_file}'")
    
    return output_file

async def main():
    """Main function with CLI argument parsing"""
    parser = argparse.ArgumentParser(
        description="Fetch keyword analysis data from DataForSEO API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python api_driver.py "faceless video ai" "videoinu.com" --token "YOUR_TOKEN"
  python api_driver.py "best headphones" "amazon.com" --output "headphones_data.json" --token "YOUR_TOKEN"
  python api_driver.py "python tutorial" "python.org" --token "YOUR_TOKEN"
  
Note: If --token is not provided, you will be prompted to enter it securely.
        """
    )
    
    parser.add_argument(
        "keyword", 
        help="The keyword to analyze (e.g., 'faceless video ai')"
    )
    
    parser.add_argument(
        "domain", 
        help="The target domain to analyze (e.g., 'videoinu.com')"
    )
    
    parser.add_argument(
        "--output", "-o",
        help="Custom output JSON file path (if not provided, auto-generates unique filename)"
    )
    
    parser.add_argument(
        "--token", "-t",
        help="DataForSEO API token (base64 encoded). If not provided, will prompt for input."
    )
    
    args = parser.parse_args()
    
    # Validate inputs
    if not args.keyword.strip():
        print("❌ Error: Keyword cannot be empty")
        sys.exit(1)
    
    if not args.domain.strip():
        print("❌ Error: Domain cannot be empty")
        sys.exit(1)
    
    # Get API token
    token = args.token
    if not token:
        print("\n🔑 DataForSEO API Token Required")
        print("You can get your token from: https://app.dataforseo.com/api-dashboard")
        token = input("Enter your DataForSEO API token: ").strip()
        
        if not token:
            print("❌ Error: API token is required")
            sys.exit(1)
    
    # Run the data fetching
    output_file = await fetch_keyword_data(args.keyword.strip(), args.domain.strip(), token, args.output)
    print(f"\n📁 Final output file: {output_file}")

if __name__ == "__main__":
    asyncio.run(main())
