![CI](https://github.com/yourusername/stock-advisor/actions/workflows/python-tests.yml/badge.svg)
![Coverage](https://coveralls.io/repos/github/yourusername/stock-advisor/badge.svg)
![Dependabot](https://img.shields.io/badge/dependabot-enabled-brightgreen.svg)
![Contributors](https://img.shields.io/github/contributors/yourusername/stock-advisor.svg)

# Stock Advisor

For Python hobbyists who want disciplined, back-tested trade ideas in < 3 min.

A Python-based stock advisor application that fetches real-time market data, calculates technical indicators, generates trading signals, and manages portfolio simulations.

## Features

- Fetches stock data from Yahoo Finance
- Resamples data to default **10-minute** intervals (configurable via `INTERVAL_MINUTES` env var: 1–30 min)
- Calculates technical indicators (RSI, Moving Averages, Bollinger Bands, MACD, Stochastic Oscillator)
- Implements multiple trading strategies:
  - MA crossovers with RSI filters
  - Bollinger Bands mean reversion and breakout strategies
  - MACD + Stochastic momentum strategy
- Tracks portfolio performance and simulated trades
- Provides reporting and alerts via CLI dashboard
- **Web Dashboard**: Interactive Flask-based UI for portfolio management and visualization
- **Portfolio Management**: Configuration-based setup and position management
- **Discovery engine**: Daily screener auto-adds oversold or breakout candidates to watch-list
- Includes specialized testing and backtesting functionality
- Supports Docker deployment with environment variable configuration

## Architecture

```
┌───────────────┐     ┌───────────────┐     ┌───────────────┐
│ Yahoo Finance │────>│  Data Fetcher │────>│    Storage    │
└───────────────┘     └───────────────┘     │SQLite/Parquet │
                                            └───────┬───────┘
                                                    │
                                                    ▼
┌───────────┐      ┌───────────────┐      ┌────────────┐
│ Indicators│<─────│ Strategy      │─────>│  Signals   │
│ RSI, MA.. │─────>│ Engine        │      │ Buy/Sell   │
└───────────┘      └───────────────┘      └──────┬─────┘
                                                 │
                                                 ▼
                    ┌───────────────┐      ┌────────────┐
                    │ Portfolio     │<─────│  Reports   │
                    │ Ledger        │─────>│ Dashboard  │
                    └───────┬───────┘      └────────────┘
                            │
                            ▼
                    ┌───────────────┐
                    │  Backtesting  │
                    │  Validation   │
                    └───────────────┘
```

[View full architecture diagram](./assets/architecture.svg)

## Quick Start (30 sec)

```bash
git clone https://github.com/yourusername/stock-advisor.git && \
cd stock-advisor && \
make quickstart   # ⏳ installs deps, fetches last hour, prints dashboard once
```

*Need a live feed?*

```bash
make live         # polls every 10 min (INTERVAL_MINUTES env var)
```

## Makefile Commands

```bash
make fetch        # fetches data according to DATA_RETENTION_DAYS and INTERVAL_MINUTES
make advisor      # runs advisor dashboard once (--once)
make live         # live APScheduler loop with default 10-min interval
make test         # run tests and lint
make docker-up    # build and start Docker container
make discover     # run stock screener and find candidates
make discover-update # run screener and update watch-list
```

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

Choose your setup path:

| Environment | Requirements | Setup Command | Use Case |
|-------------|--------------|---------------|----------|
| **Local**   | Python 3.8–3.12 | `python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt` | Development |
| **Docker**  | Docker, Docker Compose | `cp .env.example .env && docker-compose up -d` | Production |
| **Codespaces** | GitHub Codespaces | Open in Codespaces | Quick testing |

*Tip: Run `make quickstart` after setup to fetch data and run the dashboard.*

## Environment Variables

The application can be configured using environment variables:

| Variable | Description | Default |
|----------|-------------|---------|

The application can be configured using environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `TICKERS` | Comma-separated list of stock symbols | SPY,AAPL,MSFT,GOOGL,AMZN |
| `LOG_LEVEL` | Logging level | INFO |
| `DATA_RETENTION_DAYS` | Days of historical data to retain | 30 |
| `INTERVAL_MINUTES` | Polling interval in minutes (1–30) | 10 |
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

## Secrets

**Never commit `.env` to git.** Use GitHub Secrets or a `.secrets/` file in Docker.
The application loads environment variables via dotenv; see `.env.example` for reference.

<!-- Added Secrets section to highlight secrets management -->

## Documentation

- [Quick Start Guide](./docs/quickstart.md)
- [Trading Strategies](./docs/strategies.md)
- [Backtesting Guide](./docs/backtesting.md)
- [Portfolio Setup Guide](./docs/portfolio_setup.md)
- [Stock Discovery](./docs/discovery.md)
- [Project Roadmap](./docs/roadmap.md)

## Usage Examples

<details>
<summary>Data Fetcher Examples</summary>

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
```
</details>

<details>
<summary>Advisor Dashboard Examples</summary>

```bash
# Run the advisor dashboard in the background
python advisor.py

# Run once without scheduling
python advisor.py --once

# Send a daily summary email now
python advisor.py --daily-summary

# Use a different trading strategy
python advisor.py --strategy bollinger_bands
```
</details>

<details>
<summary>Web Dashboard Examples</summary>

```bash
# Start the web dashboard
./start_web.sh

# Access the dashboard in your browser
# Visit: http://127.0.0.1:5050

# Initialize your portfolio using the configuration file
./setup_portfolio.py

# Test portfolio setup methods
./test_portfolio_setup.sh
```
</details>

<details>
<summary>Portfolio Management Examples</summary>

```bash
# Initialize portfolio from configuration file
./setup_portfolio.py

# Configure with a custom config file
./setup_portfolio.py --config my_portfolio.json

# Reset portfolio first, then set up
./setup_portfolio.py --reset

# Buy shares manually
python trade.py buy --ticker AAPL --qty 10 --price 150.00

# Sell shares
python trade.py sell --ticker AAPL --price 160.00

# List current positions
python trade.py list

# View transaction history
python trade.py transactions
```
</details>

<details>
<summary>Backtesting Examples</summary>

```bash
# Run a backtest with default parameters
python backtest.py --ticker SPY

# Customize strategy parameters
python backtest.py --ticker AAPL --start-date 2020-01-01 --end-date 2023-12-31 --fast-ma 50 --slow-ma 200 --rsi-period 14

# Run a parameter sweep to find optimal settings
python backtest.py --ticker SPY --param-sweep
```
</details>

<details>
<summary>Strategy Testing Examples</summary>

```bash
# Test the Bollinger Bands strategy on AAPL
python test_bbands.py AAPL

# Test the MACD + Stochastic strategy on SPY
python test_macd_stoch.py SPY --macd-fast 8 --macd-slow 21 --macd-signal 9

# Backtest the MA Crossover strategy
python backtest.py --ticker AAPL --strategy ma_crossover
```
</details>

## Scheduling

| Mode        | Command                                                    | Use Case        |
| ----------- | ---------------------------------------------------------- | --------------- |
| Manual      | `make fetch && make advisor`                               | One-off test    |
| APScheduler | `make live`                                                | Dev desktop     |
| System Cron | `*/10 14-21 * * 1-5 /usr/bin/python .../advisor.py`        | VPS / always-on |

*APScheduler auto-pauses outside US market hours; adjust in `config/market_hours.py`.*

<!-- Added Scheduling section for clarity on execution modes -->

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

### Web Dashboard Implementation

A Flask-based web dashboard has been implemented to enhance user experience and provide visual insights:

- **Interactive Portfolio Management**: View and manage portfolio positions with performance metrics
- **Trading Signals Visualization**: Monitor buy/sell signals with detailed information
- **Stock Discovery Interface**: Explore potential investment candidates through the web interface
- **Chart View**: Visualize stock performance and technical indicators for each ticker
- **Mobile-Responsive Design**: Access the dashboard from any device with a responsive layout

### Portfolio Management Enhancements

Portfolio management has been significantly improved with new features:

- **Configuration-Based Setup**: Easily initialize your portfolio using JSON configuration
- **Web Form Integration**: Add positions through an intuitive web interface
- **Performance Metrics**: Track portfolio valuation, returns, volatility, and Sharpe ratio
- **Position Management**: View detailed position-level metrics and performance
- **Comprehensive Documentation**: Detailed guides for portfolio setup and management

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

- **Web Dashboard Enhancements**: Add more interactive features and visualization options
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

As of May 2025, the project has successfully implemented three main trading strategies with comprehensive backtesting capabilities. We've recently added a Flask-based web dashboard for interactive portfolio management and visualization, with mobile-responsive design and integrated stock discovery.

The portfolio management system has been enhanced with configuration-based setup, web form integration, and comprehensive documentation. We've also improved the MACD + Stochastic strategy to work reliably with limited historical data and fixed technical issues with indicator calculations.

The backtesting module now provides detailed performance metrics including CAGR, Sharpe ratio, maximum drawdown, win rate, and profit factor. We've also developed specialized debugging tools to help visualize and understand strategy behavior.

Next steps include enhancing the web interface with more interactive features, implementing parameter optimization, and exploring machine learning integration. Community contributions are welcome, especially in these planned improvement areas.

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
