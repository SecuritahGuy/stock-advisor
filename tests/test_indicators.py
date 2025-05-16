"""
Unit tests for technical indicators.
"""
import unittest
import pandas as pd
import numpy as np
from app.indicators.tech import add_rsi, add_moving_averages, add_bollinger_bands, calculate_all_indicators


class TestTechnicalIndicators(unittest.TestCase):
    """Test suite for technical indicators."""
    
    def setUp(self):
        """Set up test data."""
        # Create test data with a trending price
        self.dates = pd.date_range(start='2023-01-01', periods=250, freq='D')
        self.df = pd.DataFrame({
            'Date': self.dates,
            'Open': [100 + i * 0.1 for i in range(250)],
            'High': [101 + i * 0.1 for i in range(250)],
            'Low': [99 + i * 0.1 for i in range(250)],
            'Close': [100.5 + i * 0.1 for i in range(250)],
            'Volume': [1000 + i * 10 for i in range(250)]
        })
    
    def test_rsi_calculation(self):
        """Test RSI calculation."""
        result = add_rsi(self.df, length=14)
        
        # Check column exists
        self.assertIn('rsi14', result.columns)
        
        # Check if RSI is within 0-100 range
        rsi_values = result['rsi14'].dropna()
        self.assertTrue(all(0 <= val <= 100 for val in rsi_values))
        
        # Check correct number of NaN values at beginning
        expected_nan_count = 14  # RSI needs at least 'length' periods
        actual_nan_count = result['rsi14'].isna().sum()
        self.assertGreaterEqual(actual_nan_count, expected_nan_count)
    
    def test_moving_averages(self):
        """Test Moving Averages calculation."""
        ma_lengths = [50, 200]
        result = add_moving_averages(self.df, lengths=ma_lengths)
        
        # Check columns exist
        for length in ma_lengths:
            column_name = f'ma{length}'
            self.assertIn(column_name, result.columns)
            
            # Check correct number of NaN values at beginning
            expected_nan_count = length - 1
            actual_nan_count = result[column_name].isna().sum()
            self.assertEqual(actual_nan_count, expected_nan_count)
            
            # Check if MA is calculated correctly for a simple case
            # MA should be average of the last 'length' prices
            if length < len(self.df):
                # tests/test_indicators.py  (inside TestTechnicalIndicators.test_moving_averages)

                for i in range(length - 1, len(self.df)):
                    # window **including** the current row
                    expected_ma = self.df['Close'].iloc[i - length + 1 : i + 1].mean()
                    actual_ma   = result[column_name].iloc[i]

                    self.assertAlmostEqual(actual_ma, expected_ma, places=4)

            
    def test_bollinger_bands(self):
        """Test Bollinger Bands calculation."""
        length = 20
        std = 2
        result = add_bollinger_bands(self.df, length=length, std=std)
        
        # Check columns exist
        expected_columns = [f'bb_lower_{length}', f'bb_middle_{length}', f'bb_upper_{length}']
        for column in expected_columns:
            self.assertIn(column, result.columns)
        
        # Check correct number of NaN values at beginning
        expected_nan_count = length - 1
        for column in expected_columns:
            actual_nan_count = result[column].isna().sum()
            self.assertEqual(actual_nan_count, expected_nan_count)
        
        # Check relationships between bands
        non_nan_idx = ~result[f'bb_middle_{length}'].isna()
        self.assertTrue(all(result[f'bb_lower_{length}'][non_nan_idx] < result[f'bb_middle_{length}'][non_nan_idx]))
        self.assertTrue(all(result[f'bb_middle_{length}'][non_nan_idx] < result[f'bb_upper_{length}'][non_nan_idx]))
        
        # Check middle band is equal to SMA
        middle_band = result[f'bb_middle_{length}']
        sma_df = add_moving_averages(self.df, lengths=[length])
        sma = sma_df[f'ma{length}']
        # Instead of comparing Series directly, use numpy.isclose for floating point comparison
        import numpy as np
        non_nan_indices = ~middle_band.isna() & ~sma.isna()
        self.assertTrue(np.allclose(
            middle_band[non_nan_indices].values, 
            sma[non_nan_indices].values,
            rtol=1e-5, atol=1e-5
        ))
    
    def test_nan_handling(self):
        """Test handling of NaN values."""
        # Create DataFrame with NaN values
        df_with_nans = self.df.copy()
        df_with_nans.loc[10:20, 'Close'] = np.nan
        
        # Calculate indicators
        result = calculate_all_indicators(df_with_nans)
        
        # Check if function completes without errors
        self.assertIsNotNone(result)
        
        # RSI should have NaNs where Close is NaN and in the window after
        self.assertTrue(result['rsi14'].isna().sum() > df_with_nans['Close'].isna().sum())
    
    def test_all_indicators(self):
        """Test calculating all indicators at once."""
        result = calculate_all_indicators(self.df)
        
        # Check if all expected columns are present
        expected_columns = ['rsi14', 'ma50', 'ma200', 
                            'bb_lower_20', 'bb_middle_20', 'bb_upper_20',
                            'macd', 'macd_signal', 'macd_hist']
        
        for column in expected_columns:
            self.assertIn(column, result.columns)


if __name__ == '__main__':
    unittest.main()
