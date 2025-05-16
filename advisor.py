#!/usr/bin/env python
"""
Main advisor script that ties together data fetching, indicator calculation,
signal generation, portfolio tracking, and reporting.
"""
import logging
import argparse
import time
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.data.data_fetch import fetch_stock_data, resample_data, is_market_open
from app.data.storage import load_from_sqlite, save_to_sqlite
from app.indicators.tech import calculate_all_indicators
from app.strategy.ma_crossover import MACrossoverStrategy
from app.strategy.bollinger_bands import BBandsStrategy
from app.portfolio.portfolio import Portfolio
from app.portfolio.valuation import get_latest_prices, store_valuation, get_performance_metrics
from app.report.dashboard import display_dashboard, display_error
from app.report.notify import EmailNotifier

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("advisor.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("advisor")

# List of tickers to track
TICKERS = ["SPY", "AAPL", "MSFT", "GOOGL", "AMZN"]

# Available strategies
STRATEGIES = {
    "ma_crossover": "Moving Average Crossover with RSI filter",
    "bollinger_bands": "Bollinger Bands with RSI filter"
}

# Global variables
portfolio = None
strategy = None
email_notifier = None
signals_today = []


def initialize(strategy_name="ma_crossover"):
    """
    Initialize components.
    
    Args:
        strategy_name (str): Name of the strategy to use
    """
    global portfolio, strategy, email_notifier
    
    # Initialize portfolio
    portfolio = Portfolio("default")
    
    # Initialize strategy
    if strategy_name == "ma_crossover":
        strategy = MACrossoverStrategy(fast_ma=50, slow_ma=200, rsi_period=14)
    elif strategy_name == "bollinger_bands":
        strategy = BBandsStrategy(bb_length=20, bb_std=2, rsi_period=14, mean_reversion=True)
    else:
        logger.error(f"Unknown strategy: {strategy_name}, defaulting to MA crossover")
        strategy = MACrossoverStrategy(fast_ma=50, slow_ma=200, rsi_period=14)
    
    # Initialize email notifier
    email_notifier = EmailNotifier()
    
    logger.info(f"Initialized advisor components with {strategy.name} strategy")


def process_ticker(ticker):
    """
    Process a single ticker: load data, calculate indicators, and generate signals.
    
    Args:
        ticker (str): Stock ticker symbol
        
    Returns:
        list: List of new signals
    """
    try:
        # Load the latest data
        df = load_from_sqlite(table_name="stock_data_10min", ticker=ticker)
        
        if df.empty:
            logger.warning(f"No data found for {ticker}")
            return []
        
        # Calculate indicators if not already present
        if 'rsi14' not in df.columns or f'ma50' not in df.columns or f'ma200' not in df.columns:
            df = calculate_all_indicators(df)
        
        # Generate signals
        new_signals = strategy.generate_signals(df)
        
        # Log signals
        for signal in new_signals:
            logger.info(f"New signal: {signal}")
            
            # Send email alert
            if email_notifier and email_notifier.enabled:
                email_notifier.send_signal_alert(signal)
            
            # Add to today's signals
            today = datetime.now().date()
            if signal.timestamp.date() == today:
                signals_today.append(signal)
        
        return new_signals
        
    except Exception as e:
        logger.error(f"Error processing {ticker}: {str(e)}")
        return []


def process_all_tickers():
    """Process all tickers and return combined signals."""
    all_signals = []
    
    for ticker in TICKERS:
        signals = process_ticker(ticker)
        all_signals.extend(signals)
    
    return all_signals


def update_dashboard():
    """Update the dashboard with the latest data."""
    try:
        # Get latest prices
        price_data = get_latest_prices(TICKERS)
        
        # Update portfolio valuation
        portfolio_data = portfolio.calculate_current_value(price_data)
        
        # Store valuation for historical tracking
        store_valuation(portfolio.name, portfolio_data)
        
        # Get performance metrics
        metrics = get_performance_metrics(portfolio.name, period="all")
        
        # Process tickers for signals
        new_signals = process_all_tickers()
        
        # Get all of today's signals
        today = datetime.now().date()
        today_signals = [s for s in signals_today if s.timestamp.date() == today]
        
        # Display dashboard
        display_dashboard(portfolio_data, today_signals, metrics)
        
        return new_signals
        
    except Exception as e:
        logger.error(f"Error updating dashboard: {str(e)}")
        display_error(f"Error updating dashboard: {str(e)}")
        return []


def send_daily_summary():
    """Send a daily summary email at market close."""
    try:
        # Check if market was open today
        now = datetime.now()
        if now.weekday() > 4:  # Weekend
            logger.info("Market closed (weekend), skipping daily summary")
            return
        
        # Get latest prices
        price_data = get_latest_prices(TICKERS)
        
        # Update portfolio valuation
        portfolio_data = portfolio.calculate_current_value(price_data)
        
        # Get performance metrics
        metrics = get_performance_metrics(portfolio.name, period="day")
        
        # Get today's signals
        today = datetime.now().date()
        today_signals = [s for s in signals_today if s.timestamp.date() == today]
        
        # Send daily summary email
        if email_notifier and email_notifier.enabled:
            email_notifier.send_daily_summary(portfolio_data, today_signals, metrics)
            logger.info("Sent daily summary email")
        
    except Exception as e:
        logger.error(f"Error sending daily summary: {str(e)}")


def run_scheduler():
    """Start the scheduler for periodic updates."""
    scheduler = BackgroundScheduler()
    
    # Update dashboard every 10 minutes during market hours
    scheduler.add_job(
        update_dashboard,
        CronTrigger.from_crontab("*/10 * * * *"),
        id="update_dashboard",
        name="Update Dashboard Every 10 Minutes"
    )
    
    # Send daily summary at market close (4:00 PM EST)
    scheduler.add_job(
        send_daily_summary,
        CronTrigger.from_crontab("0 16 * * 1-5"),  # 4:00 PM, Monday-Friday
        id="daily_summary",
        name="Send Daily Summary at Market Close"
    )
    
    logger.info("Starting scheduler...")
    scheduler.start()
    
    try:
        # Initial update
        update_dashboard()
        
        # Keep the script running
        while True:
            time.sleep(60)
            
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scheduler shutdown requested")
        scheduler.shutdown()
        logger.info("Scheduler shut down successfully")


def run_once():
    """Run the advisor once for testing purposes."""
    logger.info("Running one-time advisor update")
    update_dashboard()
    logger.info("One-time update completed")


def main():
    """Main function to parse arguments and run the advisor."""
    parser = argparse.ArgumentParser(description="Stock Advisor Dashboard")
    parser.add_argument("--once", action="store_true", help="Run once without scheduling")
    parser.add_argument("--daily-summary", action="store_true", help="Send daily summary now")
    parser.add_argument("--strategy", choices=list(STRATEGIES.keys()), default="ma_crossover",
                       help="Trading strategy to use")
    parser.add_argument("--tickers", nargs="+", help="List of ticker symbols (overrides defaults)")
    
    args = parser.parse_args()
    
    # Override tickers if specified
    global TICKERS
    if args.tickers:
        TICKERS = args.tickers
        logger.info(f"Using custom ticker list: {TICKERS}")
    
    # Initialize components with selected strategy
    initialize(args.strategy)
    
    if args.daily_summary:
        send_daily_summary()
    elif args.once:
        run_once()
    else:
        run_scheduler()


if __name__ == "__main__":
    main()
