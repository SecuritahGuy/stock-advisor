"""
Base portfolio module for tracking positions and performance.
"""
import sqlite3
import logging
import pandas as pd
from pathlib import Path
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("portfolio")

# Define database path
DATA_DIR = Path(__file__).parent.parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)
PORTFOLIO_DB_PATH = DATA_DIR / "portfolio.db"


class Portfolio:
    """Portfolio class for tracking positions and performance."""
    
    def __init__(self, name="default", db_path=None):
        """
        Initialize the portfolio.
        
        Args:
            name (str): Portfolio name
            db_path (str): Path to SQLite database
        """
        self.name = name
        self.db_path = db_path or PORTFOLIO_DB_PATH
        self._init_db()
        logger.info(f"Initialized portfolio '{name}'")
    
    def _init_db(self):
        """Initialize the portfolio database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create positions table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS positions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                portfolio TEXT NOT NULL,
                ticker TEXT NOT NULL,
                shares REAL NOT NULL,
                cost_basis REAL NOT NULL,
                opened_at TIMESTAMP NOT NULL,
                notes TEXT
            )
            ''')
            
            # Create transactions table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                portfolio TEXT NOT NULL,
                ticker TEXT NOT NULL,
                action TEXT NOT NULL,
                shares REAL NOT NULL,
                price REAL NOT NULL,
                timestamp TIMESTAMP NOT NULL,
                notes TEXT
            )
            ''')
            
            conn.commit()
            conn.close()
            
            logger.info("Portfolio database initialized")
            
        except Exception as e:
            logger.error(f"Error initializing portfolio database: {str(e)}")
            raise
    
    def add_position(self, ticker, shares, price, timestamp=None, notes=None):
        """
        Add a new position to the portfolio.
        
        Args:
            ticker (str): Stock ticker symbol
            shares (float): Number of shares
            price (float): Price per share
            timestamp (datetime): Time of transaction
            notes (str): Additional notes
            
        Returns:
            int: Position ID if successful, None otherwise
        """
        if timestamp is None:
            timestamp = datetime.now()
            
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Insert new position
            cursor.execute('''
            INSERT INTO positions (portfolio, ticker, shares, cost_basis, opened_at, notes)
            VALUES (?, ?, ?, ?, ?, ?)
            ''', (self.name, ticker, shares, price, timestamp, notes))
            
            # Record the transaction
            cursor.execute('''
            INSERT INTO transactions (portfolio, ticker, action, shares, price, timestamp, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (self.name, ticker, 'BUY', shares, price, timestamp, notes))
            
            conn.commit()
            position_id = cursor.lastrowid
            conn.close()
            
            logger.info(f"Added position: {shares} shares of {ticker} at ${price:.2f}")
            return position_id
            
        except Exception as e:
            logger.error(f"Error adding position: {str(e)}")
            return None
    
    def close_position(self, position_id, price, timestamp=None, notes=None):
        """
        Close an existing position.
        
        Args:
            position_id (int): ID of the position to close
            price (float): Selling price per share
            timestamp (datetime): Time of transaction
            notes (str): Additional notes
            
        Returns:
            bool: True if successful, False otherwise
        """
        if timestamp is None:
            timestamp = datetime.now()
            
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get position details
            cursor.execute('SELECT ticker, shares, cost_basis FROM positions WHERE id = ?', (position_id,))
            row = cursor.fetchone()
            
            if not row:
                logger.warning(f"Position ID {position_id} not found")
                conn.close()
                return False
                
            ticker, shares, cost_basis = row
            
            # Record the transaction
            cursor.execute('''
            INSERT INTO transactions (portfolio, ticker, action, shares, price, timestamp, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (self.name, ticker, 'SELL', shares, price, timestamp, notes))
            
            # Remove the position
            cursor.execute('DELETE FROM positions WHERE id = ?', (position_id,))
            
            conn.commit()
            conn.close()
            
            profit_loss = (price - cost_basis) * shares
            logger.info(f"Closed position: {shares} shares of {ticker} at ${price:.2f} (P/L: ${profit_loss:.2f})")
            return True
            
        except Exception as e:
            logger.error(f"Error closing position: {str(e)}")
            return False
    
    def update_position(self, position_id, shares=None, cost_basis=None, notes=None):
        """
        Update an existing position.
        
        Args:
            position_id (int): ID of the position to update
            shares (float): New number of shares
            cost_basis (float): New cost basis
            notes (str): New notes
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Build update query
            update_parts = []
            params = []
            
            if shares is not None:
                update_parts.append("shares = ?")
                params.append(shares)
                
            if cost_basis is not None:
                update_parts.append("cost_basis = ?")
                params.append(cost_basis)
                
            if notes is not None:
                update_parts.append("notes = ?")
                params.append(notes)
                
            if not update_parts:
                logger.warning("No updates specified")
                conn.close()
                return False
                
            # Add position_id to params
            params.append(position_id)
            
            # Execute update
            cursor.execute(f'''
            UPDATE positions SET {', '.join(update_parts)}
            WHERE id = ?
            ''', params)
            
            if cursor.rowcount == 0:
                logger.warning(f"Position ID {position_id} not found")
                conn.close()
                return False
                
            conn.commit()
            conn.close()
            
            logger.info(f"Updated position ID {position_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating position: {str(e)}")
            return False
    
    def get_positions(self):
        """
        Get all open positions.
        
        Returns:
            pd.DataFrame: DataFrame with positions
        """
        try:
            conn = sqlite3.connect(self.db_path)
            
            query = f'''
            SELECT id, ticker, shares, cost_basis, opened_at, notes
            FROM positions
            WHERE portfolio = ?
            '''
            
            df = pd.read_sql(query, conn, params=(self.name,))
            conn.close()
            
            logger.info(f"Retrieved {len(df)} positions")
            return df
            
        except Exception as e:
            logger.error(f"Error getting positions: {str(e)}")
            return pd.DataFrame()
    
    def get_transactions(self, start_date=None, end_date=None):
        """
        Get transaction history.
        
        Args:
            start_date (datetime): Start date for filtering
            end_date (datetime): End date for filtering
            
        Returns:
            pd.DataFrame: DataFrame with transactions
        """
        try:
            conn = sqlite3.connect(self.db_path)
            
            query = f'''
            SELECT id, ticker, action, shares, price, timestamp, notes
            FROM transactions
            WHERE portfolio = ?
            '''
            
            params = [self.name]
            
            if start_date:
                query += " AND timestamp >= ?"
                params.append(start_date)
                
            if end_date:
                query += " AND timestamp <= ?"
                params.append(end_date)
                
            query += " ORDER BY timestamp DESC"
            
            df = pd.read_sql(query, conn, params=params)
            conn.close()
            
            logger.info(f"Retrieved {len(df)} transactions")
            return df
            
        except Exception as e:
            logger.error(f"Error getting transactions: {str(e)}")
            return pd.DataFrame()
    
    def get_position_by_ticker(self, ticker):
        """
        Get position details for a specific ticker.
        
        Args:
            ticker (str): Stock ticker symbol
            
        Returns:
            pd.DataFrame: DataFrame with position details
        """
        try:
            conn = sqlite3.connect(self.db_path)
            
            query = f'''
            SELECT id, ticker, shares, cost_basis, opened_at, notes
            FROM positions
            WHERE portfolio = ? AND ticker = ?
            '''
            
            df = pd.read_sql(query, conn, params=(self.name, ticker))
            conn.close()
            
            return df
            
        except Exception as e:
            logger.error(f"Error getting position for {ticker}: {str(e)}")
            return pd.DataFrame()
    
    def calculate_current_value(self, price_data):
        """
        Calculate the current value of the portfolio.
        
        Args:
            price_data (dict): Dictionary mapping tickers to current prices
            
        Returns:
            dict: Dictionary with portfolio value and position details
        """
        positions = self.get_positions()
        
        if positions.empty:
            return {
                'total_value': 0,
                'total_cost': 0,
                'total_pl': 0,
                'total_pl_pct': 0,
                'positions': []
            }
            
        position_details = []
        total_value = 0
        total_cost = 0
        
        for _, position in positions.iterrows():
            ticker = position['ticker']
            shares = position['shares']
            cost_basis = position['cost_basis']
            total_cost_position = shares * cost_basis
            
            # Get current price
            current_price = price_data.get(ticker)
            
            if current_price is None:
                logger.warning(f"No price data available for {ticker}")
                current_value = total_cost_position  # Assume no change if no price data
                pl = 0
                pl_pct = 0
            else:
                current_value = shares * current_price
                pl = current_value - total_cost_position
                pl_pct = (pl / total_cost_position) * 100 if total_cost_position > 0 else 0
                
            position_details.append({
                'id': position['id'],
                'ticker': ticker,
                'shares': shares,
                'cost_basis': cost_basis,
                'current_price': current_price,
                'current_value': current_value,
                'total_cost': total_cost_position,
                'pl': pl,
                'pl_pct': pl_pct,
                'opened_at': position['opened_at'],
                'notes': position['notes']
            })
            
            total_value += current_value
            total_cost += total_cost_position
            
        total_pl = total_value - total_cost
        total_pl_pct = (total_pl / total_cost) * 100 if total_cost > 0 else 0
        
        return {
            'total_value': total_value,
            'total_cost': total_cost,
            'total_pl': total_pl,
            'total_pl_pct': total_pl_pct,
            'positions': position_details
        }


def main():
    """Test the portfolio functionality."""
    portfolio = Portfolio("test_portfolio")
    
    # Add sample positions
    portfolio.add_position("AAPL", 10, 150.0, notes="Initial Apple position")
    portfolio.add_position("MSFT", 5, 250.0, notes="Initial Microsoft position")
    
    # Get all positions
    positions = portfolio.get_positions()
    print("Current positions:")
    print(positions)
    
    # Calculate current value with simulated prices
    price_data = {
        "AAPL": 155.0,
        "MSFT": 260.0
    }
    
    valuation = portfolio.calculate_current_value(price_data)
    print("\nPortfolio valuation:")
    print(f"Total value: ${valuation['total_value']:.2f}")
    print(f"Total cost: ${valuation['total_cost']:.2f}")
    print(f"Total P/L: ${valuation['total_pl']:.2f} ({valuation['total_pl_pct']:.2f}%)")
    
    for pos in valuation['positions']:
        print(f"{pos['ticker']}: {pos['shares']} shares, P/L: ${pos['pl']:.2f} ({pos['pl_pct']:.2f}%)")


if __name__ == "__main__":
    main()
