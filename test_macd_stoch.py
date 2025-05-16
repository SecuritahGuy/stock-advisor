#!/usr/bin/env python
"""
Test script for MACD + Stochastic strategy.

This script allows testing the MACD + Stochastic strategy on historical data
and visualizing the signals generated.
"""
import argparse
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import sys
import logging

from app.data.data_fetch import fetch_stock_data
from app.data.storage import load_from_sqlite, load_from_parquet
from app.indicators.tech import calculate_all_indicators
from app.strategy.macd_stochastic import MACDStochasticStrategy

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("test_macd_stoch")


def test_macd_stoch_strategy(ticker, interval="1d", days=60, 
                          macd_fast=12, macd_slow=26, macd_signal=9,
                          stoch_k=14, stoch_d=3, stoch_smooth=3,
                          stoch_overbought=80, stoch_oversold=20,
                          plot=True):
    """
    Test the MACD + Stochastic strategy on historical data.
    
    Args:
        ticker (str): Stock ticker symbol
        interval (str): Data interval
        days (int): Number of days of data to use
        macd_fast (int): MACD fast period
        macd_slow (int): MACD slow period
        macd_signal (int): MACD signal period
        stoch_k (int): Stochastic %K period
        stoch_d (int): Stochastic %D period
        stoch_smooth (int): Stochastic %K smoothing
        stoch_overbought (int): Stochastic overbought threshold
        stoch_oversold (int): Stochastic oversold threshold
        plot (bool): Whether to plot the results
        
    Returns:
        tuple: (DataFrame with data and signals, list of Signal objects)
    """
    logger.info(f"Testing MACD+Stochastic strategy on {ticker} ({interval} data)")
    
    # Try to load data from storage first
    try:
        # Try SQLite
        table_name = f"stock_data_{interval}"
        start_date = datetime.now() - timedelta(days=days)
        df = load_from_sqlite(table_name=table_name, ticker=ticker, start_date=start_date)
        
        # If no data in SQLite, try Parquet
        if df.empty:
            logger.info(f"No data in SQLite, trying Parquet for {ticker}")
            df = load_from_parquet(ticker, interval=interval)
        
        # If still no data, fetch from Yahoo Finance
        if df.empty:
            logger.info(f"No data in storage, fetching from Yahoo Finance for {ticker}")
            
            # Convert interval format (10min -> 10m for yfinance)
            yf_interval = interval.replace('min', 'm')
            df = fetch_stock_data(ticker, interval=yf_interval, period=f"{days}d")
    
    except Exception as e:
        logger.error(f"Error loading data: {str(e)}")
        logger.info(f"Fetching from Yahoo Finance for {ticker}")
        
        # Convert interval format (10min -> 10m for yfinance)
        yf_interval = interval.replace('min', 'm')
        df = fetch_stock_data(ticker, interval=yf_interval, period=f"{days}d")
    
    if df.empty:
        logger.error(f"No data available for {ticker}")
        return None, []
    
    # Make sure the ticker column is populated
    if 'ticker' not in df.columns:
        df['ticker'] = ticker
        
    # Calculate indicators
    df = calculate_all_indicators(df)
    
    # Initialize strategy
    strategy = MACDStochasticStrategy(
        fast=macd_fast,
        slow=macd_slow,
        signal=macd_signal,
        stoch_k=stoch_k,
        stoch_d=stoch_d,
        smooth_k=stoch_smooth,
        stoch_overbought=stoch_overbought,
        stoch_oversold=stoch_oversold
    )
    
    # Generate signals
    signals = strategy.generate_signals(df)
    
    # Update DataFrame with signals
    df['signal'] = 0
    for signal in signals:
        # Find the index for this timestamp
        if 'Date' in df.columns:
            idx = df[df['Date'] == signal.timestamp].index
        else:
            idx = df[df['Datetime'] == signal.timestamp].index
            
        if len(idx) > 0:
            if signal.action.value == 'BUY':
                df.loc[idx[0], 'signal'] = 1
            else:  # SELL
                df.loc[idx[0], 'signal'] = -1
    
    if plot:
        plot_strategy(df, signals, ticker, strategy.name)
    
    return df, signals


