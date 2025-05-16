# Backtesting Guide

Stock Advisor provides robust backtesting capabilities to evaluate trading strategies against historical data. This guide explains how to use these tools effectively.

## Basic Backtesting

To backtest a strategy with default parameters:

```bash
python backtest.py --ticker SPY
```

This will run the default MA Crossover strategy on SPY data for the past 90 days.

## Customizing Backtests

### Time Period

```bash
python backtest.py --ticker AAPL --start-date 2024-01-01 --end-date 2025-04-30
```

### Strategy Selection

```bash
# Bollinger Bands strategy
python backtest.py --ticker SPY --strategy bollinger_bands

# MACD + Stochastic strategy
python backtest.py --ticker MSFT --strategy macd_stochastic
```

### Strategy Parameters

```bash
# Customize MA Crossover parameters
python backtest.py --ticker AAPL --fast-ma 50 --slow-ma 200 --rsi-period 14

# Customize MACD + Stochastic parameters
python backtest.py --ticker SPY --strategy macd_stochastic --macd-fast 8 --macd-slow 21 --stoch-k 9
```

## Parameter Optimization

Run a parameter sweep to find optimal settings:

```bash
python backtest.py --ticker SPY --param-sweep
```

This will test various combinations of parameters and report the best performing setup.

## Understanding Backtest Results

Backtest results include:

- **Equity Curve**: Visual representation of portfolio value over time
- **Trade Log**: Detailed record of each trade with entry/exit prices and reasons
- **Performance Metrics**:
  - **Total Return**: Overall percentage return
  - **CAGR**: Compound Annual Growth Rate
  - **Sharpe Ratio**: Risk-adjusted return measure
  - **Maximum Drawdown**: Largest peak-to-trough decline
  - **Win Rate**: Percentage of profitable trades
  - **Profit Factor**: Gross profits divided by gross losses
  - **Average Trade**: Average profit/loss per trade

Results are saved to the `results/` directory in both JSON and image formats.

## Comparing to Benchmarks

To compare strategy performance against a benchmark:

```bash
python backtest.py --ticker AAPL --benchmark SPY
```

This will show your strategy's performance alongside the benchmark for comparison.

## Common Issues and Solutions

### Limited Historical Data

If you get warnings about limited historical data:

```bash
python run_fetcher.py --ticker SPY --days 365
```

This will fetch a full year of data before running backtests.

### Survivorship Bias

Be aware that backtests only use currently available tickers, which can introduce survivorship bias. For more realistic results, consider testing against a broad market ETF like SPY.

### Look-Ahead Bias

Stock Advisor's backtesting engine carefully prevents look-ahead bias by ensuring signals are only generated based on data that would have been available at that point in time.
