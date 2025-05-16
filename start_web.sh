#!/bin/zsh
# Start the Flask web application with virtual environment

# Activate the virtual environment
source .venv/bin/activate

# Install Flask if not installed
pip install flask

# Update portfolio data to ensure current prices
echo "Updating portfolio stock data..."
python update_portfolio_data.py

# Run the Flask app on port 5050 instead of default 5000 (which might be used by AirPlay on macOS)
python run_web.py --debug --port 5050
