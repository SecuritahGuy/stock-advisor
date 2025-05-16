"""
Test module for stock discovery functionality
"""
import unittest
import pandas as pd
from unittest.mock import patch, MagicMock
from app.screener.discover import find_candidates, save_candidates, get_candidates, update_tickers_env

class TestStockDiscovery(unittest.TestCase):
    """Test suite for stock discovery module"""
    
    @patch('app.screener.discover.Screener')
    def test_find_candidates(self, mock_screener):
        """Test finding stock candidates with a mock screener"""
        # Setup mock
        mock_instance = MagicMock()
        mock_instance.to_df.return_value = pd.DataFrame({
            'Ticker': ['AAPL', 'MSFT', 'GOOGL'],
            'Company': ['Apple Inc.', 'Microsoft Corp', 'Alphabet Inc.'],
            'Sector': ['Technology'] * 3,
            'Price': [150.0, 250.0, 120.0],
            'Market Cap': ['2.5T', '2.0T', '1.5T']
        })
        mock_screener.return_value = mock_instance
        
        # Call function
        result = find_candidates(strategy="oversold_reversals", limit=10)
        
        # Assertions
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 3)
        self.assertTrue('discovered_at' in result.columns)
        self.assertTrue('strategy' in result.columns)
        
        # Verify mock was called with correct filters
        mock_screener.assert_called_once()
        
    @patch('app.screener.discover.Screener')
    def test_find_candidates_with_custom_price(self, mock_screener):
        """Test finding stock candidates with custom price range"""
        # Setup mock
        mock_instance = MagicMock()
        mock_instance.to_df.return_value = pd.DataFrame({
            'Ticker': ['AAPL', 'MSFT'],
            'Price': [150.0, 250.0]
        })
        mock_screener.return_value = mock_instance
        
        # Call function with custom price range
        result = find_candidates(min_price=100, max_price=300)
        
        # Assertions
        self.assertIsNotNone(result)
        # Verify filter included custom price range
        call_args = mock_screener.call_args[1]
        self.assertEqual(call_args['filters']['price'], '100to300')
        
    @patch('pandas.DataFrame.to_parquet')
    def test_save_candidates(self, mock_to_parquet):
        """Test saving candidates to parquet file"""
        # Create test dataframe
        df = pd.DataFrame({
            'Ticker': ['AAPL', 'MSFT', 'GOOGL'],
            'Price': [150.0, 250.0, 120.0],
            'discovered_at': [pd.Timestamp.now()] * 3
        })
        
        # Call function
        result = save_candidates(df, append=False)
        
        # Assertions
        self.assertTrue(result)
        mock_to_parquet.assert_called_once()
        
    @patch('pandas.read_parquet')
    def test_get_candidates(self, mock_read_parquet):
        """Test getting candidates from parquet file"""
        # Setup mock
        mock_read_parquet.return_value = pd.DataFrame({
            'Ticker': ['AAPL', 'MSFT', 'GOOGL'],
            'Price': [150.0, 250.0, 120.0],
            'Market Cap': ['2.5T', '2.0T', '1.5T'],
            'discovered_at': [pd.Timestamp.now()] * 3
        })
        
        # Call function
        result = get_candidates(days=7, top_n=2)
        
        # Assertions
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 2)  # Limited to top 2
        
    @patch('builtins.open', new_callable=unittest.mock.mock_open, read_data='LOG_LEVEL=INFO\n')
    @patch('pathlib.Path.exists')
    def test_update_tickers_env(self, mock_exists, mock_open):
        """Test updating tickers in .env file"""
        # Setup mocks
        mock_exists.return_value = True
        
        # Create test dataframe
        df = pd.DataFrame({
            'Ticker': ['PLTR', 'SNOW', 'U'],
            'Price': [10.0, 15.0, 20.0]
        })
        
        # Call function
        result = update_tickers_env(df, max_tickers=5)
        
        # Assertions
        self.assertTrue(result)
        mock_open.assert_called()
        
if __name__ == '__main__':
    unittest.main()
