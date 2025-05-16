# Stock Advisor

A Python-based stock advisor application that fetches real-time market data, calculates technical indicators, generates trading signals, and manages portfolio simulations.

## Features

- Fetches 1-minute stock data from Yahoo Finance
- Resamples data to custom intervals for analysis (5, 10, 15, or 30 min)
- Calculates technical indicators (RSI, Moving Averages, Bollinger Bands, MACD, Stochastic Oscillator, ATR, OBV, VWAP, ADX)
- Implements multiple trading strategies:
  - MA crossovers with RSI filters
  - Bollinger Bands mean reversion and breakout strategies
  - MACD + Stochastic momentum strategy with enhanced backtesting capabilities
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
├─ debug_*.py          # Debugging scripts
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

# Test with different oversold/overbought thresholds
python test_macd_stoch.py AAPL --stoch-oversold 30 --stoch-overbought 70
```

You can also backtest full strategies using the backtesting module:

```bash
# Backtest the MA Crossover strategy
python backtest.py --ticker AAPL --strategy ma_crossover

# Backtest the Bollinger Bands strategy 
python backtest.py --ticker SPY --strategy bollinger_bands --days 60

# Backtest the MACD + Stochastic strategy
python backtest.py --ticker MSFT --strategy macd_stochastic --days 90

# Debugging strategy behavior
python debug_macd_stoch.py --ticker SPY
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

## Recent Improvements

### MACD + Stochastic Strategy Enhancements

The MACD + Stochastic strategy has been significantly improved to work better with limited historical data:

- **Adaptive Signal Generation**: The strategy now adjusts its signal generation logic based on the size of the available dataset
- **Improved Backtesting**: Enhanced to generate reliable signals even with small datasets by implementing initial position logic
- **Better Error Handling**: Added robust fallback calculations for technical indicators when primary methods fail
- **Debugging Tools**: New debugging script (`debug_macd_stoch.py`) for visualizing indicator calculations and signal generation
- **Flexible Parameters**: Additional configuration options for fine-tuning strategy behavior

### Technical Infrastructure Improvements

- **Bollinger Bands Calculation**: Added fallback manual calculation when pandas_ta encounters errors
- **Compatible Dependencies**: Updated requirements to ensure numpy and pandas-ta work correctly together
- **Enhanced Logging**: More detailed logging to track indicator calculation and strategy behavior
- **Performance Metrics**: Additional metrics for evaluating strategy performance in backtests

## Future Improvements and Roadmap

### Short-term Improvements (Next 1-3 Months)

- **Web Dashboard**: Create a Flask or Streamlit-based web interface for easier monitoring of signals and portfolio performance
- **Parameter Optimization**: Implement grid search and genetic algorithms for automated strategy optimization
- **Portfolio Optimization**: Add portfolio allocation recommendations based on risk-adjusted returns
- **Indicator Combination Analysis**: Investigate which indicator combinations perform best across different market conditions
- **Custom Alert Rules**: Allow users to define complex conditional alerts based on multiple indicators

### Medium-term Enhancements (3-6 Months)

- **Machine Learning Integration**: Implement ML models to identify patterns and predict price movements
- **Real-time Data Integration**: Connect to websocket APIs for real-time market data instead of periodic polling
- **Market Sentiment Analysis**: Incorporate news sentiment and social media analysis to enhance trading signals
- **Automated Trading**: Add integration with brokerage APIs for automated execution of trading signals
- **Multi-timeframe Analysis**: Enhance strategies to consider signals across multiple timeframes
- **Risk Management Module**: Develop more sophisticated position sizing and risk management rules

### Long-term Vision (6+ Months)

- **Deep Learning Models**: Implement advanced deep learning models (LSTM, Transformers) for price prediction
- **Alternative Data Sources**: Integrate alternative data like options flow, dark pool activity, and institutional positioning
- **Crypto Market Support**: Extend functionality to cryptocurrency markets with exchange API integrations
- **Community Features**: Create a platform for users to share and collaborate on strategy development
- **Mobile Application**: Develop a companion mobile app for alerts and monitoring on the go
- **Strategy Marketplace**: Build a marketplace where users can subscribe to or purchase proven strategies

### Technical Debt and Infrastructure

- **Testing Coverage**: Increase unit test and integration test coverage to at least 80%
- **Documentation**: Create comprehensive API documentation and extensive code examples
- **Performance Optimization**: Refactor critical path code for improved execution speed
- **Data Storage Solutions**: Migrate to more scalable storage solutions for larger datasets
- **Containerization**: Improve Docker configurations for easier deployment across environments

## Current Project Status

As of May 2025, the project has successfully implemented three main trading strategies with comprehensive backtesting capabilities. The recent focus has been on improving the MACD + Stochastic strategy to work reliably with limited historical data and fixing technical issues with indicator calculations.

The backtesting module now provides detailed performance metrics including CAGR, Sharpe ratio, maximum drawdown, win rate, and profit factor. We've also developed specialized debugging tools to help visualize and understand strategy behavior.

Next steps include web interface development, parameter optimization, and machine learning integration. Community contributions are welcome, especially in these planned improvement areas.

## Contributing

Contributions to the Stock Advisor project are welcome! Here's how you can help:

1. **Bug Reports**: If you find a bug, please create an issue with detailed reproduction steps
2. **Feature Requests**: Suggest new features through the issues section
3. **Code Contributions**: 
   - Fork the repository
   - Create a feature branch (`git checkout -b feature/amazing-feature`)
   - Commit your changes (`git commit -m 'Add some amazing feature'`)
   - Push to the branch (`git push origin feature/amazing-feature`)
   - Open a Pull Request

Please ensure your code follows the project's style guidelines and includes appropriate tests.

## Disclaimer

This software is for educational and informational purposes only. It is not intended to be financial advice. Always do your own research and consult with a professional financial advisor before making investment decisions.

## License

MIT
