#!/usr/bin/env python
"""
Debug script for MACD + Stochastic strategy.
"""
import pandas as pd
import logging
import matplotlib.pyplot as plt
from datetime import datetime

from app.indicators.tech import calculate_all_indicators
from app.strategy.macd_stochastic import MACDStochasticStrategy

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("debug_macd_stoch")

def debug_macd_stoch(ticker='SPY'):
    """Debug the MACD Stochastic strategy with the given ticker."""
    # Load data
    file_path = f"data/{ticker}_1d_2025-02-15_2025-05-16.parquet"
    try:
        df = pd.read_parquet(file_path)
        logger.info(f"Loaded {len(df)} rows for {ticker}")
    except Exception as e:
        logger.error(f"Failed to load data: {str(e)}")
        return

    # Calculate indicators
    df = calculate_all_indicators(df)
    
    # Print the first few rows with key indicators
    stoch_k_col = 'stoch_k14'
    stoch_d_col = 'stoch_d14'
    selected_cols = ['Date', 'Close', 'macd', 'macd_signal', 'macd_hist', stoch_k_col, stoch_d_col]
    
    print("\nFirst 10 rows with indicators:")
    print(df[selected_cols].head(10))
    
    # Check for NaN values in key columns
    for col in selected_cols:
        if col in df.columns:
            nan_count = df[col].isna().sum()
            print(f"Column {col} has {nan_count} NaN values out of {len(df)} rows")
    
    # Calculate crossovers manually
    df['macd_prev'] = df['macd'].shift(1)
    df['macd_signal_prev'] = df['macd_signal'].shift(1)
    df['stoch_k_prev'] = df[stoch_k_col].shift(1)
    df['stoch_d_prev'] = df[stoch_d_col].shift(1)
    
    # MACD crosses
    df['macd_cross_above'] = (df['macd_prev'] < df['macd_signal_prev']) & (df['macd'] > df['macd_signal'])
    df['macd_cross_below'] = (df['macd_prev'] > df['macd_signal_prev']) & (df['macd'] < df['macd_signal'])
    
    # Stochastic crosses
    df['stoch_cross_above'] = (df['stoch_k_prev'] < df['stoch_d_prev']) & (df[stoch_k_col] > df[stoch_d_col])
    df['stoch_cross_below'] = (df['stoch_k_prev'] > df['stoch_d_prev']) & (df[stoch_k_col] < df[stoch_d_col])
    
    # Count crossovers
    macd_above_count = df['macd_cross_above'].sum()
    macd_below_count = df['macd_cross_below'].sum()
    stoch_above_count = df['stoch_cross_above'].sum()
    stoch_below_count = df['stoch_cross_below'].sum()
    
    print(f"\nMACD crosses above: {macd_above_count}")
    print(f"MACD crosses below: {macd_below_count}")
    print(f"Stochastic crosses above: {stoch_above_count}")
    print(f"Stochastic crosses below: {stoch_below_count}")
    
    # Check for potential buy/sell signals
    buy_conditions1 = df['macd_cross_above'] & (df[stoch_k_col] < 50)
    buy_conditions2 = df['macd_cross_above'] & df['stoch_cross_above'] & (df['stoch_k_prev'] < 20)
    
    sell_conditions1 = df['macd_cross_below'] & (df[stoch_k_col] > 50)
    sell_conditions2 = df['macd_cross_below'] & df['stoch_cross_below'] & (df['stoch_k_prev'] > 80)
    
    # Alternative conditions for small datasets
    alt_buy = ((df['macd'] > df['macd_signal']) & 
              (df['macd'] > df['macd_prev']) &
              (df[stoch_k_col] > df[stoch_d_col]) &
              (df[stoch_k_col] > df['stoch_k_prev']) &
              (df[stoch_k_col] < 40))
    
    alt_sell = ((df['macd'] < df['macd_signal']) & 
               (df['macd'] < df['macd_prev']) &
               (df[stoch_k_col] < df[stoch_d_col]) &
               (df[stoch_k_col] < df['stoch_k_prev']) &
               (df[stoch_k_col] > 60))
    
    print(f"\nBuy condition 1 met: {buy_conditions1.sum()}")
    print(f"Buy condition 2 met: {buy_conditions2.sum()}")
    print(f"Sell condition 1 met: {sell_conditions1.sum()}")
    print(f"Sell condition 2 met: {sell_conditions2.sum()}")
    print(f"Alternative buy condition met: {alt_buy.sum()}")
    print(f"Alternative sell condition met: {alt_sell.sum()}")
    
    # Initialize strategy
    strategy = MACDStochasticStrategy()
    signals = strategy.generate_signals(df)
    
    print(f"\nStrategy generated {len(signals)} signals")
    
    # Plot
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 10), gridspec_kw={'height_ratios': [3, 1, 1]})
    
    # Plot price
    ax1.plot(df['Date'], df['Close'], label='Close Price')
    ax1.set_title(f'MACD + Stochastic Debug - {ticker}')
    
    # Mark buy and sell points
    for i, signal in enumerate(signals):
        idx = df[df['Date'] == signal.timestamp].index[0]
        marker = '^' if signal.action.value == 'BUY' else 'v'
        color = 'g' if signal.action.value == 'BUY' else 'r'
        ax1.scatter(df['Date'].iloc[idx], df['Close'].iloc[idx], marker=marker, color=color, s=100)
        ax1.annotate(f"{i+1}", (df['Date'].iloc[idx], df['Close'].iloc[idx]), 
                    xytext=(5, 5), textcoords='offset points')
    
    # Plot MACD
    ax2.plot(df['Date'], df['macd'], label='MACD')
    ax2.plot(df['Date'], df['macd_signal'], label='Signal')
    ax2.bar(df['Date'], df['macd_hist'], alpha=0.3, label='Histogram')
    ax2.axhline(y=0, color='r', linestyle='-', alpha=0.3)
    ax2.legend()
    
    # Plot Stochastic
    ax3.plot(df['Date'], df[stoch_k_col], label='%K')
    ax3.plot(df['Date'], df[stoch_d_col], label='%D')
    ax3.axhline(y=80, color='r', linestyle='--', alpha=0.5)
    ax3.axhline(y=20, color='g', linestyle='--', alpha=0.5)
    ax3.set_ylim(0, 100)
    ax3.legend()
    
    plt.tight_layout()
    plt.savefig(f"debug_{ticker}_macd_stoch.png")
    print(f"\nPlot saved as debug_{ticker}_macd_stoch.png")
    plt.show()

if __name__ == "__main__":
    import sys
    ticker = 'SPY'
    if len(sys.argv) > 1:
        ticker = sys.argv[1]
    debug_macd_stoch(ticker)
