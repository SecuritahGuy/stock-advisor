"""
Command-line interface for stock discovery
"""
import argparse
import logging
import os
import sys
from pathlib import Path
from datetime import datetime

# Set up path to allow importing from parent directory
sys.path.insert(0, str(Path(os.path.dirname(__file__)).parent))

from app.screener.discover import (
    find_candidates, save_candidates, get_candidates, update_tickers_env, STRATEGIES
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('discovery.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Stock Discovery Tool')
    parser.add_argument('--strategy', type=str, choices=list(STRATEGIES.keys()),
                      default='oversold_reversals',
                      help='Strategy to use for finding stock candidates')
    parser.add_argument('--limit', type=int, default=20,
                      help='Maximum number of candidates to return')
    parser.add_argument('--min-price', type=float, default=10,
                      help='Minimum stock price')
    parser.add_argument('--max-price', type=float, default=150,
                      help='Maximum stock price')
    parser.add_argument('--min-market-cap', type=float, default=500,
                      help='Minimum market cap in millions')
    parser.add_argument('--update-env', action='store_true',
                      help='Update TICKERS in .env file with top candidates')
    parser.add_argument('--max-tickers', type=int, default=30,
                      help='Maximum number of tickers to include in .env')
    parser.add_argument('--list', action='store_true',
                      help='List recently discovered candidates')
    parser.add_argument('--days', type=int, default=30,
                      help='Number of days to look back when listing candidates')
    parser.add_argument('--top', type=int, default=None,
                      help='Show only top N candidates by market cap')
    
    return parser.parse_args()

def main():
    """Main function for stock discovery CLI"""
    args = parse_args()
    
    if args.list:
        # List candidates mode
        df = get_candidates(days=args.days, top_n=args.top, min_market_cap=args.min_market_cap)
        if df.empty:
            print("No candidates found in the specified time range.")
            return
        
        # Print candidates in a formatted table
        print(f"\n{'='*80}")
        print(f"STOCK CANDIDATES DISCOVERED IN THE LAST {args.days} DAYS")
        print(f"{'='*80}")
        
        # Format the table
        display_cols = ['Ticker', 'Company', 'Sector', 'Industry', 'Price', 'Change', 'Volume', 
                       'Market Cap', 'strategy_name', 'discovered_at']
        # Filter to only columns that exist
        display_cols = [col for col in display_cols if col in df.columns]
        
        # Format dates
        if 'discovered_at' in df.columns:
            df['discovered_at'] = df['discovered_at'].dt.strftime('%Y-%m-%d')
        
        # Print the table
        print(df[display_cols].to_string(index=False))
        print(f"\nTotal: {len(df)} candidates")
        
    else:
        # Discovery mode
        logger.info(f"Finding candidates using {STRATEGIES[args.strategy]['name']} strategy...")
        df = find_candidates(
            strategy=args.strategy,
            limit=args.limit,
            min_price=args.min_price,
            max_price=args.max_price
        )
        
        if df is None or df.empty:
            logger.error("No candidates found. Check connection or try different filter settings.")
            return
        
        # Save candidates
        save_candidates(df, append=True)
        
        # Display results
        print(f"\n{'='*80}")
        print(f"DISCOVERED {len(df)} CANDIDATES WITH {STRATEGIES[args.strategy]['name'].upper()} STRATEGY")
        print(f"{'='*80}")
        
        # Select display columns based on what's available
        all_possible_cols = ['Ticker', 'Company', 'Sector', 'Industry', 'Price', 'Change', 'Volume', 'Market Cap']
        display_cols = [col for col in all_possible_cols if col in df.columns]
        
        print(df[display_cols].to_string(index=False))
        
        # Update TICKERS in .env if requested
        if args.update_env:
            if df is not None and not df.empty:
                # Filter candidates by market cap if specified
                if args.min_market_cap:
                    # Filter logic here...
                    pass
                    
                # Update .env
                success = update_tickers_env(df, max_tickers=args.max_tickers)
                if success:
                    logger.info("Successfully updated TICKERS in .env file")
                else:
                    logger.error("Failed to update TICKERS in .env file")
            else:
                logger.warning("No candidates to add to .env")

if __name__ == '__main__':
    main()
