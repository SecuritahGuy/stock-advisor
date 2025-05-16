"""
Script to check RSI and MA calculations to debug test failures.
"""
import pandas as pd
import pandas_ta as ta
import numpy as np

def debug_rsi():
    """Debug RSI calculation issues."""
    # Create test data with a trending price (same as in test)
    dates = pd.date_range(start='2023-01-01', periods=250, freq='D')
    df = pd.DataFrame({
        'Date': dates,
        'Open': [100 + i * 0.1 for i in range(250)],
        'High': [101 + i * 0.1 for i in range(250)],
        'Low': [99 + i * 0.1 for i in range(250)],
        'Close': [100.5 + i * 0.1 for i in range(250)],
        'Volume': [1000 + i * 10 for i in range(250)]
    })
    
    # Calculate RSI using pandas_ta
    rsi_values = ta.rsi(df['Close'], length=14)
    
    # Print statistics
    print("\nRSI Statistics:")
    print(f"Min: {rsi_values.min()}")
    print(f"Max: {rsi_values.max()}")
    print(f"Any values outside 0-100 range: {any((rsi_values < 0) | (rsi_values > 100))}")
    if any((rsi_values < 0) | (rsi_values > 100)):
        outside_range = rsi_values[(rsi_values < 0) | (rsi_values > 100)]
        print(f"Values outside range: {outside_range.values}")
        print(f"Indices of values outside range: {outside_range.index.tolist()}")

def debug_ma():
    """Debug Moving Average calculation issues."""
    # Create test data with a trending price (same as in test)
    dates = pd.date_range(start='2023-01-01', periods=250, freq='D')
    df = pd.DataFrame({
        'Date': dates,
        'Open': [100 + i * 0.1 for i in range(250)],
        'High': [101 + i * 0.1 for i in range(250)],
        'Low': [99 + i * 0.1 for i in range(250)],
        'Close': [100.5 + i * 0.1 for i in range(250)],
        'Volume': [1000 + i * 10 for i in range(250)]
    })
    
    length = 50  # Just check the MA50
    
    # pandas_ta calculation
    ma_ta = ta.sma(df['Close'], length=length)
    
    # Manual calculation (as done in test)
    i = length  # Just check a specific index
    expected_ma = df['Close'].iloc[i-length:i].mean()
    actual_ma = ma_ta.iloc[i]
    
    print("\nMoving Average Comparison:")
    print(f"pandas_ta MA at index {i}: {actual_ma}")
    print(f"Manual calculation at index {i}: {expected_ma}")
    print(f"Difference: {actual_ma - expected_ma}")
    
    # Check values used in calculation
    print(f"\nValues used in manual calculation:")
    print(df['Close'].iloc[i-length:i].values)
    
    # Calculate arithmetic mean directly for verification
    values = df['Close'].iloc[i-length:i].values
    arithmetic_mean = sum(values) / len(values)
    print(f"Direct arithmetic mean calculation: {arithmetic_mean}")

if __name__ == "__main__":
    debug_rsi()
    debug_ma()
