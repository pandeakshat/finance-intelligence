import streamlit as st
import os
from src.data_loader import get_available_tickers
from src.utils import get_simulated_date

# 1. Page Configuration (Must be the first Streamlit command)
st.set_page_config(
    page_title="Finance Intelligence Hub",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Load Custom CSS
# We will create assets/style.css next, but this function prepares app.py to read it.
def local_css(file_name):
    if os.path.exists(file_name):
        with open(file_name) as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    else:
        # Fallback if CSS file is missing
        st.warning(f"Note: {file_name} not found. Using default style.")

local_css("assets/style.css") 

# 3. Main Header
st.title("⚡ Finance Intelligence Hub")
st.markdown("### Institutional-Grade Analytics Dashboard")
st.markdown("---")

# 4. System Status & Metrics
# We use columns to create a "Dashboard" feel right at the entry
col1, col2, col3 = st.columns(3)

# Metric A: Simulated Date (From utils.py)
sim_date = get_simulated_date()
col1.metric("📅 Market Data Date", sim_date.strftime("%Y-%m-%d"))

# Metric B: Available Tickers (From data_loader.py)
tickers = get_available_tickers()
if tickers:
    # Shows count and lists first few tickers (e.g., "TSLA, AAPL...")
    ticker_preview = ", ".join(tickers[:3]) + ("..." if len(tickers) > 3 else "")
    col2.metric("📈 Stocks Loaded", len(tickers), ticker_preview)
else:
    col2.metric("📈 Stocks Loaded", "0", "Action Required")

# Metric C: System Health
status = "Online" if tickers else "⚠️ Setup Needed"
col3.metric("🟢 System Status", status)

st.markdown("---")

# 5. Navigation Guide (The Map)
st.info("ℹ️ **Navigation Guide: Select a Module from the Sidebar**")

row1_col1, row1_col2 = st.columns(2)

with row1_col1:
    st.markdown("""
    #### 🔭 1. Forecast Studio
    * **Goal:** Predict future price trends.
    * **Engine:** Facebook Prophet (Machine Learning).
    * **Output:** 30-90 day price trajectory with confidence intervals.
    """)

    st.markdown("""
    #### 🛡️ 2. Risk Analysis
    * **Goal:** Quantify portfolio danger.
    * **Engine:** Value at Risk (VaR) & Volatility Calculators.
    * **Output:** "Fat Tail" risk analysis and Sharpe Ratios.
    """)

with row1_col2:
    st.markdown("""
    #### 🧠 3. Sentiment Monitor (Admin)
    * **Goal:** Correlate News with Stock Price.
    * **Engine:** VADER (NLP) Sentiment Analysis.
    * **Action:** **Go here first** to run the ETL Pipeline and generate data.
    """)

# 6. Sidebar Footer
st.sidebar.markdown("---")
st.sidebar.caption(f"Finance Hub v1.0\nSimulated Date: {sim_date}")