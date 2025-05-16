"""
Storage module for persisting stock data locally.
"""
import os
import logging
import pandas as pd
import sqlite3
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("storage")

# Define storage paths
DATA_DIR = Path(__file__).parent.parent.parent / "data"
SQLITE_DB_PATH = DATA_DIR / "stock_data.db"
PARQUET_DIR = DATA_DIR / "parquet"

# Create directories if they don't exist
DATA_DIR.mkdir(exist_ok=True)
PARQUET_DIR.mkdir(exist_ok=True)


def save_to_sqlite(df, table_name="stock_data", db_path=None):
    """
    Save DataFrame to SQLite database.
    
    Args:
        df (pd.DataFrame): DataFrame to save
        table_name (str): Table name in SQLite
        db_path (str, optional): Path to SQLite database
        
    Returns:
        bool: True if successful, False otherwise
    """
    if df.empty:
        logger.warning("Empty DataFrame, skipping SQLite save")
        return False
        
    if db_path is None:
        db_path = SQLITE_DB_PATH
        
    try:
        logger.info(f"Saving {len(df)} rows to SQLite table '{table_name}'")
        
        # Create connection
        conn = sqlite3.connect(db_path)
        
        # Save to SQLite
        df.to_sql(table_name, conn, if_exists="append", index=False)
        
        # Close connection
        conn.close()
        
        logger.info(f"Successfully saved data to {db_path}")
        return True
        
    except Exception as e:
        logger.error(f"Error saving to SQLite: {str(e)}")
        return False


def save_to_parquet(df, ticker, interval="10min", data_dir=None):
    """
    Save DataFrame to Parquet file.
    
    Args:
        df (pd.DataFrame): DataFrame to save
        ticker (str): Stock ticker symbol
        interval (str): Data interval identifier
        data_dir (str, optional): Directory to save Parquet files
        
    Returns:
        bool: True if successful, False otherwise
    """
    if df.empty:
        logger.warning("Empty DataFrame, skipping Parquet save")
        return False
        
    if data_dir is None:
        data_dir = PARQUET_DIR
        
    try:
        # Create filename with date range info
        if 'Datetime' in df.columns:
            start_date = df['Datetime'].min().strftime('%Y%m%d')
            end_date = df['Datetime'].max().strftime('%Y%m%d')
        elif 'Date' in df.columns:
            start_date = df['Date'].min().strftime('%Y%m%d')
            end_date = df['Date'].max().strftime('%Y%m%d')
        else:
            start_date = "unknown"
            end_date = "unknown"
            
        filename = f"{ticker}_{interval}_{start_date}_to_{end_date}.parquet"
        filepath = Path(data_dir) / filename
        
        logger.info(f"Saving {len(df)} rows to Parquet file '{filepath}'")
        
        # Save to Parquet
        df.to_parquet(filepath, compression="snappy")
        
        logger.info(f"Successfully saved data to {filepath}")
        return True
        
    except Exception as e:
        logger.error(f"Error saving to Parquet: {str(e)}")
        return False


def load_from_sqlite(table_name="stock_data", ticker=None, start_date=None, end_date=None, db_path=None):
    """
    Load data from SQLite database with optional filtering.
    
    Args:
        table_name (str): Table name in SQLite
        ticker (str, optional): Filter by ticker symbol
        start_date (str, optional): Filter by start date (YYYY-MM-DD)
        end_date (str, optional): Filter by end date (YYYY-MM-DD)
        db_path (str, optional): Path to SQLite database
        
    Returns:
        pd.DataFrame: DataFrame with loaded data
    """
    if db_path is None:
        db_path = SQLITE_DB_PATH
        
    if not os.path.exists(db_path):
        logger.warning(f"Database file {db_path} does not exist")
        return pd.DataFrame()
        
    try:
        logger.info(f"Loading data from SQLite table '{table_name}'")
        
        # Create connection
        conn = sqlite3.connect(db_path)
        
        # Build query
        query = f"SELECT * FROM {table_name}"
        params = []
        
        # Add filters if provided
        where_clauses = []
        
        if ticker:
            where_clauses.append("ticker = ?")
            params.append(ticker)
            
        if start_date:
            # Assuming datetime column is named 'Datetime' or 'Date'
            # This needs to match the actual column name in your DB
            where_clauses.append("Datetime >= ?")
            params.append(start_date)
            
        if end_date:
            where_clauses.append("Datetime <= ?")
            params.append(end_date)
            
        if where_clauses:
            query += " WHERE " + " AND ".join(where_clauses)
            
        # Load data
        df = pd.read_sql(query, conn, params=params)
        
        # Close connection
        conn.close()
        
        logger.info(f"Loaded {len(df)} rows from SQLite")
        return df
        
    except Exception as e:
        logger.error(f"Error loading from SQLite: {str(e)}")
        return pd.DataFrame()


def load_from_parquet(ticker, data_dir=None):
    """
    Load data from Parquet files for a specific ticker.
    
    Args:
        ticker (str): Stock ticker symbol
        data_dir (str, optional): Directory with Parquet files
        
    Returns:
        pd.DataFrame: DataFrame with loaded data
    """
    if data_dir is None:
        data_dir = PARQUET_DIR
        
    try:
        logger.info(f"Loading Parquet data for {ticker}")
        
        # Find all Parquet files for this ticker
        parquet_files = list(Path(data_dir).glob(f"{ticker}_*.parquet"))
        
        if not parquet_files:
            logger.warning(f"No Parquet files found for {ticker}")
            return pd.DataFrame()
            
        # Load and concatenate all files
        dfs = []
        for file in parquet_files:
            logger.info(f"Loading file {file}")
            df = pd.read_parquet(file)
            dfs.append(df)
            
        if not dfs:
            return pd.DataFrame()
            
        # Concatenate all DataFrames
        result_df = pd.concat(dfs)
        
        # Sort by datetime if available
        if 'Datetime' in result_df.columns:
            result_df = result_df.sort_values('Datetime')
        elif 'Date' in result_df.columns:
            result_df = result_df.sort_values('Date')
            
        # Remove duplicates if any
        if 'Datetime' in result_df.columns:
            result_df = result_df.drop_duplicates(subset=['Datetime', 'ticker'])
        elif 'Date' in result_df.columns:
            result_df = result_df.drop_duplicates(subset=['Date', 'ticker'])
            
        logger.info(f"Loaded total of {len(result_df)} rows for {ticker}")
        return result_df
        
    except Exception as e:
        logger.error(f"Error loading from Parquet: {str(e)}")
        return pd.DataFrame()


def main():
    """Test the storage functionality with sample data."""
    # Create test data
    dates = pd.date_range(start='2023-01-01', periods=100, freq='10min')
    df = pd.DataFrame({
        'Datetime': dates,
        'Open': [100 + i * 0.1 for i in range(100)],
        'High': [101 + i * 0.1 for i in range(100)],
        'Low': [99 + i * 0.1 for i in range(100)],
        'Close': [100.5 + i * 0.1 for i in range(100)],
        'Volume': [1000 + i * 10 for i in range(100)],
        'ticker': ['SPY'] * 100
    })
    
    # Test SQLite storage
    save_to_sqlite(df)
    loaded_df = load_from_sqlite(ticker='SPY')
    print(f"Loaded {len(loaded_df)} rows from SQLite")
    
    # Test Parquet storage
    save_to_parquet(df, 'SPY')
    loaded_df = load_from_parquet('SPY')
    print(f"Loaded {len(loaded_df)} rows from Parquet")


if __name__ == "__main__":
    main()
