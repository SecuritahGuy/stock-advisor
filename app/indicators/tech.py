"""
Technical indicators calculation module.
"""
import pandas as pd
import pandas_ta as ta
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("tech_indicators")


def add_rsi(df, length=14, column='Close'):
    """
    Add Relative Strength Index (RSI) to DataFrame.
    
    Args:
        df (pd.DataFrame): DataFrame with price data
        length (int): Period for RSI calculation
        column (str): Column name to use for calculation
        
    Returns:
        pd.DataFrame: DataFrame with RSI column added
    """
    try:
        logger.info(f"Calculating RSI{length} on {column}")
        df[f'rsi{length}'] = ta.rsi(df[column], length=length)
        return df
    except Exception as e:
        logger.error(f"Error calculating RSI: {str(e)}")
        return df


def add_moving_averages(df, lengths=[50, 200], column='Close'):
    """
    Add Simple Moving Averages (SMA) to DataFrame.
    
    Args:
        df (pd.DataFrame): DataFrame with price data
        lengths (list): List of periods for MA calculations
        column (str): Column name to use for calculation
        
    Returns:
        pd.DataFrame: DataFrame with MA columns added
    """
    try:
        for length in lengths:
            logger.info(f"Calculating MA{length} on {column}")
            df[f'ma{length}'] = ta.sma(df[column], length=length)
        return df
    except Exception as e:
        logger.error(f"Error calculating Moving Averages: {str(e)}")
        return df


def add_exponential_moving_averages(df, lengths=[9, 20, 50], column='Close'):
    """
    Add Exponential Moving Averages (EMA) to DataFrame.
    
    Args:
        df (pd.DataFrame): DataFrame with price data
        lengths (list): List of periods for EMA calculations
        column (str): Column name to use for calculation
        
    Returns:
        pd.DataFrame: DataFrame with EMA columns added
    """
    try:
        for length in lengths:
            logger.info(f"Calculating EMA{length} on {column}")
            df[f'ema{length}'] = ta.ema(df[column], length=length)
        return df
    except Exception as e:
        logger.error(f"Error calculating Exponential Moving Averages: {str(e)}")
        return df


def add_bollinger_bands(df, length=20, std=2, column='Close'):
    """
    Add Bollinger Bands to DataFrame.
    
    Args:
        df (pd.DataFrame): DataFrame with price data
        length (int): Period for Bollinger Bands calculation
        std (float): Number of standard deviations
        column (str): Column name to use for calculation
        
    Returns:
        pd.DataFrame: DataFrame with Bollinger Bands columns added
    """
    try:
        logger.info(f"Calculating Bollinger Bands({length}, {std}) on {column}")
        bbands = ta.bbands(df[column], length=length, std=std)
        
        # Rename columns to a simpler format
        bbands.columns = [f'bb_lower_{length}', f'bb_middle_{length}', f'bb_upper_{length}']
        
        # Join with original DataFrame
        df = df.join(bbands)
        return df
    except Exception as e:
        logger.error(f"Error calculating Bollinger Bands: {str(e)}")
        return df


def add_macd(df, fast=12, slow=26, signal=9, column='Close'):
    """
    Add Moving Average Convergence Divergence (MACD) to DataFrame.
    
    Args:
        df (pd.DataFrame): DataFrame with price data
        fast (int): Fast period
        slow (int): Slow period
        signal (int): Signal period
        column (str): Column name to use for calculation
        
    Returns:
        pd.DataFrame: DataFrame with MACD columns added
    """
    try:
        logger.info(f"Calculating MACD({fast},{slow},{signal}) on {column}")
        macd = ta.macd(df[column], fast=fast, slow=slow, signal=signal)
        
        # Rename columns to a simpler format
        macd.columns = ['macd', 'macd_signal', 'macd_hist']
        
        # Join with original DataFrame
        df = df.join(macd)
        return df
    except Exception as e:
        logger.error(f"Error calculating MACD: {str(e)}")
        return df


def add_atr(df, length=14, column_close='Close', column_high='High', column_low='Low'):
    """
    Add Average True Range (ATR) to DataFrame.
    
    Args:
        df (pd.DataFrame): DataFrame with price data
        length (int): Period for ATR calculation
        column_close (str): Column name for close prices
        column_high (str): Column name for high prices
        column_low (str): Column name for low prices
        
    Returns:
        pd.DataFrame: DataFrame with ATR column added
    """
    try:
        logger.info(f"Calculating ATR({length})")
        df[f'atr{length}'] = ta.atr(df[column_high], df[column_low], df[column_close], length=length)
        return df
    except Exception as e:
        logger.error(f"Error calculating ATR: {str(e)}")
        return df