def plot_strategy(df, signals, ticker, strategy_name):
    """
    Plot the strategy results with price, indicators, and signals.
    
    Args:
        df (pd.DataFrame): DataFrame with price data and indicators
        signals (list): List of Signal objects
        ticker (str): Stock ticker symbol
        strategy_name (str): Name of the strategy
    """
    # Create figure with subplots
    fig = plt.figure(figsize=(12, 12))
    
    # Determine the time column
    time_col = 'Date' if 'Date' in df.columns else 'Datetime'
    
    # Convert to datetime if not already
    df[time_col] = pd.to_datetime(df[time_col])
    
    # Create subplots
    ax1 = plt.subplot2grid((4, 1), (0, 0), rowspan=2)
    ax2 = plt.subplot2grid((4, 1), (2, 0))
    ax3 = plt.subplot2grid((4, 1), (3, 0))
    
    # Set titles
    ax1.set_title(f"{ticker} - MACD + Stochastic Strategy Test")
    
    # Plot price
    ax1.plot(df[time_col], df['Close'], label='Close Price')
    
    # Add Buy/Sell markers
    buy_signals = df[df['signal'] == 1]
    sell_signals = df[df['signal'] == -1]
    
    ax1.scatter(buy_signals[time_col], buy_signals['Close'], marker='^', color='g', s=100, label='Buy Signal')
    ax1.scatter(sell_signals[time_col], sell_signals['Close'], marker='v', color='r', s=100, label='Sell Signal')
    
    # Plot MACD
    ax2.plot(df[time_col], df['macd'], label='MACD')
    ax2.plot(df[time_col], df['macd_signal'], label='Signal Line')
    ax2.bar(df[time_col], df['macd_hist'], color='gray', alpha=0.3, label='MACD Histogram')
    ax2.axhline(y=0, color='k', linestyle='--')
    ax2.set_ylabel('MACD')
    
    # Plot Stochastic Oscillator
    stoch_k_col = f'stoch_k{signals[0].metadata["stoch_k"] if signals else 14}'
    stoch_d_col = f'stoch_d{signals[0].metadata["stoch_k"] if signals else 14}'
    
    ax3.plot(df[time_col], df[stoch_k_col], label='%K')
    ax3.plot(df[time_col], df[stoch_d_col], label='%D')
    ax3.axhline(y=80, color='r', linestyle='--')
    ax3.axhline(y=20, color='g', linestyle='--')
    ax3.fill_between(df[time_col], 80, 100, color='r', alpha=0.1)
    ax3.fill_between(df[time_col], 0, 20, color='g', alpha=0.1)
    ax3.set_ylabel('Stochastic')
    ax3.set_ylim(0, 100)
    
    # Format x-axis
    for ax in [ax1, ax2, ax3]:
        ax.legend()
        ax.grid(True)
        
    # Add signal summary text
    buy_count = len(buy_signals)
    sell_count = len(sell_signals)
    
    summary_text = (
        f"Buy Signals: {buy_count}\n"
        f"Sell Signals: {sell_count}\n"
        f"Total Signals: {buy_count + sell_count}\n"
        f"MACD: Fast={signals[0].metadata['macd']:.2f}, "
        f"Slow={signals[0].metadata['macd_signal']:.2f}\n"
        f"Stochastic: %K={signals[0].metadata['stoch_k']:.1f}, "
        f"%D={signals[0].metadata['stoch_d']:.1f}"
    ) if signals else "No signals generated"
    
    # Add text box with summary
    bbox_props = dict(boxstyle="round,pad=0.5", fc="white", alpha=0.8)
    ax1.text(0.02, 0.02, summary_text, transform=ax1.transAxes, fontsize=10,
            verticalalignment='bottom', bbox=bbox_props)
    
    plt.tight_layout()
    plt.show()


def main():
    """Parse arguments and run the strategy test."""
    parser = argparse.ArgumentParser(description="Test MACD + Stochastic strategy")
    
    parser.add_argument("ticker", help="Stock ticker symbol")
    parser.add_argument("--interval", default="1d", help="Data interval")
    parser.add_argument("--days", type=int, default=60, help="Number of days of data to use")
    
    # MACD parameters
    parser.add_argument("--macd-fast", type=int, default=12, help="MACD fast period")
    parser.add_argument("--macd-slow", type=int, default=26, help="MACD slow period")
    parser.add_argument("--macd-signal", type=int, default=9, help="MACD signal period")
    
    # Stochastic parameters
    parser.add_argument("--stoch-k", type=int, default=14, help="Stochastic %K period")
    parser.add_argument("--stoch-d", type=int, default=3, help="Stochastic %D period")
    parser.add_argument("--stoch-smooth", type=int, default=3, help="Stochastic %K smoothing")
    parser.add_argument("--stoch-overbought", type=int, default=80, help="Stochastic overbought threshold")
    parser.add_argument("--stoch-oversold", type=int, default=20, help="Stochastic oversold threshold")
    
    # Plotting option
    parser.add_argument("--no-plot", action="store_true", help="Disable plotting")
    
    args = parser.parse_args()
    
    # Run the test
    test_macd_stoch_strategy(
        ticker=args.ticker,
        interval=args.interval,
        days=args.days,
        macd_fast=args.macd_fast,
        macd_slow=args.macd_slow,
        macd_signal=args.macd_signal,
        stoch_k=args.stoch_k,
        stoch_d=args.stoch_d,
        stoch_smooth=args.stoch_smooth,
        stoch_overbought=args.stoch_overbought,
        stoch_oversold=args.stoch_oversold,
        plot=not args.no_plot
    )


if __name__ == "__main__":
    main()
