"""
Base strategy module defining common interfaces for trading strategies.
"""
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any


class SignalAction(Enum):
    """Enum representing possible trading signal actions."""
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


class SignalStrength(Enum):
    """Enum representing the strength of a trading signal."""
    STRONG = "STRONG"
    MODERATE = "MODERATE"
    WEAK = "WEAK"


@dataclass
class Signal:
    """Class representing a trading signal."""
    ticker: str
    action: SignalAction
    strength: SignalStrength
    reason: str
    timestamp: datetime
    price: float
    metadata: Optional[Dict[str, Any]] = None
    
    def __str__(self):
        """String representation of the signal."""
        return (f"{self.action.value} {self.ticker} @ ${self.price:.2f} "
                f"({self.strength.value}, {self.reason}) - {self.timestamp}")


class Strategy:
    """Base class for all trading strategies."""
    
    def __init__(self, name):
        """
        Initialize the strategy.
        
        Args:
            name (str): Strategy name
        """
        self.name = name
        self.last_signals = {}  # Store the last signal for each ticker
    
    def generate_signals(self, df):
        """
        Generate trading signals based on the input DataFrame.
        Must be implemented by subclasses.
        
        Args:
            df (pd.DataFrame): DataFrame with price and indicator data
            
        Returns:
            list: List of Signal objects
        """
        raise NotImplementedError("Subclasses must implement generate_signals()")
    
    def can_signal(self, ticker, timestamp, cooldown_minutes=30):
        """
        Check if enough time has passed since the last signal for this ticker.
        
        Args:
            ticker (str): Stock ticker symbol
            timestamp (datetime): Current timestamp
            cooldown_minutes (int): Minimum minutes between signals
            
        Returns:
            bool: True if a new signal can be generated, False otherwise
        """
        if ticker not in self.last_signals:
            return True
            
        last_timestamp = self.last_signals[ticker].timestamp
        minutes_diff = (timestamp - last_timestamp).total_seconds() / 60
        
        return minutes_diff >= cooldown_minutes
    
    def update_last_signal(self, signal):
        """
        Update the record of the last signal for a ticker.
        
        Args:
            signal (Signal): The new signal to record
        """
        self.last_signals[signal.ticker] = signal
