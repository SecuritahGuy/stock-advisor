#!/usr/bin/env python
"""
Test script for Bollinger Bands strategy.

This script allows testing the Bollinger Bands strategy on historical data
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
from app.strategy.bollinger_bands import BBandsStrategy

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("test_bbands")


def test_bbands_strategy(ticker, interval="10min", days=10, 
                         bb_length=20, bb_std=2, rsi_period=14,
                         mean_reversion=True, plot=True):
    """
    Test the Bollinger Bands strategy on historical data.
    
    Args:
        ticker (str): Stock ticker symbol
        interval (str): Data interval
        days (int): Number of days of data to use
        bb_length (int): Bollinger Bands period
        bb_std (float): Number of standard deviations for bands
        rsi_period (int): RSI period
        mean_reversion (bool): Whether to use mean reversion or breakout strategy
        plot (bool): Whether to plot the results
        
    Returns:
        tuple: (DataFrame with data and signals, list of Signal objects)
    """
    logger.info(f"Testing BBands strategy on {ticker} ({interval} data)")
    
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
    strategy = BBandsStrategy(
        bb_length=bb_length, 
        bb_std=bb_std, 
        rsi_period=rsi_period,
        mean_reversion=mean_reversion
    )
    
    # Generate signals
    signals = strategy.generate_signals(df)
    
    # Update DataFrame with signals
    df['signal'] = 0
    for signal in signals:
        idx = df.index[df['Datetime'] == signal.timestamp]
        if len(idx) > 0:
            df.loc[idx, 'signal'] = 1 if signal.action == 'BUY' else -1
    
    # Plot if requested
    if plot and not df.empty:
        plot_bbands_signals(df, ticker, bb_length, rsi_period, mean_reversion)
    
    return df, signals


def plot_bbands_signals(df, ticker, bb_length, rsi_period, mean_reversion):
    """
    Plot the price chart with Bollinger Bands and signals.
    
    Args:
        df (pd.DataFrame): DataFrame with price, indicators, and signals
        ticker (str): Stock ticker symbol
        bb_length (int): Bollinger Bands period
        rsi_period (int): RSI period
        mean_reversion (bool): Whether mean reversion strategy was used
    """
    try:
        import matplotlib.pyplot as plt
        from matplotlib.gridspec import GridSpec
        
        bb_lower = f'bb_lower_{bb_length}'
        bb_middle = f'bb_middle_{bb_length}'
        bb_upper = f'bb_upper_{bb_length}'
        rsi_col = f'rsi{rsi_period}'
        
        # Create figure and subplots
        fig = plt.figure(figsize=(14, 10))
        gs = GridSpec(2, 1, height_ratios=[3, 1])
        ax1 = fig.add_subplot(gs[0])
        ax2 = fig.add_subplot(gs[1], sharex=ax1)
        
        # Plot price and Bollinger Bands
        ax1.plot(df.index, df['Close'], label='Close Price', alpha=0.6)
        ax1.plot(df.index, df[bb_middle], label=f'BBand SMA{bb_length}', linestyle='--', alpha=0.6)
        ax1.fill_between(df.index, df[bb_lower], df[bb_upper], alpha=0.1, color='gray',
                        label=f'BBands ({bb_length}, {2}σ)')
        
        # Plot signals
        buys = df[df['signal'] == 1]
        sells = df[df['signal'] == -1]
        
        if not buys.empty:
            ax1.scatter(buys.index, buys['Close'], marker='^', color='g', s=100, label='Buy')
        if not sells.empty:
            ax1.scatter(sells.index, sells['Close'], marker='v', color='r', s=100, label='Sell')
        
        # Format price chart
        strategy_type = "Mean Reversion" if mean_reversion else "Breakout"
        ax1.set_title(f"{ticker} - Bollinger Bands {strategy_type} Strategy")
        ax1.set_ylabel('Price')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Plot RSI
        ax2.plot(df.index, df[rsi_col], label=f'RSI{rsi_period}', color='purple')
        ax2.axhline(y=70, color='r', linestyle='--', alpha=0.5)
        ax2.axhline(y=30, color='g', linestyle='--', alpha=0.5)
        ax2.fill_between(df.index, 70, 100, alpha=0.1, color='red')
        ax2.fill_between(df.index, 0, 30, alpha=0.1, color='green')
        
        # Format RSI chart
        ax2.set_ylim(0, 100)
        ax2.set_ylabel('RSI')
        ax2.set_xlabel('Date')
        ax2.grid(True, alpha=0.3)
        
        # Add signal stats
        buys_count = len(buys)
        sells_count = len(sells)
        total_signals = buys_count + sells_count
        
        signal_text = (
            f"Total Signals: {total_signals}\n"
            f"Buy Signals: {buys_count}\n"
            f"Sell Signals: {sells_count}"
        )
        
        plt.figtext(0.92, 0.5, signal_text, bbox=dict(facecolor='white', alpha=0.5),
                   verticalalignment='center')
        
        plt.tight_layout()
        plt.show()
        
    except Exception as e:
        logger.error(f"Error plotting results: {str(e)}")


def main():
    """Parse command-line arguments and run the test."""
    parser = argparse.ArgumentParser(description="Test the Bollinger Bands strategy")
    parser.add_argument("ticker", help="Stock ticker symbol")
    parser.add_argument("--interval", choices=["1min", "5min", "10min", "30min", "60min", "1h", "1d"], 
                        default="10min", help="Data interval")
    parser.add_argument("--days", type=int, default=10, help="Number of days of data to use")
    parser.add_argument("--bb-length", type=int, default=20, help="Bollinger Bands period")
    parser.add_argument("--bb-std", type=float, default=2, help="Standard deviations for Bollinger Bands")
    parser.add_argument("--rsi-period", type=int, default=14, help="RSI period")
    parser.add_argument("--breakout", action="store_true", 
                        help="Use breakout strategy (default is mean reversion)")
    parser.add_argument("--no-plot", action="store_true", help="Don't display the plot")
    
    args = parser.parse_args()
    
    mean_reversion = not args.breakout
    
    # Run the test
    df, signals = test_bbands_strategy(
        args.ticker, 
        interval=args.interval, 
        days=args.days,
        bb_length=args.bb_length, 
        bb_std=args.bb_std, 
        rsi_period=args.rsi_period,
        mean_reversion=mean_reversion,
        plot=not args.no_plot
    )
    
    if not signals:
        print(f"No signals generated for {args.ticker}")
        return
    
    # Print signal summary
    print(f"\nGenerated {len(signals)} signals for {args.ticker}:")
    
    buy_signals = [s for s in signals if s.action.value == "BUY"]
    sell_signals = [s for s in signals if s.action.value == "SELL"]
    
    print(f"Buy signals: {len(buy_signals)}")
    print(f"Sell signals: {len(sell_signals)}")
    
    # Print individual signals
    for i, signal in enumerate(signals):
        print(f"\n{i+1}. {signal}")


if __name__ == "__main__":
    main()
