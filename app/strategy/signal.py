"""
Signal module for generating and retrieving trading signals.
"""
import logging
import sqlite3
import pandas as pd
from pathlib import Path
from datetime import datetime
from enum import Enum

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("signal")

# Define database path
DATA_DIR = Path(__file__).parent.parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)
SIGNAL_DB_PATH = DATA_DIR / "signals.db"


class SignalAction(Enum):
    """Enum for signal actions."""
    BUY = "BUY"
    SELL = "SELL"


class SignalStrength(Enum):
    """Enum for signal strength."""
    WEAK = "WEAK"
    MODERATE = "MODERATE"
    STRONG = "STRONG"


class Signal:
    """Trading signal class."""
    
    def __init__(self, ticker, action, price, timestamp=None, 
                 strategy="default", strength=SignalStrength.MODERATE, reason=""):
        """
        Initialize a new signal.
        
        Args:
            ticker (str): Stock ticker symbol
            action (SignalAction): Signal action (BUY/SELL)
            price (float): Current price
            timestamp (datetime): Signal timestamp
            strategy (str): Strategy that generated the signal
            strength (SignalStrength): Signal strength
            reason (str): Reason for the signal
        """
        self.ticker = ticker
        self.action = action if isinstance(action, SignalAction) else SignalAction(action)
        self.price = price
        self.timestamp = timestamp or datetime.now()
        self.strategy = strategy
        self.strength = strength if isinstance(strength, SignalStrength) else SignalStrength(strength)
        self.reason = reason


def initialize_signal_db():
    """Initialize the signals database if it doesn't exist."""
    try:
        conn = sqlite3.connect(SIGNAL_DB_PATH)
        cursor = conn.cursor()
        
        # Create signals table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS signals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT NOT NULL,
            action TEXT NOT NULL,
            price REAL NOT NULL,
            timestamp TIMESTAMP NOT NULL,
            strategy TEXT NOT NULL,
            strength TEXT NOT NULL,
            reason TEXT
        )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("Signals database initialized")
        
    except Exception as e:
        logger.error(f"Error initializing signals database: {str(e)}")


# Initialize database on module import
initialize_signal_db()


def save_signal(signal):
    """
    Save a signal to the database.
    
    Args:
        signal (Signal): Signal to save
        
    Returns:
        int: Signal ID if successful, None otherwise
    """
    try:
        conn = sqlite3.connect(SIGNAL_DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT INTO signals (ticker, action, price, timestamp, strategy, strength, reason)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            signal.ticker,
            signal.action.value,
            signal.price,
            signal.timestamp,
            signal.strategy,
            signal.strength.value,
            signal.reason
        ))
        
        conn.commit()
        signal_id = cursor.lastrowid
        conn.close()
        
        logger.info(f"Saved {signal.action.value} signal for {signal.ticker} at ${signal.price:.2f}")
        return signal_id
        
    except Exception as e:
        logger.error(f"Error saving signal: {str(e)}")
        return None


def get_recent_signals(ticker=None, limit=20, days=None):
    """
    Get recent signals from the database.
    
    Args:
        ticker (str): Filter by ticker (optional)
        limit (int): Maximum number of signals to return
        days (int): Filter signals from the last N days (optional)
        
    Returns:
        list: List of Signal objects
    """
    try:
        conn = sqlite3.connect(SIGNAL_DB_PATH)
        
        query = "SELECT * FROM signals"
        params = []
        
        # Apply filters
        where_clauses = []
        
        if ticker:
            where_clauses.append("ticker = ?")
            params.append(ticker)
            
        if days:
            where_clauses.append("timestamp >= datetime('now', ?)")
            params.append(f"-{days} days")
            
        if where_clauses:
            query += " WHERE " + " AND ".join(where_clauses)
            
        query += " ORDER BY timestamp DESC"
        
        if limit:
            query += " LIMIT ?"
            params.append(limit)
            
        # Execute query
        cursor = conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        # Convert to Signal objects
        signals = []
        for row in rows:
            signal = Signal(
                ticker=row[1],
                action=SignalAction(row[2]),
                price=row[3],
                timestamp=datetime.strptime(row[4], '%Y-%m-%d %H:%M:%S.%f') 
                         if '.' in row[4] else datetime.strptime(row[4], '%Y-%m-%d %H:%M:%S'),
                strategy=row[5],
                strength=SignalStrength(row[6]),
                reason=row[7]
            )
            signals.append(signal)
            
        logger.info(f"Retrieved {len(signals)} signals")
        return signals
        
    except Exception as e:
        logger.error(f"Error getting signals: {str(e)}")
        return []


def generate_manual_signal(ticker, action, price, strategy="manual", strength="MODERATE", reason="User generated"):
    """
    Generate a manual signal.
    
    Args:
        ticker (str): Stock ticker symbol
        action (str): "BUY" or "SELL"
        price (float): Current price
        strategy (str): Strategy name
        strength (str): Signal strength ("WEAK", "MODERATE", "STRONG")
        reason (str): Reason for the signal
        
    Returns:
        Signal: Generated signal
    """
    try:
        signal = Signal(
            ticker=ticker,
            action=SignalAction(action),
            price=price,
            timestamp=datetime.now(),
            strategy=strategy,
            strength=SignalStrength(strength),
            reason=reason
        )
        
        # Save the signal
        save_signal(signal)
        
        logger.info(f"Generated manual {action} signal for {ticker}")
        return signal
        
    except Exception as e:
        logger.error(f"Error generating manual signal: {str(e)}")
        return None
