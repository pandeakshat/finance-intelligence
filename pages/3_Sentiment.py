import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import time
import sys
from pathlib import Path

# Add the root directory to path so we can import from src
sys.path.append(str(Path(__file__).parent.parent))

# Import your actual backend functions
from src.data_loader import get_available_tickers, load_stock_data
from src.etl_pipeline import run_pipeline

# --- PAGE CONFIG ---
st.set_page_config(page_title="Sentiment Monitor", page_icon="🧠", layout="wide")


# Load CSS
try:
    with open("assets/style.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
except FileNotFoundError:
    pass

st.title("🧠 Sentiment Monitor")
st.markdown("### Correlation Analysis: Social Sentiment vs. Price Action")

# --- SIDEBAR: ADMIN CONSOLE ---
with st.sidebar:
    st.header("⚙️ Data Pipeline")
    st.info("Run this to generate/update the data files.")
    
    # The "Admin" Button
    if st.button("🚀 Process All Datasets", type="primary"):
        with st.spinner("Running ETL Pipeline... (Check Terminal for Logs)"):
            try:
                # 1. Trigger the logic in src/etl_pipeline.py
                run_pipeline()
                
                # 2. Success Feedback
                st.success("Pipeline Finished Successfully!")
                time.sleep(1)
                
                # 3. Clear Cache & Reload so new data appears
                st.cache_data.clear()
                st.rerun()
                
            except Exception as e:
                st.error(f"Pipeline Failed: {e}")
    shock_factor = st.slider("Simulate Negative News Event", 0, 100, 0, help="0 = No Shock, 100 = Major Scandal")
         
    st.markdown("---")
    st.caption("Select an asset below to visualize the data.")

# --- MAIN CONTENT ---

# 1. Get Available Data
tickers = get_available_tickers()

if not tickers:
    st.warning("⚠️ No data found. Please click 'Process All Datasets' in the sidebar.")
    st.stop()

# 2. Asset Selector
col1, col2 = st.columns([1, 3])
with col1:
    selected_ticker = st.selectbox("Select Asset", tickers)

# 3. Load & Analyze
if selected_ticker:
    df = load_stock_data(selected_ticker)
    
    # Basic KPI: Last Sentiment
    last_sentiment = df['daily_sentiment'].iloc[-1]
    
    # Determine Color/Label
    if last_sentiment > 0.05:
        color, label = "#4CAF50", "Positive" # Green
    elif last_sentiment < -0.05:
        color, label = "#FF5252", "Negative" # Red
    else:
        color, label = "#B0BEC5", "Neutral"  # Grey
        
    with col2:
        st.metric("Latest Sentiment Signal", f"{label} ({last_sentiment:.2f})")


    if shock_factor > 0:
        # Theoretical impact: 100% shock = Drop sentiment to -1.0
        # and reduce price by a correlation factor (e.g., 5% drop for max shock)
        
        st.warning(f"⚠️ SIMULATING SHOCK: {shock_factor}% Negative News Intensity")
        
        # 1. Adjust Sentiment Line
        # We degrade the last 30 days of sentiment
        df['daily_sentiment'] = df['daily_sentiment'] - (shock_factor / 100)
        
        # 2. Adjust Price (Hypothetical Stress Test)
        # Assume a max 15% drop for a 100% shock
        price_drop = 1 - ((shock_factor / 100) * 0.15) 
        
        # Apply drop to the last 7 days to simulate a crash "happening now"
        mask = df.index[-7:]
        df.loc[mask, 'Close'] = df.loc[mask, 'Close'] * price_drop

    # 4. Dual-Axis Visualization
    st.subheader(f"Price vs. Sentiment: {selected_ticker}")
    
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # Trace 1: Stock Price (Cyan Line)
    fig.add_trace(
        go.Scatter(
            x=df['Date'], y=df['Close'], 
            name="Stock Price", 
            line=dict(color='#00F0FF', width=2)
        ),
        secondary_y=False,
    )

    # Trace 2: Sentiment (Orange Step Line)
    # shape='hv' creates the "Step" look, showing how sentiment holds steady
    fig.add_trace(
        go.Scatter(
            x=df['Date'], y=df['daily_sentiment'], 
            name="Sentiment (Market Memory)", 
            line=dict(color='#FFA500', width=2, shape='hv', dash='dot'), 
            fill='tozeroy',
            fillcolor='rgba(255, 165, 0, 0.1)' 
        ),
        secondary_y=True,
    )

    # Chart Styling
    fig.update_layout(
        height=500,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="white"),
        hovermode="x unified",
        legend=dict(orientation="h", y=1.1)
    )
    # Axes
    fig.update_yaxes(title_text="Price ($)", secondary_y=False, showgrid=True, gridcolor='#333')
    fig.update_yaxes(title_text="Sentiment (-1 to +1)", secondary_y=True, showgrid=False, range=[-1.1, 1.1])

    st.plotly_chart(fig, use_container_width=True)
    
    # 5. Explainer
    st.info("""
    **ℹ️ How to read this:**
    * **Cyan Line (Price):** The actual closing price of the stock.
    * **Orange Area (Sentiment):** The aggregated news sentiment. 
    * *Note:* We use 'Market Memory' (Forward Fill). If a major news event happens, the sentiment score 'sticks' for 7 days, simulating the lasting impact of news on trader psychology.
    """)


