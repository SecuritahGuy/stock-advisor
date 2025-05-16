"""
Moving Average Crossover strategy implementation.
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
logger = logging.getLogger("ma_crossover")


class MACrossoverStrategy(Strategy):
    """
    Moving Average Crossover strategy implementation.
    
    Generates BUY signals when the fast MA crosses above the slow MA (Golden Cross),
    and SELL signals when the fast MA crosses below the slow MA (Death Cross).
    
    Includes RSI filters to avoid buying in overbought conditions and selling in oversold conditions.
    """
    
    def __init__(self, fast_ma=50, slow_ma=200, rsi_period=14, 
                 rsi_overbought=70, rsi_oversold=30, cooldown_minutes=30):
        """
        Initialize the MA Crossover strategy.
        
        Args:
            fast_ma (int): Fast moving average period
            slow_ma (int): Slow moving average period
            rsi_period (int): RSI period
            rsi_overbought (int): RSI threshold for overbought condition
            rsi_oversold (int): RSI threshold for oversold condition
            cooldown_minutes (int): Minimum minutes between signals
        """
        super().__init__(f"MA{fast_ma}-{slow_ma}_RSI{rsi_period}")
        self.fast_ma = fast_ma
        self.slow_ma = slow_ma
        self.rsi_period = rsi_period
        self.rsi_overbought = rsi_overbought
        self.rsi_oversold = rsi_oversold
        self.cooldown_minutes = cooldown_minutes
        
        logger.info(f"Initialized {self.name} strategy")
    
    def generate_signals(self, df):
        """
        Generate trading signals based on MA crossovers and RSI filters.
        
        Args:
            df (pd.DataFrame): DataFrame with price and indicator data
            
        Returns:
            list: List of Signal objects
        """
        if df.empty:
            logger.warning("Empty DataFrame provided, no signals generated")
            return []
            
        # Check if required columns exist
        required_columns = [
            'ticker', 'Close', 
            f'ma{self.fast_ma}', f'ma{self.slow_ma}', 
            f'rsi{self.rsi_period}'
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
        if len(df) < self.slow_ma:
            logger.warning(f"Not enough data points ({len(df)}) for MA{self.slow_ma} calculation")
            return []
            
        # Calculate crossover signal
        df['fast_ma'] = df[f'ma{self.fast_ma}']
        df['slow_ma'] = df[f'ma{self.slow_ma}']
        df['rsi'] = df[f'rsi{self.rsi_period}']
        
        # Calculate crossover
        df['fast_ma_prev'] = df['fast_ma'].shift(1)
        df['slow_ma_prev'] = df['slow_ma'].shift(1)
        
        # Golden Cross: fast MA crosses above slow MA
        df['golden_cross'] = (df['fast_ma_prev'] < df['slow_ma_prev']) & (df['fast_ma'] > df['slow_ma'])
        
        # Death Cross: fast MA crosses below slow MA
        df['death_cross'] = (df['fast_ma_prev'] > df['slow_ma_prev']) & (df['fast_ma'] < df['slow_ma'])
        
        # Generate signals
        signals = []
        
        for idx, row in df.iterrows():
            # Skip rows with NaN values in key columns
            if pd.isna(row['fast_ma']) or pd.isna(row['slow_ma']) or pd.isna(row['rsi']):
                continue
                
            # Skip if we don't have enough data points yet
            if idx < self.slow_ma:
                continue
                
            timestamp = row[time_col]
            ticker = row['ticker']
            
            # Check if cooled down since last signal
            if not self.can_signal(ticker, timestamp, self.cooldown_minutes):
                continue
                
            # Check for Golden Cross (BUY)
            if row['golden_cross']:
                # RSI filter: avoid buying when overbought
                if row['rsi'] < self.rsi_overbought:
                    signal = Signal(
                        ticker=ticker,
                        action=SignalAction.BUY,
                        strength=SignalStrength.STRONG,
                        reason=f"Golden Cross (MA{self.fast_ma} crosses above MA{self.slow_ma}) with RSI{self.rsi_period}={row['rsi']:.1f}",
                        timestamp=timestamp,
                        price=row['Close'],
                        metadata={
                            'fast_ma': row['fast_ma'],
                            'slow_ma': row['slow_ma'],
                            'rsi': row['rsi']
                        }
                    )
                    signals.append(signal)
                    self.update_last_signal(signal)
                    logger.info(f"Generated BUY signal for {ticker} at {timestamp} (Golden Cross)")
                else:
                    logger.info(f"Filtered out BUY signal for {ticker} at {timestamp} (RSI too high: {row['rsi']:.1f})")
            
            # Check for Death Cross (SELL)
            elif row['death_cross']:
                # RSI filter: avoid selling when oversold
                if row['rsi'] > self.rsi_oversold:
                    signal = Signal(
                        ticker=ticker,
                        action=SignalAction.SELL,
                        strength=SignalStrength.STRONG,
                        reason=f"Death Cross (MA{self.fast_ma} crosses below MA{self.slow_ma}) with RSI{self.rsi_period}={row['rsi']:.1f}",
                        timestamp=timestamp,
                        price=row['Close'],
                        metadata={
                            'fast_ma': row['fast_ma'],
                            'slow_ma': row['slow_ma'],
                            'rsi': row['rsi']
                        }
                    )
                    signals.append(signal)
                    self.update_last_signal(signal)
                    logger.info(f"Generated SELL signal for {ticker} at {timestamp} (Death Cross)")
                else:
                    logger.info(f"Filtered out SELL signal for {ticker} at {timestamp} (RSI too low: {row['rsi']:.1f})")
        
        return signals
