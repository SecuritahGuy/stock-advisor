#!/usr/bin/env python
"""
Update stock data for all tickers in the portfolio.
This script fetches current price data for all tickers in the portfolio
to ensure that the portfolio valuation can be calculated correctly.
"""

import logging
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add project root to path
sys.path.append(str(Path(__file__).parent))

# Import app modules
from app.portfolio.portfolio import Portfolio
from app.data.data_fetch import fetch_stock_data

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("update_portfolio_data.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("update_portfolio_data")

def fetch_portfolio_stock_data(period='1mo', interval='1d'):
    """
    Fetch stock data for all tickers in the portfolio.
    
    Args:
        period (str): Time period for stock data (default: '1mo')
        interval (str): Data interval (default: '1d')
    """
    try:
        # Initialize portfolio
        portfolio = Portfolio(name="default")
        
        # Get positions
        positions = portfolio.get_positions()
        
        if positions.empty:
            logger.warning("No positions found in the portfolio")
            return
        
        # Get unique tickers
        tickers = positions['ticker'].unique()
        logger.info(f"Found {len(tickers)} unique tickers in the portfolio")
        
        # Fetch data for each ticker
        successful = 0
        failed = 0
        
        for ticker in tickers:
            try:
                logger.info(f"Fetching data for {ticker}...")
                data = fetch_stock_data(ticker, period=period, interval=interval)
                
                if data is not None and not data.empty:
                    logger.info(f"Successfully fetched {len(data)} rows of data for {ticker}")
                    successful += 1
                else:
                    logger.warning(f"No data returned for {ticker}")
                    failed += 1
            except Exception as e:
                logger.error(f"Error fetching data for {ticker}: {str(e)}")
                failed += 1
        
        logger.info(f"Data fetch complete. Successfully fetched data for {successful} tickers, failed for {failed} tickers.")
        
    except Exception as e:
        logger.error(f"Error updating portfolio stock data: {str(e)}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Update stock data for portfolio tickers")
    parser.add_argument("--period", default="1mo", help="Time period for stock data (default: 1mo)")
    parser.add_argument("--interval", default="1d", help="Data interval (default: 1d)")
    
    args = parser.parse_args()
    
    logger.info(f"Starting update of portfolio stock data with period={args.period}, interval={args.interval}")
    fetch_portfolio_stock_data(period=args.period, interval=args.interval)
    logger.info("Portfolio stock data update complete")
