"""
Backtesting module for validating trading strategies with historical data.
"""
import logging
import argparse
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import json
from pathlib import Path
from datetime import datetime, timedelta
import yfinance as yf

from app.indicators.tech import calculate_all_indicators
from app.strategy.ma_crossover import MACrossoverStrategy
from app.strategy.bollinger_bands import BBandsStrategy
from app.strategy.base import SignalAction

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("backtest")

# Define paths
DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)
RESULTS_DIR = Path(__file__).parent / "results"
RESULTS_DIR.mkdir(exist_ok=True)


def fetch_historical_data(ticker, start_date, end_date, interval="1d"):
    """
    Fetch historical data for backtesting.
    
    Args:
        ticker (str): Stock ticker symbol
        start_date (str): Start date (YYYY-MM-DD)
        end_date (str): End date (YYYY-MM-DD)
        interval (str): Data interval (e.g., "1d", "1wk")
        
    Returns:
        pd.DataFrame: DataFrame with historical data
    """
    try:
        logger.info(f"Fetching historical data for {ticker} from {start_date} to {end_date}")
        
        ticker_obj = yf.Ticker(ticker)
        df = ticker_obj.history(start=start_date, end=end_date, interval=interval)
        
        if df.empty:
            logger.warning(f"No data returned for {ticker}")
            return pd.DataFrame()
            
        # Reset index to make Date a column
        df = df.reset_index()
        
        # Add ticker column
        df['ticker'] = ticker
        
        logger.info(f"Successfully fetched {len(df)} rows for {ticker}")
        
        # Save data to Parquet for caching
        file_path = DATA_DIR / f"{ticker}_{interval}_{start_date}_{end_date}.parquet"
        df.to_parquet(file_path, compression="snappy")
        logger.info(f"Saved historical data to {file_path}")
        
        return df
        
    except Exception as e:
        logger.error(f"Error fetching historical data for {ticker}: {str(e)}")
        return pd.DataFrame()


def load_historical_data(ticker, start_date, end_date, interval="1d"):
    """
    Load historical data from cache or fetch if not available.
    
    Args:
        ticker (str): Stock ticker symbol
        start_date (str): Start date (YYYY-MM-DD)
        end_date (str): End date (YYYY-MM-DD)
        interval (str): Data interval (e.g., "1d", "1wk")
        
    Returns:
        pd.DataFrame: DataFrame with historical data
    """
    file_path = DATA_DIR / f"{ticker}_{interval}_{start_date}_{end_date}.parquet"
    
    if file_path.exists():
        try:
            logger.info(f"Loading historical data from {file_path}")
            df = pd.read_parquet(file_path)
            logger.info(f"Loaded {len(df)} rows for {ticker}")
            return df
        except Exception as e:
            logger.error(f"Error loading data from {file_path}: {str(e)}")
            # Fall back to fetching
    
    return fetch_historical_data(ticker, start_date, end_date, interval)


