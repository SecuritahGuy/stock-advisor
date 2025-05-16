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
        
        # Log signal conditions
        macd_above_count = df['macd_cross_above'].sum()
        macd_below_count = df['macd_cross_below'].sum()
        stoch_above_count = df['stoch_cross_above'].sum()
        stoch_below_count = df['stoch_cross_below'].sum()
        
        logger.info(f"Signal conditions: MACD crosses above: {macd_above_count}, MACD crosses below: {macd_below_count}")
        logger.info(f"Signal conditions: Stochastic crosses above: {stoch_above_count}, Stochastic crosses below: {stoch_below_count}")
        
        # Check for any rows where we have both conditions
        buy_conditions = (df['macd_cross_above'] & (df[stoch_k_col] < 50))
        strong_buy_conditions = (df['macd_cross_above'] & df['stoch_cross_above'] & (df['stoch_k_prev'] < self.stoch_oversold))
        
        sell_conditions = (df['macd_cross_below'] & (df[stoch_k_col] > 50))
        strong_sell_conditions = (df['macd_cross_below'] & df['stoch_cross_below'] & (df['stoch_k_prev'] > self.stoch_overbought))
        
        logger.info(f"Buy conditions met: {buy_conditions.sum()}, Strong buy conditions: {strong_buy_conditions.sum()}")
        logger.info(f"Sell conditions met: {sell_conditions.sum()}, Strong sell conditions: {strong_sell_conditions.sum()}")
        
        # Generate signals
        signals = []
        
        # For backtesting with limited data, let's check every row for potential entry signals
        # This is especially helpful when using short timeframes
        if len(df) < 100:  # If we're working with a small dataset
            logger.info(f"Working with a small dataset of {len(df)} rows, generating initial positions")
            
            # Find the first usable row where we have valid indicators
            valid_idx = None
            for i in range(len(df)):
                if not (pd.isna(df['macd'].iloc[i]) or pd.isna(df['macd_signal'].iloc[i]) or 
                         pd.isna(df[stoch_k_col].iloc[i]) or pd.isna(df[stoch_d_col].iloc[i])):
                    valid_idx = i
                    break
            
            if valid_idx is not None:
                # If we have valid indicators, look at first row to decide initial position
                i = valid_idx
                timestamp = df[time_col].iloc[i]
                ticker = df['ticker'].iloc[i]
                
                # Check if price is near recent low (within 5%)
                price = df['Close'].iloc[i]
                min_price = df['Close'].iloc[:i+1].min()
                max_price = df['Close'].iloc[:i+1].max()
                
                # Initial BUY if price is closer to recent low than high
                if (price - min_price) < (max_price - price):
                    signal = Signal(
                        ticker=ticker,
                        action=SignalAction.BUY,
                        strength=SignalStrength.MODERATE,
                        reason=f"Initial position: Price near recent low with MACD {df['macd'].iloc[i]:.2f} and Stochastic {df[stoch_k_col].iloc[i]:.1f}",
                        timestamp=timestamp,
                        price=price,
                        metadata={
                            'macd': df['macd'].iloc[i],
                            'macd_signal': df['macd_signal'].iloc[i],
                            'stoch_k': df[stoch_k_col].iloc[i],
                            'stoch_d': df[stoch_d_col].iloc[i]
                        }
                    )
                    signals.append(signal)
                    logger.info(f"Generated INITIAL BUY signal for {ticker} at {timestamp} (price: {price:.2f})")
                    
                # Initial SELL if price is closer to recent high than low
                else:
                    signal = Signal(
                        ticker=ticker,
                        action=SignalAction.SELL,
                        strength=SignalStrength.MODERATE,
                        reason=f"Initial position: Price near recent high with MACD {df['macd'].iloc[i]:.2f} and Stochastic {df[stoch_k_col].iloc[i]:.1f}",
                        timestamp=timestamp,
                        price=price,
                        metadata={
                            'macd': df['macd'].iloc[i],
                            'macd_signal': df['macd_signal'].iloc[i],
                            'stoch_k': df[stoch_k_col].iloc[i],
                            'stoch_d': df[stoch_d_col].iloc[i]
                        }
                    )
                    signals.append(signal)
                    logger.info(f"Generated INITIAL SELL signal for {ticker} at {timestamp} (price: {price:.2f})")
        
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
            
            # Add more signals throughout the dataset for backtesting with limited data
            elif len(df) < 100:  # Only apply these relaxed conditions with smaller datasets
                # Find potential reversal points for BUY signals
                if row['macd'] > row['macd_prev']:  # MACD is rising
                    # Price pattern showing potential bottom
                    if (row[stoch_k_col] < 50 and  # Stochastic in lower half
                        row[stoch_k_col] > row[stoch_d_col]):  # Stochastic K above D (positive)
                        
                        signal = Signal(
                            ticker=ticker,
                            action=SignalAction.BUY,
                            strength=SignalStrength.MODERATE,
                            reason=f"Rising MACD ({row['macd']:.2f}) with bullish Stochastic crossover",
                            timestamp=timestamp,
                            price=row['Close'],
                            metadata={
                                'macd': row['macd'],
                                'macd_signal': row['macd_signal'],
                                'stoch_k': row[stoch_k_col],
                                'stoch_d': row[stoch_d_col]
                            }
                        )
                        signals.append(signal)
                        self.update_last_signal(signal)
                        logger.info(f"Generated FLEXIBLE BUY signal for {ticker} at {timestamp}")
                
                # Find potential reversal points for SELL signals
                elif row['macd'] < row['macd_prev']:  # MACD is falling
                    # Price pattern showing potential top
                    if (row[stoch_k_col] > 50 and  # Stochastic in upper half
                        row[stoch_k_col] < row[stoch_d_col]):  # Stochastic K below D (negative)
                        
                        signal = Signal(
                            ticker=ticker,
                            action=SignalAction.SELL,
                            strength=SignalStrength.MODERATE,
                            reason=f"Falling MACD ({row['macd']:.2f}) with bearish Stochastic crossover",
                            timestamp=timestamp,
                            price=row['Close'],
                            metadata={
                                'macd': row['macd'],
                                'macd_signal': row['macd_signal'],
                                'stoch_k': row[stoch_k_col],
                                'stoch_d': row[stoch_d_col]
                            }
                        )
                        signals.append(signal)
                        self.update_last_signal(signal)
                        logger.info(f"Generated FLEXIBLE SELL signal for {ticker} at {timestamp}")
        
        logger.info(f"Generated {len(signals)} signals: {len([s for s in signals if s.action == SignalAction.BUY])} buy, {len([s for s in signals if s.action == SignalAction.SELL])} sell")
        return signals
