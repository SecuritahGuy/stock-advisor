#!/usr/bin/env python
"""
Command-line utility for managing portfolio trades.
"""
import argparse
import logging
from datetime import datetime
from app.portfolio.portfolio import Portfolio

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("trade.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("trade")


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Manage portfolio trades")
    
    # Portfolio selection
    parser.add_argument("--portfolio", default="default", help="Portfolio name")
    
    # Action subcommands
    subparsers = parser.add_subparsers(dest="action", help="Action to perform")
    
    # Buy action
    buy_parser = subparsers.add_parser("buy", help="Buy shares")
    buy_parser.add_argument("--ticker", required=True, help="Stock ticker symbol")
    buy_parser.add_argument("--qty", type=float, required=True, help="Number of shares")
    buy_parser.add_argument("--price", type=float, required=True, help="Price per share")
    buy_parser.add_argument("--date", help="Transaction date (YYYY-MM-DD HH:MM:SS)")
    buy_parser.add_argument("--notes", help="Transaction notes")
    
    # Sell action
    sell_parser = subparsers.add_parser("sell", help="Sell shares")
    sell_parser.add_argument("--id", type=int, help="Position ID")
    sell_parser.add_argument("--ticker", help="Stock ticker symbol (alternative to ID)")
    sell_parser.add_argument("--price", type=float, required=True, help="Price per share")
    sell_parser.add_argument("--date", help="Transaction date (YYYY-MM-DD HH:MM:SS)")
    sell_parser.add_argument("--notes", help="Transaction notes")
    
    # List action
    list_parser = subparsers.add_parser("list", help="List positions")
    
    # Transactions action
    transactions_parser = subparsers.add_parser("transactions", help="List transactions")
    transactions_parser.add_argument("--limit", type=int, default=10, help="Number of transactions to show")
    
    return parser.parse_args()


def execute_buy(args):
    """Execute a buy trade."""
    portfolio = Portfolio(args.portfolio)
    
    # Parse date if provided
    if args.date:
        try:
            timestamp = datetime.strptime(args.date, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            logger.error("Invalid date format. Use YYYY-MM-DD HH:MM:SS")
            return False
    else:
        timestamp = datetime.now()
    
    # Add the position
    position_id = portfolio.add_position(
        ticker=args.ticker,
        shares=args.qty,
        price=args.price,
        timestamp=timestamp,
        notes=args.notes
    )
    
    if position_id:
        print(f"Added position: {args.qty} shares of {args.ticker} at ${args.price:.2f} (ID: {position_id})")
        return True
    else:
        print("Failed to add position")
        return False


def execute_sell(args):
    """Execute a sell trade."""
    portfolio = Portfolio(args.portfolio)
    
    # Parse date if provided
    if args.date:
        try:
            timestamp = datetime.strptime(args.date, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            logger.error("Invalid date format. Use YYYY-MM-DD HH:MM:SS")
            return False
    else:
        timestamp = datetime.now()
    
    # Get position ID if ticker is provided instead of ID
    position_id = args.id
    if not position_id and args.ticker:
        positions = portfolio.get_position_by_ticker(args.ticker)
        if not positions.empty:
            position_id = positions['id'].iloc[0]
        else:
            print(f"No position found for ticker {args.ticker}")
            return False
    
    if not position_id:
        print("Position ID or ticker is required")
        return False
    
    # Close the position
    result = portfolio.close_position(
        position_id=position_id,
        price=args.price,
        timestamp=timestamp,
        notes=args.notes
    )
    
    if result:
        print(f"Closed position ID {position_id} at ${args.price:.2f}")
        return True
    else:
        print(f"Failed to close position ID {position_id}")
        return False


def execute_list(args):
    """List positions in the portfolio."""
    portfolio = Portfolio(args.portfolio)
    positions = portfolio.get_positions()
    
    if positions.empty:
        print(f"No positions in portfolio '{args.portfolio}'")
        return
    
    # Print positions
    print(f"\nPositions in portfolio '{args.portfolio}':")
    print("-" * 80)
    print("{:<5} {:<6} {:<10} {:<12} {:<15} {:<20}".format(
        "ID", "Ticker", "Shares", "Cost Basis", "Total Cost", "Opened At"
    ))
    print("-" * 80)
    
    for _, pos in positions.iterrows():
        total_cost = pos['shares'] * pos['cost_basis']
        print("{:<5} {:<6} {:<10.2f} {:<12.2f} {:<15.2f} {:<20}".format(
            pos['id'], pos['ticker'], pos['shares'], pos['cost_basis'], 
            total_cost, pos['opened_at']
        ))
    
    print("-" * 80)
    print(f"Total Positions: {len(positions)}")


def execute_transactions(args):
    """List transactions in the portfolio."""
    portfolio = Portfolio(args.portfolio)
    transactions = portfolio.get_transactions()
    
    if transactions.empty:
        print(f"No transactions in portfolio '{args.portfolio}'")
        return
    
    # Limit the number of transactions
    transactions = transactions.head(args.limit)
    
    # Print transactions
    print(f"\nTransactions in portfolio '{args.portfolio}' (most recent {args.limit}):")
    print("-" * 90)
    print("{:<5} {:<6} {:<6} {:<10} {:<12} {:<20} {:<20}".format(
        "ID", "Ticker", "Action", "Shares", "Price", "Timestamp", "Notes"
    ))
    print("-" * 90)
    
    for _, tx in transactions.iterrows():
        print("{:<5} {:<6} {:<6} {:<10.2f} {:<12.2f} {:<20} {:<20}".format(
            tx['id'], tx['ticker'], tx['action'], tx['shares'], tx['price'], 
            tx['timestamp'], tx['notes'] if tx['notes'] else ""
        ))
    
    print("-" * 90)


def main():
    """Main function to parse arguments and execute commands."""
    args = parse_args()
    
    if args.action == "buy":
        execute_buy(args)
    elif args.action == "sell":
        execute_sell(args)
    elif args.action == "list":
        execute_list(args)
    elif args.action == "transactions":
        execute_transactions(args)
    else:
        print("Please specify an action: buy, sell, list, or transactions")


if __name__ == "__main__":
    main()
