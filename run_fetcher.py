"""
Scheduler for running the stock data fetcher at regular intervals.
"""
import logging
import time
import os
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from app.data.data_fetch import fetch_stock_data, resample_data, is_market_open
from app.data.storage import save_to_sqlite, save_to_parquet

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("fetcher.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("run_fetcher")

# Default tickers if not specified in environment or arguments
DEFAULT_TICKERS = ["SPY", "AAPL", "MSFT", "GOOGL", "AMZN"]

# Get tickers from environment variable if available
ENV_TICKERS = os.environ.get('TICKERS')
if ENV_TICKERS:
    TICKERS = ENV_TICKERS.split(',')
else:
    TICKERS = DEFAULT_TICKERS

# Create data directory
DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)


def fetch_and_store_data(tickers=None, interval="1m", resample_to="10T"):
    """
    Fetch data for specified tickers, resample, and store.
    Only runs if the market is open.
    
    Args:
        tickers (list): List of ticker symbols
        interval (str): Data interval for fetching
        resample_to (str): Interval to resample to
        
    Returns:
        dict: Dictionary with results for each ticker
    """
    if not is_market_open():
        logger.info("Market is closed, skipping data fetch")
        return {}
        
    if tickers is None:
        tickers = TICKERS
        
    logger.info(f"Starting data fetch for {len(tickers)} tickers")
    
    results = {}
    
    for ticker in tickers:
        try:
            # Fetch data
            df = fetch_stock_data(ticker, interval=interval, period="7d")
            
            if df.empty:
                logger.warning(f"No data retrieved for {ticker}, skipping")
                results[ticker] = False
                continue
                
            # Store raw data
            success_raw = save_to_sqlite(df, table_name=f"stock_data_{interval}")
            
            # Resample if requested
            if resample_to:
                resampled_df = resample_data(df, interval=resample_to)
                
                # Store resampled data
                resample_table = f"stock_data_{resample_to}"
                success_resampled = save_to_sqlite(resampled_df, table_name=resample_table)
                parquet_success = save_to_parquet(resampled_df, ticker, interval=resample_to)
                
                results[ticker] = success_raw and success_resampled
            else:
                results[ticker] = success_raw
                
            logger.info(f"Successfully processed data for {ticker}")
            
        except Exception as e:
            logger.error(f"Error processing {ticker}: {str(e)}")
            results[ticker] = False
    
    # Log summary
    success_count = sum(1 for result in results.values() if result)
    logger.info(f"Completed data fetch cycle: {success_count}/{len(tickers)} successful")
    
    return results


def clean_old_data(days_to_keep=30):
    """
    Clean up old data to prevent database bloat.
    
    Args:
        days_to_keep (int): Number of days of data to retain
        
    Returns:
        int: Number of rows deleted
    """
    try:
        import sqlite3
        
        # Connect to database
        db_path = DATA_DIR / "stock_data.db"
        
        if not db_path.exists():
            logger.warning(f"Database not found at {db_path}")
            return 0
            
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Calculate cutoff date
        cutoff_date = (datetime.now() - timedelta(days=days_to_keep)).strftime('%Y-%m-%d')
        
        # Delete old data from 1-minute table
        cursor.execute(
            "DELETE FROM stock_data_1min WHERE Datetime < ?",
            (cutoff_date,)
        )
        deleted_1min = cursor.rowcount
        
        # Delete old data from 10-minute table
        cursor.execute(
            "DELETE FROM stock_data_10min WHERE Datetime < ?",
            (cutoff_date,)
        )
        deleted_10min = cursor.rowcount
        
        conn.commit()
        conn.close()
        
        total_deleted = deleted_1min + deleted_10min
        logger.info(f"Cleaned up {total_deleted} rows of data older than {cutoff_date}")
        
        return total_deleted
        
    except Exception as e:
        logger.error(f"Error cleaning old data: {str(e)}")
        return 0


def run_scheduler(interval_minutes=10, tickers=None):
    """
    Start the scheduler for periodic data fetching.
    
    Args:
        interval_minutes (int): Interval between fetches in minutes
        tickers (list): List of ticker symbols
    """
    scheduler = BackgroundScheduler()
    
    # Run every X minutes during market hours
    cron_pattern = f"*/{interval_minutes} * * * 1-5"  # Every X minutes, Monday-Friday
    
    scheduler.add_job(
        lambda: fetch_and_store_data(tickers),
        CronTrigger.from_crontab(cron_pattern),
        id="fetch_stock_data",
        name=f"Fetch Stock Data Every {interval_minutes} Minutes"
    )
    
    # Schedule daily data cleanup at midnight
    scheduler.add_job(
        clean_old_data,
        CronTrigger.from_crontab("0 0 * * *"),  # Every day at midnight
        id="clean_data",
        name="Clean Old Data"
    )
    
    logger.info(f"Starting scheduler to fetch data every {interval_minutes} minutes during market hours")
    scheduler.start()
    
    try:
        # Initial fetch
        if is_market_open():
            fetch_and_store_data(tickers)
        else:
            logger.info("Market is currently closed, waiting for next scheduled fetch")
        
        # Keep the script running
        while True:
            time.sleep(60)
            
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scheduler shutdown requested")
        scheduler.shutdown()
        logger.info("Scheduler shut down successfully")


def run_once(tickers=None):
    """
    Run the data fetch once for testing purposes.
    
    Args:
        tickers (list): List of ticker symbols
    """
    logger.info("Running one-time data fetch")
    fetch_and_store_data(tickers)
    logger.info("One-time fetch completed")


def main():
    """Parse arguments and run the fetcher."""
    parser = argparse.ArgumentParser(description="Fetch stock data at regular intervals")
    
    parser.add_argument("--tickers", nargs="+", help="List of ticker symbols")
    parser.add_argument("--interval", type=int, default=10, help="Fetch interval in minutes")
    parser.add_argument("--once", action="store_true", help="Run once without scheduling")
    parser.add_argument("--clean", action="store_true", help="Clean up old data")
    parser.add_argument("--keep-days", type=int, default=30, help="Days of data to keep when cleaning")
    
    args = parser.parse_args()
    
    # Override tickers if specified
    tickers = args.tickers if args.tickers else TICKERS
    
    if args.clean:
        clean_old_data(args.keep_days)
    elif args.once:
        run_once(tickers)
    else:
        run_scheduler(args.interval, tickers)


if __name__ == "__main__":
    main()