class Backtester:
    """Class for backtesting trading strategies."""
    
    def __init__(self, strategy, initial_capital=10000.0, commission=0.001):
        """
        Initialize the backtester.
        
        Args:
            strategy: Strategy object
            initial_capital (float): Initial capital
            commission (float): Commission rate as a fraction of trade value
        """
        self.strategy = strategy
        self.initial_capital = initial_capital
        self.commission = commission
        logger.info(f"Initialized backtester with {self.strategy.name} strategy")
        
    def run(self, df):
        """
        Run a backtest on historical data.
        
        Args:
            df (pd.DataFrame): DataFrame with historical price data and indicators
            
        Returns:
            dict: Backtest results
        """
        if df.empty:
            logger.warning("Empty DataFrame provided, backtest aborted")
            return None
            
        # Add indicators if not present
        df = calculate_all_indicators(df)
        
        # Generate signals
        signals = self.strategy.generate_signals(df)
        
        # Create a DataFrame from signals for easier processing
        if not signals:
            logger.warning("No signals generated, backtest aborted")
            return None
            
        signal_data = []
        for signal in signals:
            signal_data.append({
                'ticker': signal.ticker,
                'action': signal.action.value,
                'price': signal.price,
                'timestamp': signal.timestamp,
                'strength': signal.strength.value,
                'reason': signal.reason
            })
            
        signal_df = pd.DataFrame(signal_data)
        
        # Merge signals with price data
        # Use Date or Datetime column depending on what's available
        time_col = 'Date' if 'Date' in df.columns else 'Datetime'
        
        # Convert to the same datetime type
        signal_df['timestamp'] = pd.to_datetime(signal_df['timestamp'])
        df[time_col] = pd.to_datetime(df[time_col])
        
        # Create a combined DataFrame with signals indicated
        combined = df.copy()
        combined['signal'] = np.nan
        
        for _, row in signal_df.iterrows():
            # Find the closest timestamp in the price data
            closest_idx = (combined[time_col] - row['timestamp']).abs().idxmin()
            if row['action'] == 'BUY':
                combined.loc[closest_idx, 'signal'] = 1
            elif row['action'] == 'SELL':
                combined.loc[closest_idx, 'signal'] = -1
        
        # Simulate portfolio
        portfolio = self._simulate_portfolio(combined)
        
        # Calculate performance metrics
        metrics = self._calculate_metrics(portfolio)
        
        # Combine results
        results = {
            'strategy': self.strategy.name,
            'ticker': df['ticker'].iloc[0],
            'start_date': df[time_col].min().strftime('%Y-%m-%d'),
            'end_date': df[time_col].max().strftime('%Y-%m-%d'),
            'signals': len(signal_df),
            'buy_signals': len(signal_df[signal_df['action'] == 'BUY']),
            'sell_signals': len(signal_df[signal_df['action'] == 'SELL']),
            'metrics': metrics,
            'portfolio': portfolio.to_dict(orient='records')
        }
        
        return results
        
    def _simulate_portfolio(self, df):
        """
        Simulate portfolio performance based on signals.
        
        Args:
            df (pd.DataFrame): DataFrame with price data and signals
            
        Returns:
            pd.DataFrame: DataFrame with portfolio simulation
        """
        # Initialize portfolio metrics
        portfolio = df[['Date' if 'Date' in df.columns else 'Datetime', 'Close', 'signal']].copy()
        portfolio.columns = ['timestamp', 'price', 'signal']
        
        portfolio['position'] = portfolio['signal'].fillna(0).cumsum()
        portfolio['position'] = portfolio['position'].apply(lambda x: max(min(x, 1), 0))  # Limit to 0-1 (no short selling)
        
        # Calculate cash and holdings
        portfolio['cash'] = self.initial_capital
        portfolio['holdings'] = 0
        portfolio['total'] = self.initial_capital
        
        current_cash = self.initial_capital
        current_position = 0
        
        for i in range(len(portfolio)):
            # Update position based on signal
            if portfolio.loc[i, 'signal'] == 1 and current_position == 0:  # BUY
                # Calculate shares to buy (use all available cash)
                price = portfolio.loc[i, 'price']
                shares = current_cash / price / (1 + self.commission)
                
                # Update holdings and cash
                current_position = 1
                current_cash = 0
                portfolio.loc[i, 'holdings'] = shares * price
                portfolio.loc[i, 'cash'] = current_cash
                
            elif portfolio.loc[i, 'signal'] == -1 and current_position == 1:  # SELL
                # Calculate cash from selling shares
                price = portfolio.loc[i, 'price']
                prev_holdings = portfolio.loc[i-1, 'holdings']
                shares = prev_holdings / portfolio.loc[i-1, 'price']
                
                # Update holdings and cash
                current_position = 0
                current_cash = shares * price * (1 - self.commission)
                portfolio.loc[i, 'holdings'] = 0
                portfolio.loc[i, 'cash'] = current_cash
                
            else:
                # No change in position
                if i > 0:
                    portfolio.loc[i, 'cash'] = portfolio.loc[i-1, 'cash']
                    
                    if current_position == 1:
                        # Update holdings value
                        price = portfolio.loc[i, 'price']
                        prev_price = portfolio.loc[i-1, 'price']
                        prev_holdings = portfolio.loc[i-1, 'holdings']
                        
                        portfolio.loc[i, 'holdings'] = prev_holdings * (price / prev_price)
                    else:
                        portfolio.loc[i, 'holdings'] = 0
            
            # Calculate total value
            portfolio.loc[i, 'total'] = portfolio.loc[i, 'cash'] + portfolio.loc[i, 'holdings']
        
        # Calculate daily returns
        portfolio['daily_return'] = portfolio['total'].pct_change()
        
        return portfolio
        
    def _calculate_metrics(self, portfolio):
        """
        Calculate performance metrics from portfolio simulation.
        
        Args:
            portfolio (pd.DataFrame): DataFrame with portfolio simulation
            
        Returns:
            dict: Dictionary with performance metrics
        """
        # Basic metrics
        initial_value = self.initial_capital
        final_value = portfolio['total'].iloc[-1]
        total_return = (final_value / initial_value) - 1
        
        # Calculate time period in years
        start_date = portfolio['timestamp'].min()
        end_date = portfolio['timestamp'].max()
        years = (end_date - start_date).days / 365.25
        
        # Calculate CAGR (Compound Annual Growth Rate)
        cagr = (final_value / initial_value) ** (1 / years) - 1 if years > 0 else 0
        
        # Calculate volatility (annualized)
        daily_returns = portfolio['daily_return'].dropna()
        volatility = daily_returns.std() * (252 ** 0.5)  # Annualized
        
        # Calculate maximum drawdown
        portfolio['peak'] = portfolio['total'].cummax()
        portfolio['drawdown'] = (portfolio['total'] - portfolio['peak']) / portfolio['peak']
        max_drawdown = portfolio['drawdown'].min()
        
        # Calculate Sharpe ratio (assuming risk-free rate of 0% for simplicity)
        sharpe_ratio = (cagr / volatility) if volatility > 0 else 0
        
        # Calculate win rate
        # First, identify trades
        portfolio['trade_start'] = portfolio['position'].diff() == 1
        portfolio['trade_end'] = portfolio['position'].diff() == -1
        
        trades = []
        open_price = None
        
        for i, row in portfolio.iterrows():
            if row['trade_start']:
                open_price = row['price']
            elif row['trade_end'] and open_price is not None:
                close_price = row['price']
                profit = (close_price / open_price) - 1
                trades.append(profit)
                open_price = None
        
        # Calculate win rate and profit factor
        if trades:
            winning_trades = sum(1 for t in trades if t > 0)
            win_rate = winning_trades / len(trades)
            
            gross_profit = sum(t for t in trades if t > 0)
            gross_loss = abs(sum(t for t in trades if t < 0))
            profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
        else:
            win_rate = 0
            profit_factor = 0
        
        return {
            'initial_value': initial_value,
            'final_value': final_value,
            'total_return': total_return,
            'total_return_pct': total_return * 100,
            'cagr': cagr,
            'cagr_pct': cagr * 100,
            'volatility': volatility,
            'volatility_pct': volatility * 100,
            'max_drawdown': max_drawdown,
            'max_drawdown_pct': max_drawdown * 100,
            'sharpe_ratio': sharpe_ratio,
            'win_rate': win_rate,
            'win_rate_pct': win_rate * 100,
            'profit_factor': profit_factor,
            'trades': len(trades),
            'years': years
        }
    
    def plot_results(self, results, save_path=None):
        """
        Plot backtest results.
        
        Args:
            results (dict): Backtest results
            save_path (str): Path to save the plot
            
        Returns:
            matplotlib.figure.Figure: Figure object
        """
        if not results:
            logger.warning("No results to plot")
            return None
            
        portfolio = pd.DataFrame(results['portfolio'])
        
        # Create figure
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10), gridspec_kw={'height_ratios': [3, 1]})
        
        # Plot portfolio value
        portfolio['timestamp'] = pd.to_datetime(portfolio['timestamp'])
        portfolio.set_index('timestamp', inplace=True)
        
        ax1.plot(portfolio.index, portfolio['total'], label='Portfolio Value')
        ax1.plot(portfolio.index, portfolio['cash'], label='Cash', alpha=0.5)
        ax1.plot(portfolio.index, portfolio['holdings'], label='Holdings', alpha=0.5)
        
        # Add buy/sell markers
        buys = portfolio[portfolio['signal'] == 1]
        sells = portfolio[portfolio['signal'] == -1]
        
        ax1.scatter(buys.index, buys['total'], marker='^', color='g', s=100, label='Buy')
        ax1.scatter(sells.index, sells['total'], marker='v', color='r', s=100, label='Sell')
        
        # Add buy/hold comparison
        benchmark = portfolio.copy()
        shares = self.initial_capital / benchmark['price'].iloc[0]
        benchmark['buy_hold'] = shares * benchmark['price']
        ax1.plot(benchmark.index, benchmark['buy_hold'], 'k--', label='Buy & Hold')
        
        # Format first subplot
        ax1.set_title(f"Backtest Results: {results['strategy']} on {results['ticker']}")
        ax1.set_ylabel('Portfolio Value ($)')
        ax1.legend()
        ax1.grid(True)
        
        # Plot drawdown
        portfolio['drawdown'] = (portfolio['total'] - portfolio['total'].cummax()) / portfolio['total'].cummax()
        ax2.fill_between(portfolio.index, 0, portfolio['drawdown'] * 100, color='r', alpha=0.3)
        ax2.set_ylabel('Drawdown (%)')
        ax2.set_xlabel('Date')
        ax2.grid(True)
        
        # Add metrics as text
        metrics = results['metrics']
        metrics_text = (
            f"Total Return: {metrics['total_return_pct']:.2f}%\n"
            f"CAGR: {metrics['cagr_pct']:.2f}%\n"
            f"Volatility: {metrics['volatility_pct']:.2f}%\n"
            f"Max Drawdown: {metrics['max_drawdown_pct']:.2f}%\n"
            f"Sharpe Ratio: {metrics['sharpe_ratio']:.2f}\n"
            f"Win Rate: {metrics['win_rate_pct']:.2f}%\n"
            f"Trades: {metrics['trades']}"
        )
        
        # Add text box with metrics
        bbox_props = dict(boxstyle="round,pad=0.5", fc="white", alpha=0.8)
        ax1.text(0.02, 0.98, metrics_text, transform=ax1.transAxes, fontsize=10,
                verticalalignment='top', bbox=bbox_props)
        
        plt.tight_layout()
        
        # Save figure if path provided
        if save_path:
            plt.savefig(save_path)
            logger.info(f"Saved plot to {save_path}")
        
        return fig


