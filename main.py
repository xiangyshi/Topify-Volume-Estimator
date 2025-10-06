import argparse
import sys
from pathlib import Path
import pandas as pd
from model import ChatGPTVolumeEstimator
import util.response_parser as response_parser


class ChatGPTVolumeDriver:
    """
    Driver class for ChatGPT volume estimation pipeline.
    
    Handles data loading, processing, and result presentation for the
    ChatGPT query volume estimation model.
    """
    
    def __init__(self, 
                 lambdas: list = [1.5, 1.0, 1.0, 1.0, 1.0],
                 alpha: float = 0.15):
        """
        Initialize the driver with model parameters.
        
        Args:
            lambdas: Weight vector for logit components
            alpha: Visibility decay parameter
        """
        self.estimator = ChatGPTVolumeEstimator(lambdas=lambdas, alpha=alpha)
        self.results = None
    
    def load_data(self, json_file_path: str) -> dict:
        """
        Load and parse API response data.
        
        Args:
            json_file_path: Path to the JSON file containing API responses
            
        Returns:
            Dictionary containing parsed data
        """
        if not Path(json_file_path).exists():
            raise FileNotFoundError(f"JSON file not found: {json_file_path}")
        
        print(f"Loading data from: {json_file_path}")
        data = response_parser.parse_api_responses(json_file_path)
        
        print(f"✅ Data loaded successfully:")
        print(f"   - Keyword: {data['keyword']}")
        print(f"   - AI Volume: {data['volume']}")
        print(f"   - SERP Results: {len(data['serp_df'])} domains")
        
        return data
    
    def process_data(self, data: dict) -> pd.DataFrame:
        """
        Process SERP data through the ChatGPT volume estimation pipeline.
        
        Args:
            data: Dictionary containing keyword, volume, and SERP data
            
        Returns:
            DataFrame with processed results including domain shares and AI potential volume
        """
        print(f"\n🔄 Processing SERP data for keyword: '{data['keyword']}'")
        
        # Process through the estimator
        processed = self.estimator.fit_transform(data["serp_df"], data["keyword"])
        
        # Calculate AI potential volume
        processed["ai_potential_volume"] = processed["domain_share"] * data["volume"]
        
        # Store results
        self.results = processed
        
        print(f"✅ Processing complete!")
        print(f"   - Processed {len(processed)} domains")
        print(f"   - Total domain share: {processed['domain_share'].sum():.3f}")
        
        return processed
    
    def display_results(self, top_n: int = 10):
        """
        Display the top performing domains by AI potential volume.
        
        Args:
            top_n: Number of top results to display
        """
        if self.results is None:
            print("❌ No results to display. Run process_data() first.")
            return
        
        print(f"\n📊 Top {top_n} Domains by AI Potential Volume:")
        print("=" * 60)
        
        top_results = self.results[["domain", "rank_absolute", "logit", "domain_share", "ai_potential_volume"]] \
            .sort_values(by="ai_potential_volume", ascending=False) \
            .head(top_n)
        
        # Format output
        top_results_display = top_results.copy()
        top_results_display["domain_share"] = top_results_display["domain_share"].apply(lambda x: f"{x:.3f}")
        top_results_display["ai_potential_volume"] = top_results_display["ai_potential_volume"].apply(lambda x: f"{x:.1f}")
        top_results_display["logit"] = top_results_display["logit"].apply(lambda x: f"{x:.2f}")
        
        print(top_results_display.to_string(index=False))
        
        # Summary statistics
        total_volume = self.results["ai_potential_volume"].sum()
        print(f"\n📈 Summary:")
        print(f"   - Total AI Potential Volume: {total_volume:.1f}")
        print(f"   - Top domain share: {top_results.iloc[0]['domain_share']:.3f}")
        print(f"   - Top domain potential: {top_results.iloc[0]['ai_potential_volume']:.1f}")
    
    def get_feature_importance(self) -> dict:
        """Get current feature importance weights."""
        return self.estimator.get_feature_importance()
    
    def update_weights(self, lambdas: list):
        """Update the lambda weights."""
        self.estimator.set_lambdas(lambdas)
        print(f"✅ Updated lambda weights: {lambdas}")
    
    def run_pipeline(self, json_file_path: str, top_n: int = 10):
        """
        Run the complete pipeline from data loading to result display.
        
        Args:
            json_file_path: Path to the JSON file
            top_n: Number of top results to display
        """
        try:
            # Load data
            data = self.load_data(json_file_path)
            
            # Process data
            processed = self.process_data(data)
            
            # Display results
            self.display_results(top_n)
            
            return processed
            
        except Exception as e:
            print(f"❌ Error in pipeline: {e}")
            raise


def main():
    """Main function with CLI argument parsing."""
    parser = argparse.ArgumentParser(
        description="ChatGPT Volume Estimation Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py api_responses_faceless_video_ai_videoinu_com_20251005_144925.json
  python main.py data.json --top 5 --weights 2.0 1.5 1.0 1.2 0.8
  python main.py data.json --alpha 0.2
        """
    )
    
    parser.add_argument(
        "json_file",
        help="Path to the JSON file containing API responses"
    )
    
    parser.add_argument(
        "--top", "-t",
        type=int,
        default=10,
        help="Number of top results to display (default: 10)"
    )
    
    parser.add_argument(
        "--weights", "-w",
        nargs=5,
        type=float,
        default=[1.5, 1.0, 1.0, 1.0, 1.0],
        help="Lambda weights for [vis, sem, auth, feat, est_clicks] (default: 1.5 1.0 1.0 1.0 1.0)"
    )
    
    parser.add_argument(
        "--alpha", "-a",
        type=float,
        default=0.15,
        help="Visibility decay parameter (default: 0.15)"
    )
    
    parser.add_argument(
        "--show-importance",
        action="store_true",
        help="Show feature importance weights"
    )
    
    args = parser.parse_args()
    
    # Validate weights
    if len(args.weights) != 5:
        print("❌ Error: Must provide exactly 5 weight values")
        sys.exit(1)
    
    try:
        # Initialize driver
        driver = ChatGPTVolumeDriver(lambdas=args.weights, alpha=args.alpha)
        
        # Show feature importance if requested
        if args.show_importance:
            importance = driver.get_feature_importance()
            print("🔧 Feature Importance Weights:")
            for feature, weight in importance.items():
                print(f"   - {feature}: {weight}")
            print()
        
        # Run pipeline
        results = driver.run_pipeline(args.json_file, args.top)
        
        print(f"\n🎉 Pipeline completed successfully!")
        
    except Exception as e:
        print(f"❌ Pipeline failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()