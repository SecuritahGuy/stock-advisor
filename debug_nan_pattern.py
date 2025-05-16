"""
Let's analyze the exact pattern of NaNs expected in the tests.
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

# Analysis for Moving Averages
print("MOVING AVERAGES ANALYSIS")
print("-----------------------")

for length in [20, 50]:
    print(f"\nAnalyzing MA with length={length}")
    
    # Create a series with NaNs in the first length-1 positions
    series = pd.Series(index=df.index)
    for i in range(length-1, len(df)):
        series.iloc[i] = df['Close'].iloc[i-(length-1):i+1].mean()
    
    # Check the NaN count
    nan_count = series.isna().sum()
    print(f"NaN count: {nan_count} (expected: {length-1})")
    
    # Check the first non-NaN value
    first_valid_index = series.first_valid_index()
    print(f"First valid index: {first_valid_index}")
    first_valid_value = series.loc[first_valid_index]
    print(f"First valid value: {first_valid_value}")
    
    # Calculate using the correct range
    correct_range = df['Close'].iloc[0:length].mean()
    print(f"Mean of values 0 to {length-1}: {correct_range}")
    
    # Show some sample calculations
    index_to_check = length - 1  # This should be the first non-NaN index
    values_used = df['Close'].iloc[index_to_check-(length-1):index_to_check+1]
    print(f"Values used for index {index_to_check}: {values_used.values}")
    expected_ma = values_used.mean()
    print(f"Expected MA at index {index_to_check}: {expected_ma}")

# Check the exact calculations in the test function
print("\n\nTEST FUNCTION ANALYSIS")
print("---------------------")

length = 50
i = length  # As used in test loop

# Test expected value
expected_ma = df['Close'].iloc[i-length:i].mean()
print(f"Test expected_ma at i={i}: {expected_ma}")
print(f"Values used: df['Close'].iloc[{i-length}:{i}]")
print(f"Range: {i-length} to {i-1}")

# Current implementation
result = pd.Series(index=df.index)
for j in range(length, len(df)):
    result.iloc[j] = df['Close'].iloc[j-length:j].mean()

print(f"\nNaN count in current implementation: {result.isna().sum()}")
print(f"First valid index: {result.first_valid_index()}")
print(f"First valid value: {result[result.first_valid_index()]}")

# Alternative implementation that should match test expectation
result2 = pd.Series(index=df.index)
# Set first length-1 values to NaN explicitly
result2.iloc[:length-1] = np.nan
# Calculate values starting from index length-1
for j in range(length-1, len(df)):
    result2.iloc[j] = df['Close'].iloc[j-(length-1):j+1].mean()

print(f"\nNaN count in fixed implementation: {result2.isna().sum()}")
print(f"First valid index: {result2.first_valid_index()}")
print(f"First valid value: {result2[result2.first_valid_index()]}")