def run_backtest(ticker, strategy, start_date, end_date, interval="1d", plot=True):
    """
    Run a backtest for a single ticker and strategy.
    
    Args:
        ticker (str): Stock ticker symbol
        strategy: Strategy object
        start_date (str): Start date (YYYY-MM-DD)
        end_date (str): End date (YYYY-MM-DD)
        interval (str): Data interval (e.g., "1d", "1wk")
        plot (bool): Whether to generate a plot
        
    Returns:
        dict: Backtest results
    """
    # Load historical data
    df = load_historical_data(ticker, start_date, end_date, interval)
    
    if df.empty:
        logger.error(f"No data available for {ticker}, backtest aborted")
        return None
        
    # Run backtest
    backtester = Backtester(strategy)
    results = backtester.run(df)
    
    if not results:
        logger.error(f"Backtest failed for {ticker}")
        return None
        
    # Save results to JSON
    result_file = RESULTS_DIR / f"backtest_{ticker}_{start_date}_{end_date}_{strategy.name}.json"
    
    with open(result_file, 'w') as f:
        # Convert DataFrames to lists for JSON serialization
        results_json = results.copy()
        results_json['portfolio'] = pd.DataFrame(results_json['portfolio']).to_dict(orient='records')
        json.dump(results_json, f, indent=2, default=str)
        
    logger.info(f"Saved backtest results to {result_file}")
    
    # Plot results if requested
    if plot:
        plot_file = RESULTS_DIR / f"backtest_{ticker}_{start_date}_{end_date}_{strategy.name}.png"
        backtester.plot_results(results, save_path=plot_file)
    
    return results


