"""
Test module for stock discovery functionality
"""
import unittest
import pandas as pd
from unittest.mock import patch, MagicMock
from app.screener.discover import find_candidates, save_candidates, get_candidates, update_tickers_env

class TestStockDiscovery(unittest.TestCase):
    """Test suite for stock discovery module"""
    
    @patch('app.screener.discover.finviz_available', True)  # Mock finviz availability
    @patch('finvizfinance.screener.overview.Overview')
    def test_find_candidates(self, mock_overview):
        """Test finding stock candidates with a mock screener"""
        # Setup mock
        mock_instance = mock_overview.return_value
        mock_instance.screener_view.return_value = pd.DataFrame({
            'Ticker': ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'TSLA', 'NVDA', 'NFLX', 'PYPL', 'INTC'],
            'Company': ['Apple Inc.', 'Microsoft Corp', 'Alphabet Inc.', 'Amazon', 'Meta', 'Tesla', 'Nvidia', 'Netflix', 'PayPal', 'Intel'],
            'Sector': ['Technology'] * 10,
            'Price': [150.0, 250.0, 120.0, 140.0, 180.0, 200.0, 220.0, 170.0, 90.0, 110.0],
            'Market Cap': ['2.5T', '2.0T', '1.5T', '1.4T', '1.2T', '1.0T', '0.9T', '0.8T', '0.7T', '0.6T']
        })
        
        # Call function
        result = find_candidates(strategy="oversold_reversals", limit=10)
        
        # Assertions
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 10)
        self.assertTrue('discovered_at' in result.columns)
        self.assertTrue('strategy' in result.columns)
        
        # Verify mock was called
        mock_overview.assert_called_once()
        
    @patch('app.screener.discover.finviz_available', True)  # Mock finviz availability
    @patch('finvizfinance.screener.overview.Overview')
    def test_find_candidates_with_custom_price(self, mock_overview):
        """Test finding stock candidates with custom price range"""
        # Setup mock
        mock_instance = mock_overview.return_value
        mock_instance.screener_view.return_value = pd.DataFrame({
            'Ticker': ['AAPL', 'MSFT'],
            'Price': [150.0, 250.0]
        })
        
        # Call function with custom price range
        result = find_candidates(min_price=100, max_price=300)
        
        # Assertions
        self.assertIsNotNone(result)
        
        # Verify mock was called
        mock_overview.assert_called_once()
        
        # Verify correct filters were set
        mock_set_filter = mock_instance.set_filter
        self.assertTrue(mock_set_filter.called)
        
        # Get the filter args from the calls
        call_args_list = mock_set_filter.call_args_list
        found_price_filter = False
        for call in call_args_list:
            if 'filters_dict' in call[1]:
                filters = call[1]['filters_dict']
                if 'price' in filters and filters['price'] == '100to300':
                    found_price_filter = True
                    break
        
        self.assertTrue(found_price_filter, "Price filter '100to300' was not set")
        
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
        
        # Create a dataframe with properly formatted datetime
        test_df = pd.DataFrame({
            'Ticker': ['AAPL', 'MSFT', 'GOOGL'],
            'Price': [150.0, 250.0, 120.0],
            'Market Cap': ['2.5T', '2.0T', '1.5T'],
            'discovered_at': [pd.Timestamp.now()] * 3
        })
        mock_read_parquet.return_value = test_df
        
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
