"""
Script to update technical indicators for stock data.
"""
import logging
import argparse
import pandas as pd
from app.data.storage import load_from_sqlite, save_to_sqlite
from app.indicators.tech import update_indicators

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("indicator_update.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("update_indicators")

# List of default tickers
DEFAULT_TICKERS = ["SPY", "AAPL", "MSFT", "GOOGL", "AMZN"]


def update_indicators_for_ticker(ticker, interval="10min"):
    """
    Update technical indicators for a specific ticker.
    
    Args:
        ticker (str): Stock ticker symbol
        interval (str): Data interval identifier
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        logger.info(f"Updating indicators for {ticker} ({interval})")
        
        # Load data
        table_name = "stock_data_10min" if interval == "10min" else "stock_data_1min"
        
        # Load raw price data
        df = load_from_sqlite(table_name=table_name, ticker=ticker)
        
        if df.empty:
            logger.warning(f"No data found for {ticker} in {table_name}")
            return False
            
        # Load existing indicators data if available
        existing_df = load_from_sqlite(table_name=f"indicators_{interval}", ticker=ticker)
        
        # Update indicators
        result_df = update_indicators(df, existing_df)
        
        # Save updated indicators
        if not result_df.empty:
            save_to_sqlite(result_df, table_name=f"indicators_{interval}")
            logger.info(f"Successfully updated indicators for {ticker} ({interval})")
            return True
        else:
            logger.warning(f"No indicators updated for {ticker}")
            return False
            
    except Exception as e:
        logger.error(f"Error updating indicators for {ticker}: {str(e)}")
        return False


def update_all_indicators(tickers=None, interval="10min"):
    """
    Update indicators for all specified tickers.
    
    Args:
        tickers (list): List of ticker symbols
        interval (str): Data interval identifier
        
    Returns:
        dict: Dictionary with results for each ticker
    """
    if tickers is None:
        tickers = DEFAULT_TICKERS
        
    results = {}
    
    for ticker in tickers:
        results[ticker] = update_indicators_for_ticker(ticker, interval)
        
    # Log summary
    success_count = sum(1 for result in results.values() if result)
    logger.info(f"Updated indicators for {success_count}/{len(tickers)} tickers")
    
    return results


def main():
    """Main function to parse arguments and run the indicator update."""
    parser = argparse.ArgumentParser(description="Update technical indicators for stock data")
    parser.add_argument("--tickers", nargs="+", help="List of ticker symbols")
    parser.add_argument("--interval", choices=["1min", "10min"], default="10min", help="Data interval")
    
    args = parser.parse_args()
    
    # Update indicators
    update_all_indicators(args.tickers, args.interval)


if __name__ == "__main__":
    main()
