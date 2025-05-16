#!/usr/bin/env python
"""
Setup script for initializing portfolio from a configuration file.
This allows for a quick setup of an initial portfolio with multiple positions.
"""
import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path

from app.portfolio.portfolio import Portfolio

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("portfolio_setup.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("portfolio_setup")


def load_portfolio_config(config_path):
    """
    Load portfolio configuration from a JSON file.
    
    Args:
        config_path (str): Path to the config file
        
    Returns:
        dict: Parsed configuration data
    """
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        return config
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing config file: {str(e)}")
        return None
    except FileNotFoundError:
        logger.error(f"Config file not found: {config_path}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error loading config: {str(e)}")
        return None


def setup_portfolio(config):
    """
    Set up portfolio based on configuration data.
    
    Args:
        config (dict): Portfolio configuration data
        
    Returns:
        bool: True if successful, False otherwise
    """
    if not config or 'positions' not in config:
        logger.error("Invalid config format or missing positions")
        return False
    
    # Get portfolio name from config or use default
    portfolio_name = config.get('portfolio_name', 'default')
    portfolio = Portfolio(portfolio_name)
    
    # Process each position
    positions_added = 0
    for pos in config['positions']:
        try:
            # Extract position data
            ticker = pos.get('ticker')
            shares = float(pos.get('shares', 0))
            cost_basis = float(pos.get('cost_basis', 0))
            notes = pos.get('notes', '')
            
            # Parse purchase date if provided
            purchase_date = pos.get('purchase_date')
            if purchase_date:
                try:
                    # Try different date formats
                    for fmt in ['%Y-%m-%d', '%Y-%m-%d %H:%M:%S', '%m/%d/%Y']:
                        try:
                            timestamp = datetime.strptime(purchase_date, fmt)
                            break
                        except ValueError:
                            continue
                    else:
                        # If none of the formats worked
                        logger.warning(f"Could not parse date '{purchase_date}' for {ticker}, using current time")
                        timestamp = datetime.now()
                except Exception:
                    logger.warning(f"Error parsing date for {ticker}, using current time")
                    timestamp = datetime.now()
            else:
                timestamp = datetime.now()
            
            # Validate position data
            if not ticker or shares <= 0 or cost_basis <= 0:
                logger.warning(f"Invalid position data: {pos}")
                continue
            
            # Add position to portfolio
            position_id = portfolio.add_position(
                ticker=ticker,
                shares=shares,
                price=cost_basis,
                timestamp=timestamp,
                notes=notes
            )
            
            if position_id:
                logger.info(f"Added position: {shares} shares of {ticker} at ${cost_basis:.2f} (ID: {position_id})")
                positions_added += 1
            else:
                logger.error(f"Failed to add position for {ticker}")
                
        except Exception as e:
            logger.error(f"Error processing position: {str(e)}")
    
    logger.info(f"Portfolio setup complete. Added {positions_added} positions to portfolio '{portfolio_name}'")
    return positions_added > 0


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description="Set up portfolio from configuration file")
    parser.add_argument("--config", default="portfolio_config.json", 
                        help="Path to portfolio configuration file")
    parser.add_argument("--reset", action="store_true", 
                        help="Reset portfolio first (warning: deletes all existing positions)")
    
    args = parser.parse_args()
    
    # Ensure the config file exists
    config_path = args.config
    if not Path(config_path).exists():
        logger.error(f"Config file not found: {config_path}")
        return 1
    
    # Load configuration
    config = load_portfolio_config(config_path)
    if not config:
        logger.error("Failed to load configuration")
        return 1
    
    # Reset portfolio if requested
    if args.reset:
        # Get portfolio name from config or use default
        portfolio_name = config.get('portfolio_name', 'default')
        portfolio = Portfolio(portfolio_name)
        
        # Confirm reset with user
        confirm = input(f"Are you sure you want to reset portfolio '{portfolio_name}'? This will delete all existing positions. (y/n): ")
        if confirm.lower() == 'y':
            # Use the Portfolio.clear method if it exists, otherwise warn user
            if hasattr(portfolio, 'clear'):
                portfolio.clear()
                logger.info(f"Portfolio '{portfolio_name}' has been reset")
            else:
                logger.warning("Portfolio reset not implemented. Please manually delete positions.")
        else:
            logger.info("Portfolio reset cancelled")
    
    # Set up portfolio
    success = setup_portfolio(config)
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