def add_stochastic(df, k_period=14, d_period=3, column_close='Close', column_high='High', column_low='Low'):
    """
    Add Stochastic Oscillator to DataFrame.
    
    Args:
        df (pd.DataFrame): DataFrame with price data
        k_period (int): K period for stochastic calculation
        d_period (int): D period for stochastic calculation
        column_close (str): Column name for close prices
        column_high (str): Column name for high prices
        column_low (str): Column name for low prices
        
    Returns:
        pd.DataFrame: DataFrame with Stochastic columns added
    """
    try:
        logger.info(f"Calculating Stochastic({k_period},{d_period})")
        stoch = ta.stoch(df[column_high], df[column_low], df[column_close], k=k_period, d=d_period)
        
        # Rename columns to a simpler format
        stoch.columns = ['stoch_k', 'stoch_d']
        
        # Join with original DataFrame
        df = df.join(stoch)
        return df
    except Exception as e:
        logger.error(f"Error calculating Stochastic: {str(e)}")
        return df


def add_obv(df):
    """
    Add On-Balance Volume (OBV) to DataFrame.
    
    Args:
        df (pd.DataFrame): DataFrame with price and volume data
        
    Returns:
        pd.DataFrame: DataFrame with OBV column added
    """
    try:
        logger.info("Calculating On-Balance Volume (OBV)")
        df['obv'] = ta.obv(df['Close'], df['Volume'])
        return df
    except Exception as e:
        logger.error(f"Error calculating OBV: {str(e)}")
        return df


def add_parabolic_sar(df, acceleration=0.02, maximum=0.2):
    """
    Add Parabolic SAR to DataFrame.
    
    Args:
        df (pd.DataFrame): DataFrame with OHLC price data
        acceleration (float): Acceleration factor
        maximum (float): Maximum acceleration
        
    Returns:
        pd.DataFrame: DataFrame with Parabolic SAR column added
    """
    try:
        logger.info(f"Calculating Parabolic SAR({acceleration},{maximum})")
        df['psar'] = ta.psar(df['High'], df['Low'], af=acceleration, max_af=maximum)['PSARl_0.02_0.2']
        return df
    except Exception as e:
        logger.error(f"Error calculating Parabolic SAR: {str(e)}")
        return df


def add_vwap(df):
    """
    Add Volume Weighted Average Price (VWAP) to DataFrame.
    
    Args:
        df (pd.DataFrame): DataFrame with OHLCV price data
        
    Returns:
        pd.DataFrame: DataFrame with VWAP column added
    """
    try:
        logger.info("Calculating VWAP")
        # Check if we have the necessary columns
        if all(col in df.columns for col in ['Open', 'High', 'Low', 'Close', 'Volume']):
            # VWAP requires intraday data (timestamp with time component)
            # Check if we have a timestamp column with time component
            time_col = None
            for col in ['Datetime', 'Date']:
                if col in df.columns:
                    time_col = col
                    break
            
            if time_col:
                # Make a copy to avoid modifying original DataFrame
                df_vwap = df.copy()
                
                # Add a date column if using Datetime to group by date
                if time_col == 'Datetime' and isinstance(df_vwap[time_col].iloc[0], pd.Timestamp):
                    df_vwap['date'] = df_vwap[time_col].dt.date
                    group_col = 'date'
                else:
                    group_col = time_col
                    
                # Calculate VWAP by day
                df_vwap['vwap'] = 0.0
                
                for date, group in df_vwap.groupby(group_col):
                    # Calculate Typical Price
                    typical_price = (group['High'] + group['Low'] + group['Close']) / 3
                    
                    # Calculate VWAP
                    cumulative_tp_vol = (typical_price * group['Volume']).cumsum()
                    cumulative_vol = group['Volume'].cumsum()
                    
                    group_vwap = cumulative_tp_vol / cumulative_vol
                    
                    # Assign back to df_vwap
                    df_vwap.loc[group.index, 'vwap'] = group_vwap.values
                
                # Assign vwap back to original DataFrame
                df['vwap'] = df_vwap['vwap']
            else:
                logger.warning("No timestamp column found, VWAP calculation requires intraday data")
        else:
            logger.warning("Missing required columns for VWAP calculation")
        return df
    except Exception as e:
        logger.error(f"Error calculating VWAP: {str(e)}")
        return df


def add_adx(df, length=14, column_close='Close', column_high='High', column_low='Low'):
    """
    Add Average Directional Index (ADX) to DataFrame.
    
    Args:
        df (pd.DataFrame): DataFrame with price data
        length (int): Period for ADX calculation
        column_close (str): Column name for close prices
        column_high (str): Column name for high prices
        column_low (str): Column name for low prices
        
    Returns:
        pd.DataFrame: DataFrame with ADX columns added
    """
    try:
        logger.info(f"Calculating ADX({length})")
        adx = ta.adx(df[column_high], df[column_low], df[column_close], length=length)
        
        # Rename columns to a simpler format
        adx.columns = ['adx', 'dmp', 'dmn']
        
        # Join with original DataFrame
        df = df.join(adx)
        return df
    except Exception as e:
        logger.error(f"Error calculating ADX: {str(e)}")
        return df


