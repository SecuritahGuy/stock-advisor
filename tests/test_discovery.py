"""
Test module for stock discovery functionality
"""
import unittest
import pandas as pd
import datetime
from unittest.mock import patch, MagicMock
from app.screener.discover import find_candidates, save_candidates, get_candidates, update_tickers_env

class TestStockDiscovery(unittest.TestCase):
    """Test suite for stock discovery module"""
    
    # We need to patch at a deeper level for these tests to work correctly
    @patch('app.screener.discover.finviz_available', True)
    @patch('app.screener.discover.Screener')
    def test_find_candidates(self, MockScreener, mock_finviz_available):
        """Test finding stock candidates with a mock screener"""
        # Create a mock instance
        mock_instance = MagicMock()
        MockScreener.return_value = mock_instance
        
        # Setup mock data
        mock_data = pd.DataFrame({
            'Ticker': ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'TSLA', 'NVDA', 'NFLX', 'PYPL', 'INTC'],
            'Company': ['Apple Inc.', 'Microsoft Corp', 'Alphabet Inc.', 'Amazon', 'Meta', 'Tesla', 'Nvidia', 'Netflix', 'PayPal', 'Intel'],
            'Sector': ['Technology'] * 10,
            'Price': [150.0, 250.0, 120.0, 140.0, 180.0, 200.0, 220.0, 170.0, 90.0, 110.0],
            'Market Cap': ['2.5T', '2.0T', '1.5T', '1.4T', '1.2T', '1.0T', '0.9T', '0.8T', '0.7T', '0.6T']
        })
        mock_instance.screener_view.return_value = mock_data
        
        # Call function
        result = find_candidates(strategy="oversold_reversals", limit=10)
        
        # Assertions
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 10)
        self.assertTrue('discovered_at' in result.columns)
        self.assertTrue('strategy' in result.columns)
        
        # Verify mock was called
        MockScreener.assert_called_once()
        
    @patch('app.screener.discover.finviz_available', True)
    @patch('app.screener.discover.Screener')
    def test_find_candidates_with_custom_price(self, MockScreener, mock_finviz_available):
        """Test finding stock candidates with custom price range"""
        # Create a mock instance
        mock_instance = MagicMock()
        MockScreener.return_value = mock_instance
        
        # Setup mock data
        mock_data = pd.DataFrame({
            'Ticker': ['AAPL', 'MSFT'],
            'Price': [150.0, 250.0]
        })
        mock_instance.screener_view.return_value = mock_data
        
        # Call function with custom price range
        result = find_candidates(min_price=100, max_price=300)
        
        # Assertions
        self.assertIsNotNone(result)
        
        # Verify mock was called
        MockScreener.assert_called_once()
        
        # Verify correct filters were set
        mock_set_filter = mock_instance.set_filter
        self.assertTrue(mock_set_filter.called)
        
        # Check filter calls
        # Get the filter args from any calls
        call_args_list = mock_set_filter.call_args_list
        if call_args_list:
            filters_used = {}
            for call in call_args_list:
                if call[1] and 'filters_dict' in call[1]:
                    filters_used = call[1]['filters_dict']
                    break
            
            self.assertIn('price', filters_used, "Price filter was not set")
            self.assertEqual(filters_used['price'], '100to300', "Incorrect price filter set")
        
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
        
    @patch('app.screener.discover.CANDIDATES_FILE')
    @patch('pandas.read_parquet')
    def test_get_candidates(self, mock_read_parquet, mock_file):
        """Test getting candidates from parquet file"""
        # Setup mocks
        mock_file_exists = MagicMock(return_value=True)
        mock_file.exists = mock_file_exists  # Make the file appear to exist
        
        # Use a fixed timestamp that's guaranteed to be within the time window
        now = datetime.datetime.now(datetime.timezone.utc)
        three_days_ago = now - datetime.timedelta(days=3)
        
        # Create a dataframe with properly formatted datetime
        test_df = pd.DataFrame({
            'Ticker': ['AAPL', 'MSFT', 'GOOGL'],
            'Price': [150.0, 250.0, 120.0],
            'Market Cap': ['2.5T', '2.0T', '1.5T'],
            'discovered_at': [three_days_ago, three_days_ago, three_days_ago],
            'MarketCapMillions': [2500000, 2000000, 1500000]  # Add this directly to skip conversion
        })
        mock_read_parquet.return_value = test_df
        
        # Call function with a time window that includes our timestamps
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
