import requests
import pandas as pd
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

COINGECKO_API_URL = "https://api.coingecko.com/api/v3"

def fetch_current_bitcoin_price(vs_currency: str = "usd") -> Optional[Dict[str, Any]]:
    """
    Fetches the current price of Bitcoin in the specified currency.
    
    Args:
        vs_currency: The target currency (e.g., 'usd', 'eur', 'jpy').
        
    Returns:
        A dictionary containing price and 24h change, or None if the request fails.
    """
    endpoint = f"{COINGECKO_API_URL}/simple/price"
    params = {
        "ids": "bitcoin",
        "vs_currencies": vs_currency,
        "include_24hr_change": "true",
        "include_last_updated_at": "true"
    }
    
    try:
        response = requests.get(endpoint, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data.get("bitcoin")
    except requests.RequestException as e:
        logger.error(f"Error fetching current price: {e}")
        return None

def fetch_bitcoin_historical_data(days: int = 7, vs_currency: str = "usd") -> Optional[pd.DataFrame]:
    """
    Fetches historical market data for Bitcoin.
    
    Args:
        days: Number of days of data to fetch.
        vs_currency: The target currency.
        
    Returns:
        A pandas DataFrame with 'timestamp' and 'price' columns, or None if fails.
    """
    endpoint = f"{COINGECKO_API_URL}/coins/bitcoin/market_chart"
    params = {
        "vs_currency": vs_currency,
        "days": str(days),
        "interval": "daily" if days > 30 else "hourly"
    }
    
    try:
        response = requests.get(endpoint, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        prices = data.get("prices", [])
        df = pd.DataFrame(prices, columns=["timestamp", "price"])
        
        # Convert timestamp (ms) to datetime objects
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
        return df
        
    except requests.RequestException as e:
        logger.error(f"Error fetching historical data: {e}")
        return None

def calculate_price_statistics(df: pd.DataFrame) -> Dict[str, float]:
    """
    Calculates basic statistics from historical price data.
    
    Args:
        df: DataFrame containing 'price' column.
        
    Returns:
        Dictionary containing min, max, and average prices.
    """
    if df.empty or "price" not in df.columns:
        return {}
        
    return {
        "min_price": float(df["price"].min()),
        "max_price": float(df["price"].max()),
        "avg_price": float(df["price"].mean()),
        "volatility": float(df["price"].std())
    }

def add_moving_averages(df: pd.DataFrame, windows: List[int] = [7, 24]) -> pd.DataFrame:
    """
    Adds Simple Moving Average (SMA) columns to the DataFrame.
    
    Args:
        df: DataFrame containing 'price' column.
        windows: List of window sizes for SMA calculation.
        
    Returns:
        DataFrame with additional SMA columns.
    """
    if df.empty:
        return df
        
    processed_df = df.copy()
    for window in windows:
        column_name = f"sma_{window}"
        processed_df[column_name] = processed_df["price"].rolling(window=window).mean()
        
    return processed_df

def format_price(price: float, currency: str = "usd") -> str:
    """
    Formats a numeric price into a human-readable string.
    """
    symbols = {"usd": "$", "eur": "€", "gbp": "£"}
    symbol = symbols.get(currency.lower(), f"{currency.upper()} ")
    return f"{symbol}{price:,.2f}"

if __name__ == "__main__":
    # Quick test
    print("Fetching current Bitcoin price...")
    current = fetch_current_price("usd")
    if current:
        print(f"Current Price: {format_price(current['usd'])}")
        print(f"24h Change: {current['usd_24h_change']:.2f}%")