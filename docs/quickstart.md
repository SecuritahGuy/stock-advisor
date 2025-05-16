# Quick Start Guide

This guide will help you get up and running with Stock Advisor in minutes.

## Prerequisites

- Python 3.8+ installed on your system
- Git for cloning the repository
- Optional: Docker for containerized deployment

## 30-Second Setup

```bash
git clone https://github.com/yourusername/stock-advisor.git
cd stock-advisor
make quickstart   # ⏳ installs deps, fetches last hour, prints dashboard once
```

## Running Live

To continuously poll for data and update the dashboard:

```bash
make live         # polls every 10 min (INTERVAL_MINUTES env var)
```

## Manual Mode

For more granular control:

```bash
# Fetch data once
make fetch

# Run dashboard once
make advisor
```

## Next Steps

- [Configure your environment variables](../README.md#environment-variables)
- [Learn about trading strategies](./strategies.md)
- [Run backtests on historical data](./backtesting.md)
