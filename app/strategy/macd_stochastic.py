"""
MACD + Stochastic strategy implementation.
"""
import logging
from datetime import datetime
import pandas as pd
import numpy as np
from app.strategy.base import Strategy, Signal, SignalAction, SignalStrength

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("macd_stoch")


class MACDStochasticStrategy(Strategy):
    """
    MACD + Stochastic strategy implementation.
    
    Generates BUY signals when:
    1. MACD line crosses above the signal line
    2. Stochastic %K crosses above %D when both are below oversold level
    
    Generates SELL signals when:
    1. MACD line crosses below the signal line
    2. Stochastic %K crosses below %D when both are above overbought level
    """
    
    def __init__(self, fast=12, slow=26, signal=9, 
                 stoch_k=14, stoch_d=3, smooth_k=3,
                 stoch_overbought=80, stoch_oversold=20, 
                 cooldown_minutes=30):
        """
        Initialize the MACD + Stochastic strategy.
        
        Args:
            fast (int): MACD fast period
            slow (int): MACD slow period
            signal (int): MACD signal period
            stoch_k (int): Stochastic K period
            stoch_d (int): Stochastic D period
            smooth_k (int): Stochastic K smoothing
            stoch_overbought (int): Stochastic overbought level
            stoch_oversold (int): Stochastic oversold level
            cooldown_minutes (int): Minimum minutes between signals
        """
        super().__init__(f"MACD{fast}_{slow}_{signal}_Stoch{stoch_k}_{stoch_d}")
        self.fast = fast
        self.slow = slow
        self.signal = signal
        self.stoch_k = stoch_k
        self.stoch_d = stoch_d
        self.smooth_k = smooth_k
        self.stoch_overbought = stoch_overbought
        self.stoch_oversold = stoch_oversold
        self.cooldown_minutes = cooldown_minutes
        
        logger.info(f"Initialized {self.name} strategy")
    
    def generate_signals(self, df):
        """
        Generate trading signals based on MACD and Stochastic Oscillator.
        
        Args:
            df (pd.DataFrame): DataFrame with price and indicator data
            
        Returns:
            list: List of Signal objects
        """
        if df.empty:
            logger.warning("Empty DataFrame provided, no signals generated")
            return []
            
        # Check if required columns exist
        stoch_k_col = f'stoch_k{self.stoch_k}'
        stoch_d_col = f'stoch_d{self.stoch_k}'
        required_columns = [
            'ticker', 'Close', 'macd', 'macd_signal', 'macd_hist',
            stoch_k_col, stoch_d_col
        ]
        
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            logger.error(f"Missing required columns: {missing_columns}")
            return []
            
        # Ensure the DataFrame is sorted by time
        if 'Datetime' in df.columns:
            df = df.sort_values('Datetime')
            time_col = 'Datetime'
        elif 'Date' in df.columns:
            df = df.sort_values('Date')
            time_col = 'Date'
        else:
            logger.error("No time column found in DataFrame")
            return []
            
        # Make sure we have enough data
        if len(df) < max(self.slow, self.stoch_k + self.stoch_d):
            logger.warning(f"Not enough data points ({len(df)}) for indicator calculation")
            return []
        
        # Calculate crossovers
        df['macd_prev'] = df['macd'].shift(1)
        df['macd_signal_prev'] = df['macd_signal'].shift(1)
        df['stoch_k_prev'] = df[stoch_k_col].shift(1)
        df['stoch_d_prev'] = df[stoch_d_col].shift(1)
        
        # MACD crosses above signal line
        df['macd_cross_above'] = (df['macd_prev'] < df['macd_signal_prev']) & (df['macd'] > df['macd_signal'])
        
        # MACD crosses below signal line
        df['macd_cross_below'] = (df['macd_prev'] > df['macd_signal_prev']) & (df['macd'] < df['macd_signal'])
        
        # Stochastic %K crosses above %D
        df['stoch_cross_above'] = (df['stoch_k_prev'] < df['stoch_d_prev']) & (df[stoch_k_col] > df[stoch_d_col])
        
        # Stochastic %K crosses below %D
        df['stoch_cross_below'] = (df['stoch_k_prev'] > df['stoch_d_prev']) & (df[stoch_k_col] < df[stoch_d_col])
        
        # Generate signals
        signals = []
        
        for idx, row in df.iterrows():
            # Skip rows with NaN values in key columns
            if pd.isna(row['macd']) or pd.isna(row['macd_signal']) or pd.isna(row[stoch_k_col]) or pd.isna(row[stoch_d_col]):
                continue
                
            timestamp = row[time_col]
            ticker = row['ticker']
            
            # Check if cooled down since last signal
            if not self.can_signal(ticker, timestamp, self.cooldown_minutes):
                continue
            
            # BUY signal logic
            # 1. MACD crosses above signal line
            # 2. Stochastic crosses above in oversold zone
            if row['macd_cross_above'] and row[stoch_k_col] < 50:
                # Stronger signal if stochastic is coming from oversold
                if row['stoch_cross_above'] and row['stoch_k_prev'] < self.stoch_oversold:
                    strength = SignalStrength.STRONG
                    reason = (f"MACD crosses above signal line ({row['macd']:.2f} > {row['macd_signal']:.2f}) "
                             f"with bullish Stochastic crossover from oversold ({row[stoch_k_col]:.1f} > {row[stoch_d_col]:.1f})")
                else:
                    strength = SignalStrength.MODERATE
                    reason = (f"MACD crosses above signal line ({row['macd']:.2f} > {row['macd_signal']:.2f}) "
                             f"with Stochastic below 50 ({row[stoch_k_col]:.1f})")
                
                signal = Signal(
                    ticker=ticker,
                    action=SignalAction.BUY,
                    strength=strength,
                    reason=reason,
                    timestamp=timestamp,
                    price=row['Close'],
                    metadata={
                        'macd': row['macd'],
                        'macd_signal': row['macd_signal'],
                        'macd_hist': row['macd_hist'],
                        'stoch_k': row[stoch_k_col],
                        'stoch_d': row[stoch_d_col]
                    }
                )
                signals.append(signal)
                self.update_last_signal(signal)
                logger.info(f"Generated BUY signal for {ticker} at {timestamp} (MACD + Stoch)")
            
            # SELL signal logic
            # 1. MACD crosses below signal line
            # 2. Stochastic crosses below in overbought zone
            elif row['macd_cross_below'] and row[stoch_k_col] > 50:
                # Stronger signal if stochastic is coming from overbought
                if row['stoch_cross_below'] and row['stoch_k_prev'] > self.stoch_overbought:
                    strength = SignalStrength.STRONG
                    reason = (f"MACD crosses below signal line ({row['macd']:.2f} < {row['macd_signal']:.2f}) "
                             f"with bearish Stochastic crossover from overbought ({row[stoch_k_col]:.1f} < {row[stoch_d_col]:.1f})")
                else:
                    strength = SignalStrength.MODERATE
                    reason = (f"MACD crosses below signal line ({row['macd']:.2f} < {row['macd_signal']:.2f}) "
                             f"with Stochastic above 50 ({row[stoch_k_col]:.1f})")
                
                signal = Signal(
                    ticker=ticker,
                    action=SignalAction.SELL,
                    strength=strength,
                    reason=reason,
                    timestamp=timestamp,
                    price=row['Close'],
                    metadata={
                        'macd': row['macd'],
                        'macd_signal': row['macd_signal'],
                        'macd_hist': row['macd_hist'],
                        'stoch_k': row[stoch_k_col],
                        'stoch_d': row[stoch_d_col]
                    }
                )
                signals.append(signal)
                self.update_last_signal(signal)
                logger.info(f"Generated SELL signal for {ticker} at {timestamp} (MACD + Stoch)")
        
        return signals
