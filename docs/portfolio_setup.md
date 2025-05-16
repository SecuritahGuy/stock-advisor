# Portfolio Setup Guide

This guide explains how to set up your portfolio in the Stock Advisor application. There are three main ways to manage your portfolio:

1. **Using the configuration file** - Best for initial setup with multiple positions
2. **Using the trade script** - Best for day-to-day management from the command line
3. **Using the web interface** - Best for visual interaction and monitoring

## 1. Using the Configuration File

This is the easiest way to set up your initial portfolio with multiple positions at once.

### Step 1: Edit the Configuration File

Open the `portfolio_config.json` file and update it with your actual portfolio information:

```json
{
    "portfolio_name": "default",
    "positions": [
        {
            "ticker": "AAPL",
            "shares": 10,
            "cost_basis": 175.50,
            "purchase_date": "2025-01-15",
            "notes": "Initial position in Apple"
        },
        {
            "ticker": "TSLA",
            "shares": 5,
            "cost_basis": 212.75,
            "purchase_date": "2025-02-10",
            "notes": "Long-term growth investment"
        }
    ]
}
```

### Step 2: Run the Setup Script

Run the following command to set up your portfolio:

```bash
./setup_portfolio.py
```

Additional options:
- To specify a different configuration file: `./setup_portfolio.py --config my_portfolio.json`
- To reset your portfolio before setting it up: `./setup_portfolio.py --reset`

## 2. Using the Trade Script

The trade script is useful for ongoing management of your portfolio from the command line.

### Adding a New Position

```bash
# Basic usage
./trade.py buy --ticker AAPL --qty 10 --price 175.50

# With additional details
./trade.py buy --ticker GOOG --qty 5 --price 150.25 --date "2025-05-10 10:30:00" --notes "Alphabet position"

# For a different portfolio
./trade.py --portfolio growth buy --ticker AMZN --qty 3 --price 180.75
```

### Selling a Position

```bash
# Sell by position ID
./trade.py sell --id 1 --price 190.25

# Sell by ticker (will sell all shares of that ticker)
./trade.py sell --ticker AAPL --price 190.25
```

### Viewing Your Portfolio

```bash
# List all positions
./trade.py list

# View transaction history
./trade.py transactions --limit 20
```

## 3. Using the Web Interface

The web interface provides a visual way to manage your portfolio.

### Start the Web Server

```bash
./start_web.sh
```

Then visit http://127.0.0.1:5050 in your browser.

### Adding a Position

1. Navigate to the Portfolio page
2. Click the "Add Position" button at the bottom of the page
3. Fill in the required information in the form
4. Click "Add Position" to save

### Monitoring Your Portfolio

The Portfolio page shows:
- Current positions with performance metrics
- Portfolio valuation and returns
- Performance charts

## Backup and Migration

Your portfolio data is stored in a SQLite database in the `data/` directory:
- `data/portfolio.db` - Contains positions and transactions
- `data/valuation.db` - Contains historical valuation data

To backup your portfolio, simply copy these files to a safe location.

## Troubleshooting

If you encounter any issues:

1. Check the log files:
   - `trade.log` - For issues with the trade script
   - `portfolio_setup.log` - For issues with the setup script
   - `advisor.log` - For general application issues

2. Make sure your data directory exists and is writable:
   ```bash
   mkdir -p data
   chmod 755 data
   ```

3. Ensure you have the correct permissions to run the scripts:
   ```bash
   chmod +x trade.py setup_portfolio.py start_web.sh
   ```
