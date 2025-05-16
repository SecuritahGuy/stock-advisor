"""
Script to debug moving average calculation in detail.
"""
import pandas as pd
import numpy as np

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

length = 50
i = length  # Index to check

# Manual calculation as done in test
expected_ma = df['Close'].iloc[i-length:i].mean()
print(f"\nTest calculation at index {i}:")
print(f"Range used: {i-length}:{i} (exclusive of i)")
print(f"First value in range: {df['Close'].iloc[i-length]}")
print(f"Last value in range: {df['Close'].iloc[i-1]}")
print(f"Expected MA: {expected_ma}")

# Rolling calculation (pandas default)
rolling_ma = df['Close'].rolling(window=length).mean().iloc[i]
print(f"\nRolling calculation at index {i}:")
print(f"Rolling MA: {rolling_ma}")
print(f"Difference: {rolling_ma - expected_ma}")

# Print the calculated values using both methods
print("\nValues at index 50 using both methods:")
print(f"Test expected_ma = {df['Close'].iloc[0:50].mean()}")
print(f"pandas rolling_ma = {df['Close'].iloc[1:51].mean()}")

# Fix with offset
fixed_ma = df['Close'].shift(1).rolling(window=length).mean()
print(f"\nFixed calculation with shift(1):")
print(f"Fixed MA at index {i}: {fixed_ma.iloc[i]}")
print(f"Fixed MA == Expected MA: {fixed_ma.iloc[i] == expected_ma}")
