import os

class Config:
    """
    Configuration settings for the Bitcoin Price Tracker.
    """
    # API Settings
    # Using CoinGecko API as the primary source
    API_BASE_URL = os.getenv("BTC_TRACKER_API_URL", "https://api.coingecko.com/api/v3")
    PRICE_ENDPOINT = f"{API_BASE_URL}/simple/price"
    COIN_ID = "bitcoin"
    
    # Display Preferences
    DEFAULT_CURRENCY = os.getenv("BTC_TRACKER_CURRENCY", "usd").lower()
    CURRENCY_SYMBOLS = {
        "usd": "$",
        "eur": "€",
        "gbp": "£",
        "jpy": "¥"
    }
    
    # Operational Settings
    UPDATE_INTERVAL_SECONDS = int(os.getenv("BTC_TRACKER_INTERVAL", 60))
    LOG_FILE = "app.log"
    
    # Formatting
    DECIMAL_PRECISION = 2
    TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S"
    
    # UI Colors (ANSI escape codes for CLI)
    COLOR_GREEN = "\033[92m"
    COLOR_RED = "\033[91m"
    COLOR_RESET = "\033[0m"
    COLOR_BOLD = "\033[1m"

    @classmethod
    def get_currency_symbol(cls):
        """Returns the symbol for the configured currency."""
        return cls.CURRENCY_SYMBOLS.get(cls.DEFAULT_CURRENCY, cls.DEFAULT_CURRENCY.upper())

    @property
    def request_params(self):
        """Returns the parameters for the API request."""
        return {
            "ids": self.COIN_ID,
            "vs_currencies": self.DEFAULT_CURRENCY,
            "include_24hr_change": "true",
            "include_last_updated_at": "true"
        }