# ... (Keep all existing code, this goes AFTER the st.plotly_chart(fig) block) ...

    st.markdown("---")
    
    # --- NEW FEATURE: SENTIMENT BUCKET BACKTESTER ---
    st.subheader("📊 Sentiment Signal Quality (Backtest)")
    st.markdown("We analyzed historical data to see how the stock performs **1 day after** falling into a specific sentiment range.")

    # 1. Prepare Data for Backtesting
    # We need to see the Next Day's return to judge if the sentiment was a good signal
    df['Next_Day_Return'] = df['Close'].pct_change().shift(-1)
    
    # 2. Create Buckets (Bins)
    # We create bins from -1.0 to 1.0 with a step of 0.2
    # Bins: [-1.0, -0.8, -0.6, -0.4, -0.2, 0.0, 0.2, 0.4, 0.6, 0.8, 1.0]
    bins = [-1.0, -0.8, -0.6, -0.4, -0.2, 0.0, 0.2, 0.4, 0.6, 0.8, 1.0]
    labels = ['-1.0 to -0.8', '-0.8 to -0.6', '-0.6 to -0.4', '-0.4 to -0.2', 
              '-0.2 to 0.0', '0.0 to 0.2', '0.2 to 0.4', '0.4 to 0.6', 
              '0.6 to 0.8', '0.8 to 1.0']
    
    df['Sentiment_Range'] = pd.cut(df['daily_sentiment'], bins=bins, labels=labels)
    
    # 3. Group & Calculate Win Rate
    # We calculate the Mean Return for each bucket
    bucket_stats = df.groupby('Sentiment_Range', observed=False)['Next_Day_Return'].mean().reset_index()
    
    # 4. Color Logic
    # Green if the bucket historically leads to profit, Red if loss
    bucket_colors = ['#00FF00' if x > 0 else '#FF5252' for x in bucket_stats['Next_Day_Return']]

    # 5. Visual: The "Signal Strength" Bar Chart
    fig_buckets = go.Figure(go.Bar(
        x=bucket_stats['Sentiment_Range'],
        y=bucket_stats['Next_Day_Return'],
        marker_color=bucket_colors,
        text=bucket_stats['Next_Day_Return'].apply(lambda x: f"{x:.2%}"),
        textposition='auto'
    ))

    fig_buckets.update_layout(
        title=f"Avg Next-Day Return by Sentiment Range ({selected_ticker})",
        xaxis_title="Sentiment Score Range (From Extreme Negative to Positive)",
        yaxis_title="Avg Return Next Day",
        template="plotly_dark",
        height=400,
        yaxis_tickformat=".2%"
    )
    
    st.plotly_chart(fig_buckets, use_container_width=True)
    
    # 6. Automated Insight
    # Find the best performing bucket
    best_bucket = bucket_stats.loc[bucket_stats['Next_Day_Return'].idxmax()]
    worst_bucket = bucket_stats.loc[bucket_stats['Next_Day_Return'].idxmin()]
    
    c1, c2 = st.columns(2)
    with c1:
        st.success(f"📈 **Bullish Signal:** Historically, when sentiment is between **{best_bucket['Sentiment_Range']}**, the stock rises **{best_bucket['Next_Day_Return']:.2%}** the next day.")
    with c2:
        st.error(f"📉 **Bearish Signal:** When sentiment is between **{worst_bucket['Sentiment_Range']}**, the stock typically falls **{worst_bucket['Next_Day_Return']:.2%}**.")