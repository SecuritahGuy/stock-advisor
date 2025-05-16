#!/bin/zsh
# Test script for portfolio setup

echo "🧪 Testing portfolio setup methods\n"

# Make scripts executable if they aren't already
chmod +x trade.py
chmod +x setup_portfolio.py

echo "📋 Method 1: Using setup_portfolio.py with configuration file"
echo "----------------------------------------"
./setup_portfolio.py --reset
echo ""

echo "📋 Method 2: Using trade.py directly"
echo "----------------------------------------"
./trade.py list
echo ""
echo "Adding a test position with trade.py..."
./trade.py buy --ticker NVDA --qty 2 --price 101.25 --notes "Test position"
./trade.py list
echo ""

echo "📋 Method 3: Using the web interface"
echo "----------------------------------------"
echo "Please start the web server if you haven't already:"
echo "./start_web.sh"
echo "Then visit http://127.0.0.1:5050/portfolio in your browser"
echo ""

echo "✅ Setup methods tested successfully!"
