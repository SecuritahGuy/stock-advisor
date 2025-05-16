"""
Stock discovery module - finds new trading candidates using technical and fundamental filters
"""
from datetime import datetime as dt
import os
import pandas as pd
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

try:
    from finvizfinance.screener.overview import Overview as Screener
    finviz_available = True
except ImportError:
    logger.warning("finvizfinance not installed. Run 'pip install finvizfinance' for stock discovery.")
    finviz_available = False

# Create data directory if it doesn't exist
DATA_DIR = Path(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data'))
DATA_DIR.mkdir(exist_ok=True)

# File to store candidates
CANDIDATES_FILE = DATA_DIR / 'candidates.parquet'

# Configure default strategy filters
STRATEGIES = {
    "oversold_reversals": {
        "name": "Oversold Reversals",
        "description": "Stocks with temporary pullbacks in strong uptrends",
        "filters": {
            "rsi14": "-40",               # RSI below 40 (oversold)
            "sma200_pa": "pa",            # Price above 200-day SMA (uptrend intact)
            "ta_change": "u5",            # Up at least 5% from recent lows (bounce)
            "price": "10to150",           # $10-$150 price range
            "averagevolume": "over_500k"  # Sufficient liquidity
        }
    },
    "fresh_momentum": {
        "name": "Fresh Momentum",
        "description": "Stocks breaking out with strong momentum",
        "filters": {
            "sma20_pa": "pa",             # Price above 20-day SMA
            "sma50_pa": "pa",             # Price above 50-day SMA
            "sma200_pa": "pa",            # Price above 200-day SMA
            "ta_highlow52w": "h0to3",     # Within 3% of 52-week high
            "ta_change": "u3",            # Up at least 3% recently
            "averagevolume": "over_1m"    # High liquidity
        }
    },
    "quality_value": {
        "name": "Quality Value",
        "description": "Fundamentally sound stocks at reasonable prices",
        "filters": {
            "cap": "mid,large",           # Mid or large cap
            "pe": "profitable,under25",   # PE under 25 and profitable
            "peg": "under1.5",            # PEG under 1.5
            "roe": "over15",              # ROE over 15%
            "debteq": "under0.5"          # Low debt
        }
    }
}

def find_candidates(strategy="oversold_reversals", limit=20, min_price=10, max_price=150):
    """
    Find stock candidates matching the specified strategy

    Args:
        strategy (str): Strategy name from the STRATEGIES dict
        limit (int): Maximum number of candidates to return
        min_price (float): Minimum stock price
        max_price (float): Maximum stock price

    Returns:
        pd.DataFrame or None: DataFrame of candidates or None if screener unavailable
    """
    if not finviz_available:
        logger.error("finvizfinance package not installed. Run 'pip install finvizfinance'")
        return None

    if strategy not in STRATEGIES:
        logger.error(f"Unknown strategy: {strategy}. Available: {list(STRATEGIES.keys())}")
        return None

    try:
        # Get strategy filters and customize price range if needed
        filters = STRATEGIES[strategy]["filters"].copy()
        if min_price != 10 or max_price != 150:
            price_range = f"{min_price}to{max_price}"
            filters["price"] = price_range

        logger.info(f"Running {STRATEGIES[strategy]['name']} screener with filters: {filters}")

        # Initialize the screener
        screener = Screener()
        
        # Attempt to set filters; continue even if invalid filters occur
        try:
            screener.set_filter(filters_dict=filters)
        except Exception as e:
            logger.warning(f"Error setting screener filters: {e}. Proceeding without filters.")
        
        # Get the results as a DataFrame
        try:
            df = screener.screener_view()
        except Exception as e:
            logger.error(f"Error fetching screener view: {e}")
            return None

        if df.empty:
            logger.warning("No candidates found with the specified filters.")
            return None

        # Add metadata
        df["strategy"] = strategy
        df["strategy_name"] = STRATEGIES[strategy]["name"]
        df["discovered_at"] = dt.utcnow()

        # Limit the results
        if len(df) > limit:
            df = df.head(limit)

        logger.info(f"Found {len(df)} candidates for {STRATEGIES[strategy]['name']} strategy")

        return df

    except Exception as e:
        logger.error(f"Error running screener: {str(e)}")
        return None

def save_candidates(df, append=True):
    """
    Save candidate stocks to parquet file
    
    Args:
        df (pd.DataFrame): DataFrame of candidates
        append (bool): Whether to append to existing file
        
    Returns:
        bool: Success status
    """
    if df is None or len(df) == 0:
        logger.warning("No candidates to save")
        return False
    
    try:
        # Read existing candidates if appending
        if append and CANDIDATES_FILE.exists():
            existing_df = pd.read_parquet(CANDIDATES_FILE)
            combined_df = pd.concat([existing_df, df], ignore_index=True)
            # Remove duplicates, keeping the most recent
            combined_df = combined_df.sort_values('discovered_at', ascending=False)
            combined_df = combined_df.drop_duplicates(subset=['Ticker'], keep='first')
        else:
            combined_df = df
        
        # Save to parquet
        combined_df.to_parquet(CANDIDATES_FILE, index=False)
        logger.info(f"Saved {len(df)} candidates to {CANDIDATES_FILE}")
        return True
        
    except Exception as e:
        logger.error(f"Error saving candidates: {str(e)}")
        return False

def get_candidates(days=30, top_n=None, min_market_cap=None):
    """
    Get candidate stocks discovered in the last N days
    
    Args:
        days (int): Number of days to look back
        top_n (int): Return only top N candidates by market cap
        min_market_cap (float): Minimum market cap in millions
        
    Returns:
        pd.DataFrame: DataFrame of candidates
    """
    if not CANDIDATES_FILE.exists():
        logger.warning(f"No candidates file found at {CANDIDATES_FILE}")
        return pd.DataFrame()
    
    try:
        df = pd.read_parquet(CANDIDATES_FILE)
        
        # Filter by discovery date
        if days:
            cutoff_date = dt.utcnow() - pd.Timedelta(days=days)
            df = df[df['discovered_at'] >= cutoff_date]
        
        # Filter by market cap if specified
        if min_market_cap:
            # Convert market cap string to numeric
            if 'Market Cap' in df.columns:
                # Handle market cap format like "1.2B", "450M", etc.
                def parse_market_cap(mc_str):
                    if not mc_str or pd.isna(mc_str):
                        return 0
                    mc_str = mc_str.strip()
                    multiplier = 1
                    if mc_str.endswith('B'):
                        multiplier = 1000
                        mc_str = mc_str[:-1]
                    elif mc_str.endswith('M'):
                        mc_str = mc_str[:-1]
                    try:
                        return float(mc_str) * multiplier
                    except:
                        return 0
                
                df['MarketCapMillions'] = df['Market Cap'].apply(parse_market_cap)
                df = df[df['MarketCapMillions'] >= min_market_cap]
                
        # Sort by market cap if available
        if 'MarketCapMillions' in df.columns:
            df = df.sort_values('MarketCapMillions', ascending=False)
        
        # Limit to top N
        if top_n and len(df) > top_n:
            df = df.head(top_n)
            
        return df
        
    except Exception as e:
        logger.error(f"Error getting candidates: {str(e)}")
        return pd.DataFrame()

def update_tickers_env(candidates_df, max_tickers=30, env_file='.env'):
    """
    Update TICKERS in .env file with top candidates
    
    Args:
        candidates_df (pd.DataFrame): DataFrame of candidates
        max_tickers (int): Maximum number of tickers to include
        env_file (str): Path to .env file
        
    Returns:
        bool: Success status
    """
    if candidates_df.empty:
        logger.warning("No candidates to add to .env")
        return False
    
    try:
        # Get tickers from candidates
        new_tickers = candidates_df['Ticker'].tolist()
        
        # Read existing .env file
        env_path = Path(env_file)
        env_lines = []
        current_tickers = []
        
        if env_path.exists():
            with open(env_path, 'r') as f:
                env_lines = f.readlines()
                
            # Find TICKERS line
            for line in env_lines:
                if line.startswith('TICKERS='):
                    tickers_str = line.strip().split('=', 1)[1]
                    # Remove quotes if present
                    tickers_str = tickers_str.strip('\'"')
                    current_tickers = [t.strip() for t in tickers_str.split(',')]
                    break
        
        # Combine current and new tickers, removing duplicates
        all_tickers = []
        # Add current tickers first (they have priority)
        for ticker in current_tickers:
            if ticker and ticker not in all_tickers:
                all_tickers.append(ticker)
                
        # Add new tickers
        for ticker in new_tickers:
            if ticker and ticker not in all_tickers:
                all_tickers.append(ticker)
        
        # Limit to max_tickers
        if len(all_tickers) > max_tickers:
            all_tickers = all_tickers[:max_tickers]
            
        # Create new TICKERS line
        new_tickers_line = f'TICKERS={",".join(all_tickers)}\n'
        
        # Update .env file
        if env_lines:
            for i, line in enumerate(env_lines):
                if line.startswith('TICKERS='):
                    env_lines[i] = new_tickers_line
                    break
            else:
                # TICKERS line not found, add it
                env_lines.append(new_tickers_line)
        else:
            # No existing file, create it
            env_lines = [new_tickers_line]
        
        # Write back to file
        with open(env_path, 'w') as f:
            f.writelines(env_lines)
            
        added = set(all_tickers) - set(current_tickers)
        logger.info(f"Updated {env_file} with {len(all_tickers)} tickers. Added: {', '.join(added)}")
        return True
        
    except Exception as e:
        logger.error(f"Error updating tickers in .env: {str(e)}")
        return False
