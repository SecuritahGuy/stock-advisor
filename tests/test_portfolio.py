"""
Unit tests for portfolio tracking.
"""
import unittest
import os
import tempfile
import shutil
import pandas as pd
from datetime import datetime
from app.portfolio.portfolio import Portfolio


class TestPortfolio(unittest.TestCase):
    """Test suite for portfolio tracking."""
    
    def setUp(self):
        """Set up test environment."""
        # Create a temporary directory for the database
        self.test_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.test_dir, "test_portfolio.db")
        
        # Initialize test portfolio
        self.portfolio = Portfolio("test_portfolio", db_path=self.db_path)
    
    def tearDown(self):
        """Clean up test environment."""
        # Remove the test directory
        shutil.rmtree(self.test_dir)
    
    def test_add_position(self):
        """Test adding a position."""
        # Add a test position
        position_id = self.portfolio.add_position(
            ticker="AAPL",
            shares=10,
            price=150.0,
            timestamp=datetime.now(),
            notes="Test position"
        )
        
        # Check if position was added
        self.assertIsNotNone(position_id)
        self.assertGreater(position_id, 0)
        
        # Check if position can be retrieved
        positions = self.portfolio.get_positions()
        self.assertEqual(len(positions), 1)
        self.assertEqual(positions.iloc[0]['ticker'], "AAPL")
        self.assertEqual(positions.iloc[0]['shares'], 10)
        self.assertEqual(positions.iloc[0]['cost_basis'], 150.0)
    
    def test_close_position(self):
        """Test closing a position."""
        # Add a test position
        position_id = self.portfolio.add_position(
            ticker="MSFT",
            shares=5,
            price=250.0
        )
        
        # Close the position
        result = self.portfolio.close_position(
            position_id=position_id,
            price=260.0
        )
        
        # Check if position was closed
        self.assertTrue(result)
        
        # Check if position is no longer in open positions
        positions = self.portfolio.get_positions()
        self.assertTrue(positions.empty)
        
        # Check if transaction was recorded
        transactions = self.portfolio.get_transactions()
        self.assertEqual(len(transactions), 2)  # Buy and sell
        
        # Verify the second transaction is a sell
        sells = transactions[transactions['action'] == 'SELL']
        self.assertEqual(len(sells), 1)
        self.assertEqual(sells.iloc[0]['ticker'], "MSFT")
        self.assertEqual(sells.iloc[0]['shares'], 5)
        self.assertEqual(sells.iloc[0]['price'], 260.0)
    
    def test_update_position(self):
        """Test updating a position."""
        # Add a test position
        position_id = self.portfolio.add_position(
            ticker="GOOGL",
            shares=2,
            price=1000.0
        )
        
        # Update the position
        result = self.portfolio.update_position(
            position_id=position_id,
            shares=3,
            cost_basis=1100.0,
            notes="Updated position"
        )
        
        # Check if position was updated
        self.assertTrue(result)
        
        # Check updated values
        positions = self.portfolio.get_positions()
        self.assertEqual(positions.iloc[0]['shares'], 3)
        self.assertEqual(positions.iloc[0]['cost_basis'], 1100.0)
        self.assertEqual(positions.iloc[0]['notes'], "Updated position")
    
    def test_get_position_by_ticker(self):
        """Test retrieving a position by ticker."""
        # Add a test position
        self.portfolio.add_position(
            ticker="AMZN",
            shares=1,
            price=2000.0
        )
        
        # Get position by ticker
        position = self.portfolio.get_position_by_ticker("AMZN")
        
        # Check if position was retrieved
        self.assertFalse(position.empty)
        self.assertEqual(position.iloc[0]['ticker'], "AMZN")
        self.assertEqual(position.iloc[0]['shares'], 1)
        self.assertEqual(position.iloc[0]['cost_basis'], 2000.0)
        
        # Try getting a non-existent position
        non_existent = self.portfolio.get_position_by_ticker("NONEXISTENT")
        self.assertTrue(non_existent.empty)
    
    def test_calculate_current_value(self):
        """Test portfolio valuation calculation."""
        # Add test positions
        self.portfolio.add_position(ticker="AAPL", shares=10, price=150.0)
        self.portfolio.add_position(ticker="MSFT", shares=5, price=250.0)
        
        # Set up price data
        price_data = {
            "AAPL": 155.0,
            "MSFT": 260.0
        }
        
        # Calculate valuation
        valuation = self.portfolio.calculate_current_value(price_data)
        
        # Check valuation
        expected_total_cost = 10 * 150.0 + 5 * 250.0  # 2750.0
        expected_total_value = 10 * 155.0 + 5 * 260.0  # 2850.0
        expected_total_pl = expected_total_value - expected_total_cost  # 100.0
        expected_total_pl_pct = (expected_total_pl / expected_total_cost) * 100  # ~3.636%
        
        self.assertAlmostEqual(valuation['total_cost'], expected_total_cost)
        self.assertAlmostEqual(valuation['total_value'], expected_total_value)
        self.assertAlmostEqual(valuation['total_pl'], expected_total_pl)
        self.assertAlmostEqual(valuation['total_pl_pct'], expected_total_pl_pct)
        
        # Check individual positions
        aapl_position = next(p for p in valuation['positions'] if p['ticker'] == 'AAPL')
        msft_position = next(p for p in valuation['positions'] if p['ticker'] == 'MSFT')
        
        self.assertEqual(aapl_position['shares'], 10)
        self.assertEqual(aapl_position['cost_basis'], 150.0)
        self.assertEqual(aapl_position['current_price'], 155.0)
        self.assertEqual(aapl_position['current_value'], 10 * 155.0)
        self.assertEqual(aapl_position['pl'], 10 * (155.0 - 150.0))
        
        self.assertEqual(msft_position['shares'], 5)
        self.assertEqual(msft_position['cost_basis'], 250.0)
        self.assertEqual(msft_position['current_price'], 260.0)
        self.assertEqual(msft_position['current_value'], 5 * 260.0)
        self.assertEqual(msft_position['pl'], 5 * (260.0 - 250.0))


if __name__ == '__main__':
    unittest.main()