def parameter_sweep(ticker, param_grid, start_date, end_date, interval="1d"):
    """
    Perform a parameter sweep to find optimal strategy parameters.
    
    Args:
        ticker (str): Stock ticker symbol
        param_grid (dict): Dictionary of parameter names and values to test
        start_date (str): Start date (YYYY-MM-DD)
        end_date (str): End date (YYYY-MM-DD)
        interval (str): Data interval (e.g., "1d", "1wk")
        
    Returns:
        pd.DataFrame: DataFrame with parameter sweep results
    """
    # Load historical data once
    df = load_historical_data(ticker, start_date, end_date, interval)
    
    if df.empty:
        logger.error(f"No data available for {ticker}, parameter sweep aborted")
        return None
        
    # Prepare results storage
    results = []
    
    # Generate all parameter combinations
    import itertools
    param_names = list(param_grid.keys())
    param_values = list(param_grid.values())
    
    for params in itertools.product(*param_values):
        param_dict = dict(zip(param_names, params))
        
        # Create strategy with these parameters
        strategy = MACrossoverStrategy(**param_dict)
        
        # Run backtest
        backtester = Backtester(strategy)
        backtest_results = backtester.run(df)
        
        if backtest_results:
            # Extract key metrics
            result = {
                'ticker': ticker,
                **param_dict,
                'total_return': backtest_results['metrics']['total_return'],
                'cagr': backtest_results['metrics']['cagr'],
                'max_drawdown': backtest_results['metrics']['max_drawdown'],
                'sharpe_ratio': backtest_results['metrics']['sharpe_ratio'],
                'win_rate': backtest_results['metrics']['win_rate'],
                'trades': backtest_results['metrics']['trades']
            }
            
            results.append(result)
            
            logger.info(f"Completed backtest with parameters: {param_dict}")
            logger.info(f"Sharpe: {result['sharpe_ratio']:.2f}, CAGR: {result['cagr']:.2f}, Win Rate: {result['win_rate']:.2f}")
    
    # Convert to DataFrame and sort by Sharpe ratio
    if results:
        results_df = pd.DataFrame(results)
        results_df = results_df.sort_values('sharpe_ratio', ascending=False)
        
        # Save results
        results_file = RESULTS_DIR / f"param_sweep_{ticker}_{start_date}_{end_date}.csv"
        results_df.to_csv(results_file, index=False)
        logger.info(f"Saved parameter sweep results to {results_file}")
        
        return results_df
    else:
        logger.warning("No valid results found in parameter sweep")
        return None


