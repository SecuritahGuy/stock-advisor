<!-- Use this file to provide workspace-specific custom instructions to Copilot. For more details, visit https://code.visualstudio.com/docs/copilot/copilot-customization#_use-a-githubcopilotinstructionsmd-file -->

# Stock Advisor Project

This is a Python-based stock advisor application that fetches stock data, calculates technical indicators, generates trading signals, and tracks portfolio performance.

## Project Structure

- `app/data/`: Data acquisition and storage layer
- `app/indicators/`: Technical indicators calculation
- `app/strategy/`: Trading strategy implementations
- `app/portfolio/`: Portfolio tracking and management
- `app/report/`: Reporting and alerting functionality
- `tests/`: Unit tests

## Technologies

The project uses:
- `yfinance` for fetching stock data
- `pandas` for data manipulation
- `pandas_ta` for technical indicators
- `apscheduler` for scheduling tasks
- `rich` for CLI formatting
- SQLite or Parquet for data storage

## Development Guidelines

1. Follow PEP 8 style guide for Python code
2. Document functions and classes with docstrings
3. Write unit tests for new functionality
4. Handle errors gracefully with proper logging
5. Include type hints for better code readability

## Key Components

- Data fetching with retry and error handling
- Technical indicator calculation (RSI, Moving Averages)
- Trading strategy implementation (MA crossovers with RSI filters)
- Portfolio tracking with P/L calculation
- CLI dashboard for real-time monitoring
- Backtesting functionality for strategy validation
