"""
Portfolio valuation module to track performance over time.
"""
import logging
import sqlite3
import pandas as pd
from pathlib import Path
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("valuation")

# Define database paths
DATA_DIR = Path(__file__).parent.parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)
PORTFOLIO_DB_PATH = DATA_DIR / "portfolio.db"
VALUATION_DB_PATH = DATA_DIR / "valuation.db"


def initialize_stock_data_table():
    """
    Initialize the stock_data_10min table in SQLite if it doesn't exist.
    """
    try:
        sqlite_db_path = DATA_DIR / "stock_data.db"
        conn = sqlite3.connect(sqlite_db_path)
        cursor = conn.cursor()

        # Create the stock_data_10min table if it doesn't exist
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS stock_data_10min (
            ticker TEXT NOT NULL,
            Close REAL NOT NULL,
            Datetime TIMESTAMP NOT NULL,
            PRIMARY KEY (ticker, Datetime)
        )
        ''')

        conn.commit()
        conn.close()
        logger.info("Initialized stock_data_10min table in SQLite.")
    except Exception as e:
        logger.error(f"Error initializing stock_data_10min table: {str(e)}")


# Ensure the stock_data_10min table exists
initialize_stock_data_table()


def get_latest_prices(tickers):
    """
    Get the latest prices for a list of tickers from the stock data database.
    
    Args:
        tickers (list): List of ticker symbols
        
    Returns:
        dict: Dictionary mapping tickers to current prices
    """
    try:
        sqlite_db_path = DATA_DIR / "stock_data.db"
        price_data = {}
        
        for ticker in tickers:
            price = None
            
            # Try SQLite first
            if sqlite_db_path.exists():
                try:
                    conn = sqlite3.connect(sqlite_db_path)
                    # Get the most recent price from the 10-minute data
                    query = '''
                    SELECT ticker, Close, Datetime
                    FROM stock_data_10min
                    WHERE ticker = ?
                    ORDER BY Datetime DESC
                    LIMIT 1
                    '''
                    
                    df = pd.read_sql(query, conn, params=(ticker,))
                    conn.close()
                    
                    if not df.empty:
                        price = df['Close'].iloc[0]
                        logger.info(f"Latest price for {ticker}: ${price:.2f} at {df['Datetime'].iloc[0]}")
                except Exception as e:
                    logger.warning(f"Error getting price from SQLite for {ticker}: {str(e)}")
            
            # If SQLite failed, try parquet files
            if price is None:
                try:
                    parquet_dir = DATA_DIR / "parquet"
                    parquet_files = list(parquet_dir.glob(f"{ticker}_*.parquet"))
                    
                    if parquet_files:
                        # Sort files by modification time to get the most recent one
                        latest_file = sorted(parquet_files, key=lambda x: x.stat().st_mtime, reverse=True)[0]
                        df = pd.read_parquet(latest_file)
                        
                        if not df.empty:
                            # Sort by datetime to get the most recent row
                            if 'Datetime' in df.columns:
                                df = df.sort_values('Datetime', ascending=False)
                                price = df['Close'].iloc[0]
                                logger.info(f"Latest price for {ticker} from parquet: ${price:.2f} at {df['Datetime'].iloc[0]}")
                            elif 'Date' in df.columns:
                                df = df.sort_values('Date', ascending=False)
                                price = df['Close'].iloc[0]
                                logger.info(f"Latest price for {ticker} from parquet: ${price:.2f} at {df['Date'].iloc[0]}")
                except Exception as e:
                    logger.warning(f"Error getting price from parquet for {ticker}: {str(e)}")
            
            if price is not None:
                price_data[ticker] = price
            else:
                logger.warning(f"No price data found for {ticker} in any storage")
        
        return price_data
        
    except Exception as e:
        logger.error(f"Error getting latest prices: {str(e)}")
        return {}


def store_valuation(portfolio_name, valuation_data):
    """
    Store portfolio valuation in the database.
    
    Args:
        portfolio_name (str): Portfolio name
        valuation_data (dict): Valuation data from Portfolio.calculate_current_value()
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        conn = sqlite3.connect(VALUATION_DB_PATH)
        cursor = conn.cursor()
        
        # Create valuation_history table if it doesn't exist
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS valuation_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            portfolio TEXT NOT NULL,
            timestamp TIMESTAMP NOT NULL,
            total_value REAL NOT NULL,
            total_cost REAL NOT NULL,
            total_pl REAL NOT NULL,
            total_pl_pct REAL NOT NULL
        )
        ''')
        
        # Create position_history table if it doesn't exist
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS position_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            valuation_id INTEGER NOT NULL,
            ticker TEXT NOT NULL,
            shares REAL NOT NULL,
            cost_basis REAL NOT NULL,
            current_price REAL NOT NULL,
            current_value REAL NOT NULL,
            pl REAL NOT NULL,
            pl_pct REAL NOT NULL,
            FOREIGN KEY (valuation_id) REFERENCES valuation_history (id)
        )
        ''')
        
        # Insert valuation record
        timestamp = datetime.now()
        cursor.execute('''
        INSERT INTO valuation_history (portfolio, timestamp, total_value, total_cost, total_pl, total_pl_pct)
        VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            portfolio_name,
            timestamp,
            valuation_data['total_value'],
            valuation_data['total_cost'],
            valuation_data['total_pl'],
            valuation_data['total_pl_pct']
        ))
        
        valuation_id = cursor.lastrowid
        
        # Insert position records
        for position in valuation_data['positions']:
            cursor.execute('''
            INSERT INTO position_history (
                valuation_id, ticker, shares, cost_basis, current_price, 
                current_value, pl, pl_pct
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                valuation_id,
                position['ticker'],
                position['shares'],
                position['cost_basis'],
                position.get('current_price', 0),
                position['current_value'],
                position['pl'],
                position['pl_pct']
            ))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Stored valuation for {portfolio_name} at {timestamp}")
        return True
        
    except Exception as e:
        logger.error(f"Error storing valuation: {str(e)}")
        return False


def get_valuation_history(portfolio_name, start_date=None, end_date=None):
    """
    Get portfolio valuation history.
    
    Args:
        portfolio_name (str): Portfolio name
        start_date (datetime): Start date for filtering
        end_date (datetime): End date for filtering
        
    Returns:
        pd.DataFrame: DataFrame with valuation history
    """
    try:
        if not VALUATION_DB_PATH.exists():
            logger.warning(f"Valuation database not found at {VALUATION_DB_PATH}")
            return pd.DataFrame()
            
        conn = sqlite3.connect(VALUATION_DB_PATH)
        
        query = '''
        SELECT id, portfolio, timestamp, total_value, total_cost, total_pl, total_pl_pct
        FROM valuation_history
        WHERE portfolio = ?
        '''
        
        params = [portfolio_name]
        
        if start_date:
            query += " AND timestamp >= ?"
            params.append(start_date)
            
        if end_date:
            query += " AND timestamp <= ?"
            params.append(end_date)
            
        query += " ORDER BY timestamp"
        
        df = pd.read_sql(query, conn, params=params)
        conn.close()
        
        logger.info(f"Retrieved {len(df)} valuation records for {portfolio_name}")
        return df
        
    except Exception as e:
        logger.error(f"Error getting valuation history: {str(e)}")
        return pd.DataFrame()


def get_position_history(valuation_ids):
    """
    Get position history for specific valuation records.
    
    Args:
        valuation_ids (list): List of valuation IDs
        
    Returns:
        pd.DataFrame: DataFrame with position history
    """
    try:
        if not VALUATION_DB_PATH.exists():
            logger.warning(f"Valuation database not found at {VALUATION_DB_PATH}")
            return pd.DataFrame()
            
        if not valuation_ids:
            logger.warning("No valuation IDs provided")
            return pd.DataFrame()
            
        conn = sqlite3.connect(VALUATION_DB_PATH)
        
        placeholders = ','.join(['?'] * len(valuation_ids))
        query = f'''
        SELECT id, valuation_id, ticker, shares, cost_basis, current_price, 
               current_value, pl, pl_pct
        FROM position_history
        WHERE valuation_id IN ({placeholders})
        ORDER BY ticker, valuation_id
        '''
        
        df = pd.read_sql(query, conn, params=valuation_ids)
        conn.close()
        
        logger.info(f"Retrieved {len(df)} position records")
        return df
        
    except Exception as e:
        logger.error(f"Error getting position history: {str(e)}")
        return pd.DataFrame()


def get_performance_metrics(portfolio_name, period="all"):
    """
    Calculate performance metrics for the portfolio.
    
    Args:
        portfolio_name (str): Portfolio name
        period (str): Time period ("day", "week", "month", "year", "all")
        
    Returns:
        dict: Dictionary with performance metrics
    """
    try:
        # Get valuation history
        history = get_valuation_history(portfolio_name)
        
        if history.empty:
            logger.warning(f"No valuation history found for {portfolio_name}")
            return {}
            
        # Calculate metrics
        latest = history.iloc[-1]
        latest_value = latest['total_value']
        latest_date = pd.to_datetime(latest['timestamp'])
        
        # Filter by period
        if period == "day":
            filtered = history[pd.to_datetime(history['timestamp']) >= (latest_date - pd.Timedelta(days=1))]
        elif period == "week":
            filtered = history[pd.to_datetime(history['timestamp']) >= (latest_date - pd.Timedelta(weeks=1))]
        elif period == "month":
            filtered = history[pd.to_datetime(history['timestamp']) >= (latest_date - pd.Timedelta(days=30))]
        elif period == "year":
            filtered = history[pd.to_datetime(history['timestamp']) >= (latest_date - pd.Timedelta(days=365))]
        else:
            filtered = history
            
        if filtered.empty or len(filtered) < 2:
            logger.warning(f"Not enough data points for period '{period}'")
            return {}
            
        earliest = filtered.iloc[0]
        earliest_value = earliest['total_value']
        earliest_date = pd.to_datetime(earliest['timestamp'])
        
        # Calculate returns
        absolute_return = latest_value - earliest_value
        percent_return = (absolute_return / earliest_value) * 100 if earliest_value > 0 else 0
        
        # Calculate annualized return
        days_held = (latest_date - earliest_date).days
        if days_held > 0:
            annualized_return = ((1 + percent_return / 100) ** (365 / days_held) - 1) * 100
        else:
            annualized_return = 0
            
        # Calculate volatility (standard deviation of daily returns)
        history['prev_value'] = history['total_value'].shift(1)
        history['daily_return'] = (history['total_value'] - history['prev_value']) / history['prev_value']
        volatility = history['daily_return'].std() * (252 ** 0.5)  # Annualized
        
        # Calculate Sharpe ratio (assuming risk-free rate of 0% for simplicity)
        if volatility > 0:
            sharpe_ratio = (annualized_return / 100) / volatility
        else:
            sharpe_ratio = 0
            
        return {
            'period': period,
            'start_date': earliest_date,
            'end_date': latest_date,
            'start_value': earliest_value,
            'end_value': latest_value,
            'absolute_return': absolute_return,
            'percent_return': percent_return,
            'annualized_return': annualized_return,
            'volatility': volatility * 100,  # Convert to percentage
            'sharpe_ratio': sharpe_ratio,
            'days_held': days_held
        }
        
    except Exception as e:
        logger.error(f"Error calculating performance metrics: {str(e)}")
        return {}
