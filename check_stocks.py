import streamlit as st
import pandas as pd
import os

# --- CONFIGURATION ---
# Update these paths to match where your files are
STOCK_PATH = "data/raw/stock_yfinance_data.csv"
SENTIMENT_PATH = "data/raw/stock_tweets.csv"

def find_common_stocks():
    st.title("🔎 Data Validation: Common Stocks")
    st.markdown("Checks for overlapping tickers between **Price Data** and **Sentiment Data**.")

    # 1. Check if files exist
    if not os.path.exists(STOCK_PATH):
        st.error(f"❌ File not found: `{STOCK_PATH}`")
        return
    if not os.path.exists(SENTIMENT_PATH):
        st.error(f"❌ File not found: `{SENTIMENT_PATH}`")
        return

    st.info("⏳ Loading files... please wait.")
    
    # 2. Load the Dataframes
    try:
        # Load only necessary columns
        df_stocks = pd.read_csv(STOCK_PATH, usecols=['Stock Name'])
        df_sentiment = pd.read_csv(SENTIMENT_PATH, usecols=['Stock Name'])
    except ValueError as e:
        st.error(f"❌ Column Error: {e}")
        st.warning("Check if the column is named 'Stock Name' or 'Ticker' in your CSVs.")
        return
    
    # 3. Get Unique Tickers
    stock_list = set(df_stocks['Stock Name'].unique())
    sentiment_list = set(df_sentiment['Stock Name'].unique())
    
    # 4. Find the Intersection
    common_tickers = list(stock_list & sentiment_list)
    common_tickers.sort()
    
    # --- REPORT UI ---
    st.divider()
    
    # Metrics row
    col1, col2, col3 = st.columns(3)
    col1.metric("Stocks in Price Data", len(stock_list))
    col2.metric("Stocks in Tweet Data", len(sentiment_list))
    col3.metric("Common Stocks", len(common_tickers))
    
    st.divider()
    
    if common_tickers:
        st.success(f"✅ Found {len(common_tickers)} stocks present in both datasets!")
        
        # Display as a clean list or dataframe
        st.subheader("Available Tickers for Demo:")
        st.dataframe(pd.DataFrame(common_tickers, columns=["Ticker"]), use_container_width=True)
        
        # Suggest next step
        st.markdown("### 💡 Recommendation")
        st.write(f"For your `etl_pipeline.py`, pick one of these tickers: **{common_tickers[0]}**")
    else:
        st.error("❌ No overlap found! Check your CSV headers or file contents.")

if __name__ == "__main__":
    find_common_stocks()