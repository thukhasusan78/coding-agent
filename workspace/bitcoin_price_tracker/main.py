import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import time

# --- Configuration ---
st.set_page_config(
    page_title="Bitcoin Price Tracker",
    page_icon="₿",
    layout="wide"
)

# --- Styling ---
st.markdown("""
    <style>
    .main {
        background-color: #f5f7f9;
    }
    .stMetric {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    </style>
    """, unsafe_allow_html=True)

# --- Data Fetching Logic ---
def get_bitcoin_data(currency='usd'):
    """
    Fetches current price and 7-day historical data from CoinGecko API.
    """
    try:
        # Fetch current price and 24h change
        price_url = f"https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies={currency}&include_24hr_change=true&include_last_updated_at=true"
        price_response = requests.get(price_url, timeout=10)
        price_data = price_response.json()

        # Fetch historical data (7 days)
        hist_url = f"https://api.coingecko.com/api/v3/coins/bitcoin/market_chart?vs_currency={currency}&days=7&interval=hourly"
        hist_response = requests.get(hist_url, timeout=10)
        hist_data = hist_response.json()

        return price_data, hist_data
    except Exception as e:
        st.error(f"API Connection Error: {e}")
        return None, None

# --- UI Layout ---
def main():
    st.title("₿ Bitcoin Real-Time Tracker")
    
    # Sidebar Settings
    st.sidebar.header("Dashboard Settings")
    selected_currency = st.sidebar.selectbox(
        "Select Currency",
        options=["USD", "EUR", "GBP", "JPY", "CAD"],
        index=0
    ).lower()
    
    refresh_rate = st.sidebar.slider("Refresh Interval (seconds)", 10, 300, 60)
    
    # Placeholder for dynamic content
    placeholder = st.empty()

    # Main Loop
    while True:
        price_data, hist_data = get_bitcoin_data(selected_currency)

        if price_data and hist_data:
            with placeholder.container():
                # Extract Data
                current_price = price_data['bitcoin'][selected_currency]
                change_24h = price_data['bitcoin'][f'{selected_currency}_24h_change']
                last_updated = datetime.fromtimestamp(price_data['bitcoin']['last_updated_at'])

                # Metrics Row
                col1, col2, col3 = st.columns(3)
                
                currency_symbol = {"usd": "$", "eur": "€", "gbp": "£", "jpy": "¥", "cad": "C$"}.get(selected_currency, "")
                
                col1.metric(
                    label=f"Current Price ({selected_currency.upper()})",
                    value=f"{currency_symbol}{current_price:,.2f}",
                    delta=f"{change_24h:.2f}%"
                )
                
                # Process Historical Data for Chart
                prices = hist_data['prices']
                df = pd.DataFrame(prices, columns=['timestamp', 'price'])
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                df.set_index('timestamp', inplace=True)

                # Chart Section
                st.subheader(f"Price Trend - Last 7 Days ({selected_currency.upper()})")
                st.line_chart(df['price'], use_container_width=True)

                # Statistics Table
                with st.expander("View Market Statistics"):
                    stats_col1, stats_col2 = st.columns(2)
                    stats_col1.write(f"**7D High:** {currency_symbol}{df['price'].max():,.2f}")
                    stats_col1.write(f"**7D Low:** {currency_symbol}{df['price'].min():,.2f}")
                    stats_col2.write(f"**Average Price:** {currency_symbol}{df['price'].mean():,.2f}")
                    stats_col2.write(f"**Last Sync:** {last_updated.strftime('%Y-%m-%d %H:%M:%S')}")

                st.info(f"Auto-refreshing in {refresh_rate} seconds...")
        else:
            st.warning("Unable to fetch data. Please check your internet connection or API limits.")

        # Sleep and Rerun
        time.sleep(refresh_rate)
        st.rerun()

if __name__ == "__main__":
    main()