def main():
    """Parse arguments and run backtest."""
    parser = argparse.ArgumentParser(description="Backtest trading strategies")
    
    parser.add_argument("--ticker", default="SPY", help="Stock ticker symbol")
    parser.add_argument("--start-date", default="2015-01-01", help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end-date", default=None, help="End date (YYYY-MM-DD), defaults to today")
    parser.add_argument("--interval", default="1d", choices=["1d", "1wk", "1mo"], help="Data interval")
    parser.add_argument("--strategy", default="ma_crossover", choices=["ma_crossover", "bollinger_bands"], 
                        help="Trading strategy to backtest")
    parser.add_argument("--days", type=int, default=365, help="Days to backtest (alternative to start-date)")
    
    # MA Crossover parameters
    parser.add_argument("--fast-ma", type=int, default=50, help="Fast MA period")
    parser.add_argument("--slow-ma", type=int, default=200, help="Slow MA period")
    
    # Bollinger Bands parameters
    parser.add_argument("--bb-length", type=int, default=20, help="Bollinger Bands period")
    parser.add_argument("--bb-std", type=float, default=2.0, help="Bollinger Bands std deviations")
    parser.add_argument("--bb-breakout", action="store_true", help="Use breakout strategy (default is mean reversion)")
    
    # Shared parameters
    parser.add_argument("--rsi-period", type=int, default=14, help="RSI period")
    parser.add_argument("--rsi-overbought", type=int, default=70, help="RSI overbought threshold")
    parser.add_argument("--rsi-oversold", type=int, default=30, help="RSI oversold threshold")
    
    parser.add_argument("--param-sweep", action="store_true", help="Run parameter sweep")
    
    args = parser.parse_args()
    
    # Set end date to today if not specified
    if args.end_date is None:
        args.end_date = datetime.now().strftime('%Y-%m-%d')
    
    # Use days parameter if provided
    if args.days and args.start_date == "2015-01-01":  # Only override if start_date is still the default
        start_datetime = datetime.strptime(args.end_date, "%Y-%m-%d") - timedelta(days=args.days)
        args.start_date = start_datetime.strftime("%Y-%m-%d")
    
    if args.param_sweep:
        # Define parameter grid based on strategy
        if args.strategy == "ma_crossover":
            param_grid = {
                'fast_ma': [20, 50, 100],
                'slow_ma': [100, 200, 300],
                'rsi_period': [9, 14, 21],
                'rsi_overbought': [70, 75, 80],
                'rsi_oversold': [20, 25, 30]
            }
        else:  # Bollinger Bands
            param_grid = {
                'bb_length': [10, 20, 30],
                'bb_std': [1.5, 2.0, 2.5],
                'rsi_period': [9, 14, 21],
                'rsi_overbought': [70, 75, 80],
                'rsi_oversold': [20, 25, 30]
            }
        
        # Run parameter sweep
        parameter_sweep(args.ticker, param_grid, args.start_date, args.end_date, args.interval, args.strategy)
    else:
        # Create strategy with specified parameters
        strategy = MACrossoverStrategy(
            fast_ma=args.fast_ma,
            slow_ma=args.slow_ma,
            rsi_period=args.rsi_period,
            rsi_overbought=args.rsi_overbought,
            rsi_oversold=args.rsi_oversold
        )
        
        # Run backtest
        run_backtest(args.ticker, strategy, args.start_date, args.end_date, args.interval)


if __name__ == "__main__":
    main()
