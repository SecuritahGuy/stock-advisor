"""
Bollinger Bands strategy implementation.
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
logger = logging.getLogger("bollinger_bands")


class BBandsStrategy(Strategy):
    """
    Bollinger Bands strategy implementation.
    
    Generates BUY signals when price touches/breaks below the lower band and RSI is oversold,
    and SELL signals when price touches/breaks above the upper band and RSI is overbought.
    """
    
    def __init__(self, bb_length=20, bb_std=2, rsi_period=14, 
                 rsi_overbought=70, rsi_oversold=30, cooldown_minutes=30,
                 mean_reversion=True):
        """
        Initialize the Bollinger Bands strategy.
        
        Args:
            bb_length (int): Bollinger Bands period
            bb_std (float): Number of standard deviations for the bands
            rsi_period (int): RSI period
            rsi_overbought (int): RSI threshold for overbought condition
            rsi_oversold (int): RSI threshold for oversold condition
            cooldown_minutes (int): Minimum minutes between signals
            mean_reversion (bool): If True, uses mean reversion logic, otherwise uses breakout logic
        """
        super().__init__(f"BBands{bb_length}_{bb_std}std_RSI{rsi_period}")
        self.bb_length = bb_length
        self.bb_std = bb_std
        self.rsi_period = rsi_period
        self.rsi_overbought = rsi_overbought
        self.rsi_oversold = rsi_oversold
        self.cooldown_minutes = cooldown_minutes
        self.mean_reversion = mean_reversion
        
        logger.info(f"Initialized {self.name} strategy with {'mean reversion' if mean_reversion else 'breakout'} logic")
    
    def generate_signals(self, df):
        """
        Generate trading signals based on Bollinger Bands and RSI filters.
        
        Args:
            df (pd.DataFrame): DataFrame with price and indicator data
            
        Returns:
            list: List of Signal objects
        """
        if df.empty:
            logger.warning("Empty DataFrame provided, no signals generated")
            return []
            
        # Check if required columns exist
        bb_lower = f'bb_lower_{self.bb_length}'
        bb_middle = f'bb_middle_{self.bb_length}'
        bb_upper = f'bb_upper_{self.bb_length}'
        rsi_col = f'rsi{self.rsi_period}'
        
        required_columns = ['ticker', 'Close', bb_lower, bb_middle, bb_upper, rsi_col]
        
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
        if len(df) < self.bb_length:
            logger.warning(f"Not enough data points ({len(df)}) for BBands calculation")
            return []
        
        # Calculate the price position relative to bollinger bands
        df['bb_pct'] = (df['Close'] - df[bb_lower]) / (df[bb_upper] - df[bb_lower])
        
        # Generate signals based on chosen strategy (mean reversion or breakout)
        signals = []
        
        for idx, row in df.iterrows():
            # Skip rows with NaN values in key columns
            if pd.isna(row[bb_lower]) or pd.isna(row[bb_upper]) or pd.isna(row[rsi_col]):
                continue
                
            # Skip if we don't have enough data points yet
            if idx < self.bb_length:
                continue
                
            timestamp = row[time_col]
            ticker = row['ticker']
            
            # Check if cooled down since last signal
            if not self.can_signal(ticker, timestamp, self.cooldown_minutes):
                continue
            
            if self.mean_reversion:
                # Mean Reversion Logic
                # BUY when price is at/below lower band and RSI is oversold
                if row['Close'] <= row[bb_lower] and row[rsi_col] <= self.rsi_oversold:
                    signal = Signal(
                        ticker=ticker,
                        action=SignalAction.BUY,
                        strength=SignalStrength.STRONG if row[rsi_col] < 20 else SignalStrength.MODERATE,
                        reason=f"Price at/below lower BBand ({row['bb_pct']:.2f}) with RSI={row[rsi_col]:.1f}",
                        timestamp=timestamp,
                        price=row['Close'],
                        metadata={
                            'bb_lower': row[bb_lower],
                            'bb_middle': row[bb_middle],
                            'bb_upper': row[bb_upper],
                            'bb_pct': row['bb_pct'],
                            'rsi': row[rsi_col]
                        }
                    )
                    signals.append(signal)
                    self.update_last_signal(signal)
                    logger.info(f"Generated BUY signal for {ticker} at {timestamp} (Lower BBand)")
                
                # SELL when price is at/above upper band and RSI is overbought
                elif row['Close'] >= row[bb_upper] and row[rsi_col] >= self.rsi_overbought:
                    signal = Signal(
                        ticker=ticker,
                        action=SignalAction.SELL,
                        strength=SignalStrength.STRONG if row[rsi_col] > 80 else SignalStrength.MODERATE,
                        reason=f"Price at/above upper BBand ({row['bb_pct']:.2f}) with RSI={row[rsi_col]:.1f}",
                        timestamp=timestamp,
                        price=row['Close'],
                        metadata={
                            'bb_lower': row[bb_lower],
                            'bb_middle': row[bb_middle],
                            'bb_upper': row[bb_upper],
                            'bb_pct': row['bb_pct'],
                            'rsi': row[rsi_col]
                        }
                    )
                    signals.append(signal)
                    self.update_last_signal(signal)
                    logger.info(f"Generated SELL signal for {ticker} at {timestamp} (Upper BBand)")
            else:
                # Breakout Logic
                # Previous and current price position
                prev_idx = df.index[df.index.get_loc(idx) - 1]
                prev_row = df.loc[prev_idx]
                
                # BUY on upward breakout of middle band with RSI momentum
                if (prev_row['Close'] < prev_row[bb_middle] and 
                    row['Close'] > row[bb_middle] and 
                    row[rsi_col] > 50 and row[rsi_col] < self.rsi_overbought):
                    
                    signal = Signal(
                        ticker=ticker,
                        action=SignalAction.BUY,
                        strength=SignalStrength.MODERATE,
                        reason=f"Upward breakout of middle BBand with RSI={row[rsi_col]:.1f}",
                        timestamp=timestamp,
                        price=row['Close'],
                        metadata={
                            'bb_lower': row[bb_lower],
                            'bb_middle': row[bb_middle],
                            'bb_upper': row[bb_upper],
                            'bb_pct': row['bb_pct'],
                            'rsi': row[rsi_col]
                        }
                    )
                    signals.append(signal)
                    self.update_last_signal(signal)
                    logger.info(f"Generated BUY signal for {ticker} at {timestamp} (Middle BBand Breakout)")
                
                # SELL on downward breakout of middle band with RSI momentum
                elif (prev_row['Close'] > prev_row[bb_middle] and 
                      row['Close'] < row[bb_middle] and 
                      row[rsi_col] < 50 and row[rsi_col] > self.rsi_oversold):
                    
                    signal = Signal(
                        ticker=ticker,
                        action=SignalAction.SELL,
                        strength=SignalStrength.MODERATE,
                        reason=f"Downward breakout of middle BBand with RSI={row[rsi_col]:.1f}",
                        timestamp=timestamp,
                        price=row['Close'],
                        metadata={
                            'bb_lower': row[bb_lower],
                            'bb_middle': row[bb_middle],
                            'bb_upper': row[bb_upper],
                            'bb_pct': row['bb_pct'],
                            'rsi': row[rsi_col]
                        }
                    )
                    signals.append(signal)
                    self.update_last_signal(signal)
                    logger.info(f"Generated SELL signal for {ticker} at {timestamp} (Middle BBand Breakout)")
        
        return signals