def calculate_all_indicators(df):
    """
    Calculate all technical indicators for a DataFrame.
    
    Args:
        df (pd.DataFrame): DataFrame with OHLCV data
        
    Returns:
        pd.DataFrame: DataFrame with all indicators added
    """
    logger.info("Calculating all technical indicators")
    
    # Make a copy to avoid modifying the original
    result = df.copy()
    
    # Add RSI
    result = add_rsi(result, length=14)
    
    # Add Moving Averages
    result = add_moving_averages(result, lengths=[50, 200])
    
    # Add Exponential Moving Averages
    result = add_exponential_moving_averages(result, lengths=[9, 20, 50])
    
    # Add Bollinger Bands
    result = add_bollinger_bands(result)
    
    # Add MACD
    result = add_macd(result)
    
    # Add ADX
    result = add_adx(result)
    
    # Add Stochastic Oscillator
    result = add_stochastic(result)
    
    # Add ATR
    result = add_atr(result)
    
    # Add OBV
    result = add_obv(result)
    
    # Add Parabolic SAR
    result = add_parabolic_sar(result)
    
    # Add VWAP
    result = add_vwap(result)
    
    logger.info("Technical indicators calculation complete")
    return result


def update_indicators(df, existing_df=None):
    """
    Update indicators for new data, reusing existing calculations to avoid recalculating the entire dataset.
    
    Args:
        df (pd.DataFrame): New data to calculate indicators for
        existing_df (pd.DataFrame): Existing data with indicators already calculated
        
    Returns:
        pd.DataFrame: DataFrame with updated indicators
    """
    if existing_df is None or existing_df.empty:
        return calculate_all_indicators(df)
        
    try:
        logger.info("Updating indicators for new data")
        
        # Identify the timestamp of the most recent data in existing_df
        if 'Datetime' in existing_df.columns:
            last_timestamp = existing_df['Datetime'].max()
            time_column = 'Datetime'
        elif 'Date' in existing_df.columns:
            last_timestamp = existing_df['Date'].max()
            time_column = 'Date'
        else:
            logger.warning("No timestamp column found in existing data, recalculating all indicators")
            return calculate_all_indicators(df)
            
        # Filter new data to only include rows after the last timestamp in existing_df
        new_data = df[df[time_column] > last_timestamp]
        
        if new_data.empty:
            logger.info("No new data to update indicators for")
            return existing_df
            
        # Combine datasets for calculation continuity
        # We need some historical data for accurate indicator calculation
        # For a 200-period MA, we need at least 200 periods of data
        combined_data = pd.concat([existing_df, new_data]).sort_values(by=time_column)
        
        # Calculate indicators on the combined data
        updated_data = calculate_all_indicators(combined_data)
        
        # Return only the newly calculated rows
        return updated_data
        
    except Exception as e:
        logger.error(f"Error updating indicators: {str(e)}")
        return calculate_all_indicators(df)


def main():
    """Test the technical indicators functionality with sample data."""
    # Create test data
    dates = pd.date_range(start='2023-01-01', periods=250, freq='D')
    df = pd.DataFrame({
        'Date': dates,
        'Open': [100 + i * 0.1 for i in range(250)],
        'High': [101 + i * 0.1 for i in range(250)],
        'Low': [99 + i * 0.1 for i in range(250)],
        'Close': [100.5 + i * 0.1 for i in range(250)],
        'Volume': [1000 + i * 10 for i in range(250)]
    })
    
    # Calculate indicators
    result = calculate_all_indicators(df)
    
    # Show summary
    print("Original DataFrame shape:", df.shape)
    print("Result DataFrame shape:", result.shape)
    print("\nAvailable indicators:", [col for col in result.columns if col not in df.columns])
    
    # Check a few values to ensure calculations are working
    print("\nRSI14 range:", result['rsi14'].min(), "to", result['rsi14'].max())
    print("MA50 sample:", result['ma50'].dropna().iloc[0])
    print("MA200 sample:", result['ma200'].dropna().iloc[0])
    print("EMA20 sample:", result['ema20'].dropna().iloc[0])
    print("ATR14 sample:", result['atr14'].dropna().iloc[0])
    print("Stochastic K14 range:", result['stoch_k'].dropna().min(), "to", result['stoch_k'].dropna().max())
    if 'vwap' in result.columns:
        print("VWAP sample:", result['vwap'].dropna().iloc[0])


if __name__ == "__main__":
    main()
