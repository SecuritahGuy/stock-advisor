# Stock Advisor

A Python-based stock advisor application that fetches real-time market data, calculates technical indicators, generates trading signals, and manages portfolio simulations.

## Features

- Fetches 1-minute stock data from Yahoo Finance
- Resamples data to custom intervals for analysis (5, 10, 15, or 30 min)
- Calculates technical indicators (RSI, Moving Averages, Bollinger Bands, MACD, Stochastic Oscillator, ATR, OBV, VWAP, ADX)
- Implements multiple trading strategies:
  - MA crossovers with RSI filters
  - Bollinger Bands mean reversion and breakout strategies
  - MACD + Stochastic momentum strategy
- Tracks portfolio performance and simulated trades
- Provides reporting and alerts via CLI dashboard
- Includes specialized testing and backtesting functionality
- Supports Docker deployment with environment variable configuration

## Project Structure

```
stock-advisor/
├─ app/                # Python packages
│   ├─ data/           # acquisition & storage layer
│   ├─ indicators/     # technical indicators logic
│   ├─ strategy/       # trading strategy implementations
│   ├─ portfolio/      # portfolio tracking and management
│   └─ report/         # reporting and alerts functionality
├─ data/               # Local data storage
├─ results/            # Backtest results
└─ tests/              # unit tests
```

## Installation

### Option 1: Local Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/stock-advisor.git
cd stock-advisor

# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows, use: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# If you encounter issues with pandas_ta, use this specific numpy version
# pip install numpy==1.24.3

# Set up environment variables
cp .env.example .env
# Edit .env with your preferred settings and email credentials
```

### Option 2: Docker Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/stock-advisor.git
cd stock-advisor

# Set up environment variables
cp .env.example .env
# Edit .env with your preferred settings and email credentials

# Build and start the Docker container
docker-compose up -d
```

## Environment Variables

The application can be configured using environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `TICKERS` | Comma-separated list of stock symbols | SPY,AAPL,MSFT,GOOGL,AMZN |
| `LOG_LEVEL` | Logging level | INFO |
| `DATA_RETENTION_DAYS` | Days of historical data to retain | 30 |
| `EMAIL_ENABLED` | Enable email notifications | False |
| `SMTP_SERVER` | SMTP server for email | smtp.gmail.com |
| `SMTP_PORT` | SMTP port | 587 |
| `EMAIL_USER` | Email username/address | None |
| `EMAIL_PASSWORD` | Email password or app password | None |
| `EMAIL_RECIPIENTS` | Comma-separated list of recipients | None |

You can set these in the `.env` file or pass them as environment variables when running with Docker.

```bash
# Running with Docker and environment variables
docker run -e TICKERS=SPY,QQQ,AAPL -e DATA_RETENTION_DAYS=60 stock-advisor
```

## Usage

### Data Fetcher

Start the data fetcher to collect stock data:

```bash
# Run the fetcher in the background (refreshes every 10 minutes)
python run_fetcher.py

# Run the fetcher once for testing
python run_fetcher.py --once

# Run with custom tickers
python run_fetcher.py --tickers AAPL MSFT GOOG

# Run with custom interval (5, 10, 15, 30 mins)
python run_fetcher.py --interval 5

# Clean up old data (keeping 30 days by default)
python run_fetcher.py --clean

# Clean up and keep only 15 days of data
python run_fetcher.py --clean --keep-days 15
```

### Advisor Dashboard

Run the advisor dashboard to see portfolio status and signals:

```bash
# Run the advisor dashboard in the background
python advisor.py

# Run once without scheduling
python advisor.py --once

# Send a daily summary email now
python advisor.py --daily-summary

# Use a different trading strategy
python advisor.py --strategy bollinger_bands

# Run with custom ticker list
python advisor.py --tickers SPY QQQ IWM AAPL
```

### Portfolio Management

Manage your portfolio with the trade utility:

```bash
# Buy shares
python trade.py buy --ticker AAPL --qty 10 --price 150.00

# Sell shares
python trade.py sell --ticker AAPL --price 160.00

# List current positions
python trade.py list

# View transaction history
python trade.py transactions
```

### Backtesting

Backtest your strategies with historical data:

```bash
# Run a backtest with default parameters
python backtest.py --ticker SPY

# Customize strategy parameters
python backtest.py --ticker AAPL --start-date 2020-01-01 --end-date 2023-12-31 --fast-ma 50 --slow-ma 200 --rsi-period 14

# Run a parameter sweep to find optimal settings
python backtest.py --ticker SPY --param-sweep
```

### Strategy Testing

Test specific trading strategies on historical data:

```bash
# Test the Bollinger Bands strategy on AAPL
python test_bbands.py AAPL

# Use different parameters
python test_bbands.py SPY --bb-length 30 --rsi-period 10

# Test the breakout strategy instead of mean reversion
python test_bbands.py MSFT --breakout

# Test with a different time interval
python test_bbands.py GOOGL --interval 1h --days 30

# Run without showing the plot
python test_bbands.py AMZN --no-plot

# Test the MACD + Stochastic strategy on AAPL
python test_macd_stoch.py AAPL

# Use different MACD parameters
python test_macd_stoch.py SPY --macd-fast 8 --macd-slow 21 --macd-signal 9

# Use different Stochastic parameters
python test_macd_stoch.py MSFT --stoch-k 9 --stoch-d 5 --stoch-oversold 25

# Test with a different time interval and period
python test_macd_stoch.py GOOGL --interval 1h --days 90
```

You can also backtest full strategies using the backtesting module:

```bash
# Backtest the MA Crossover strategy
python backtest.py --ticker AAPL --strategy ma_crossover

# Backtest the Bollinger Bands strategy 
python backtest.py --ticker SPY --strategy bollinger_bands --days 60

# Backtest the MACD + Stochastic strategy
python backtest.py --ticker MSFT --strategy macd_stochastic --days 90
```

## Configuring Email Notifications

To enable email notifications:

1. Edit the `.env` file with your SMTP server settings
2. For Gmail, you'll need to create an "App Password" in your Google Account settings
3. Test the email functionality with `python advisor.py --daily-summary`

## Development

This project follows a phased development approach:

1. **Data Acquisition**: Fetch and store market data
2. **Indicator Engine**: Calculate technical indicators
3. **Strategy Module**: Implement trading rules
4. **Portfolio Tracker**: Track positions and performance
5. **Reporting & Alerts**: Provide actionable insights
6. **Backtesting**: Validate strategies with historical data

## Extending the Project

Here are some ideas for extending the project:

- Add more technical indicators (Bollinger Bands, MACD, etc.)
- Implement additional trading strategies
- Create a web interface with Flask or Streamlit
- Add real-time market data with websockets
- Integrate with a brokerage API for automated trading
- Implement machine learning for predictive analytics

## Disclaimer

This software is for educational and informational purposes only. It is not intended to be financial advice. Always do your own research and consult with a professional financial advisor before making investment decisions.

## License

MIT
