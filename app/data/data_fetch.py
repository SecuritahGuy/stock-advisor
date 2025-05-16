"""
Stock data acquisition module for fetching and storing stock data.
"""
import logging
import time
from datetime import datetime, timedelta
import pandas as pd
import yfinance as yf

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("app_data_fetch.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("data_fetch")


def fetch_stock_data(ticker, interval="1m", period="7d", max_retries=3, backoff_factor=2):
    """
    Fetch stock data from Yahoo Finance with retry logic.
    
    Args:
        ticker (str): Stock ticker symbol
        interval (str): Data interval (e.g., "1m", "5m", "1h", "1d")
        period (str): Lookback period (e.g., "1d", "5d", "1mo", "3mo", "1y", "max")
        max_retries (int): Maximum number of retry attempts
        backoff_factor (int): Exponential backoff multiplier
        
    Returns:
        pd.DataFrame: DataFrame containing stock data
    """
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            logger.info(f"Fetching {ticker} data with interval={interval}, period={period}")
            ticker_obj = yf.Ticker(ticker)
            df = ticker_obj.history(interval=interval, period=period)
            
            # Check if data is empty
            if df.empty:
                logger.warning(f"No data returned for {ticker}")
                return pd.DataFrame()
                
            # Reset index to make Date a column
            df = df.reset_index()
            
            # Add ticker column
            df['ticker'] = ticker
            
            logger.info(f"Successfully fetched {len(df)} rows for {ticker}")
            return df
            
        except Exception as e:
            retry_count += 1
            wait_time = backoff_factor ** retry_count
            logger.warning(f"Error fetching {ticker}: {str(e)}. Retrying in {wait_time}s... (Attempt {retry_count}/{max_retries})")
            time.sleep(wait_time)
    
    logger.error(f"Failed to fetch data for {ticker} after {max_retries} attempts")
    return pd.DataFrame()


def resample_data(df, interval="10T"):
    """
    Resample data to specified interval.
    
    Args:
        df (pd.DataFrame): DataFrame with stock data
        interval (str): Target interval (e.g., "10T" for 10 minutes)
        
    Returns:
        pd.DataFrame: Resampled DataFrame
    """
    if df.empty:
        return df
        
    # Make sure Datetime is the index for resampling
    if 'Datetime' in df.columns:
        df = df.set_index('Datetime')
    elif 'Date' in df.columns:
        df = df.set_index('Date')
        
    # Resample data
    logger.info(f"Resampling data to {interval} interval")
    resampled = df.resample(interval).agg({
        'Open': 'first',
        'High': 'max',
        'Low': 'min',
        'Close': 'last',
        'Volume': 'sum'
    })
    
    # Reset index
    resampled = resampled.reset_index()
    
    # Copy ticker if present
    if 'ticker' in df.columns:
        ticker = df['ticker'].iloc[0]
        resampled['ticker'] = ticker
        
    logger.info(f"Resampled to {len(resampled)} rows")
    return resampled


def is_market_open():
    """
    Check if the US stock market is currently open.
    Very simplified - doesn't account for holidays.
    
    Returns:
        bool: True if market is open, False otherwise
    """
    now = datetime.now()
    
    # Market is open 9:30 AM - 4:00 PM Eastern Time
    # We're not handling timezone conversion here - would need to add pytz for proper handling
    hour = now.hour
    minute = now.minute
    
    # Check if it's a weekday (0 = Monday, 4 = Friday)
    is_weekday = 0 <= now.weekday() <= 4
    
    # This is simplified - would need proper timezone handling for production
    is_market_hours = (9 < hour < 16) or (hour == 9 and minute >= 30)
    
    return is_weekday and is_market_hours


def main():
    """Test the data fetching and resampling functionality."""
    ticker = "SPY"
    df = fetch_stock_data(ticker)
    
    if not df.empty:
        print(f"Fetched {len(df)} rows of 1-minute data for {ticker}")
        print(df.head())
        
        resampled_df = resample_data(df)
        print(f"\nResampled to {len(resampled_df)} rows of 10-minute data")
        print(resampled_df.head())
    else:
        print(f"Failed to fetch data for {ticker}")


if __name__ == "__main__":
    main()
