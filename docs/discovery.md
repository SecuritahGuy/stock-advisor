# Stock Discovery

This document explains how to use the stock discovery module to find new trading candidates for your watchlist.

## Overview

The discovery module uses technical and fundamental filters to find stocks that match specific criteria aligned with the trading strategies in Stock Advisor. It helps automate the process of finding new trading opportunities.

## Available Strategies

Stock Advisor includes three pre-defined screening strategies:

1. **Oversold Reversals**: Finds stocks that have temporarily pulled back in an overall uptrend. These are candidates for a bounce trade.

2. **Fresh Momentum**: Identifies stocks showing strong upward momentum that are near their 52-week highs. These stocks may trigger MA crossover signals soon.

3. **Quality Value**: Discovers fundamentally sound companies trading at reasonable valuations to provide a balance of growth and value.

## Using the Discovery Tool

### Basic Usage

```bash
# Find oversold stocks (default strategy)
python discover.py

# Find momentum stocks
python discover.py --strategy fresh_momentum

# Find quality value stocks
python discover.py --strategy quality_value

# List recently discovered candidates
python discover.py --list

# List only top 10 candidates by market cap
python discover.py --list --top 10

# List candidates from the last 7 days
python discover.py --list --days 7
```

### Updating Your Watchlist

The discovery tool can automatically update your `TICKERS` environment variable with new candidates:

```bash
# Find candidates and add them to your watchlist
python discover.py --update-env

# Limit the total number of tickers in your watchlist
python discover.py --update-env --max-tickers 20

# Only add stocks above a certain market cap
python discover.py --update-env --min-market-cap 1000  # $1B+ market cap
```

### Customizing Filters

You can customize the price range for discovered stocks:

```bash
# Find stocks between $20 and $100
python discover.py --min-price 20 --max-price 100
```

## Scheduling Stock Discovery

For regular discovery runs, add the following to your cron jobs:

```
# Run discovery every morning at 9 AM ET (adjust for your timezone)
0 9 * * 1-5 cd /path/to/stock-advisor && python discover.py --update-env
```

Or use the Makefile command:

```bash
# Run the discovery process
make discover
```

## How It Works

1. The discovery tool connects to FinViz's stock screener via the `finvizfinance` package
2. It applies pre-defined filters based on the selected strategy
3. Results are saved to `data/candidates.parquet` for historical tracking
4. New candidates can be automatically added to your watchlist

## Extending with Custom Strategies

You can extend the `STRATEGIES` dictionary in `app/screener/discover.py` with your own custom screening strategies. See the existing implementations for examples of how to structure the filter dictionary.

The filters follow FinViz's syntax. For a complete reference of available filters, visit [FinViz's screener page](https://finviz.com/screener.ashx).
