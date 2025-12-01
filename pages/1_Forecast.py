import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

# Import Backend Logic
from src.data_loader import get_available_tickers, load_stock_data
from src.forecasting import generate_forecast, find_market_opportunities

# --- PAGE CONFIG ---
st.set_page_config(page_title="Forecast Studio", page_icon="🔭", layout="wide")

try:
    with open("assets/style.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
except FileNotFoundError:
    pass

st.title("🔭 Forecast & Strategy Studio")

# Create Tabs
tab1, tab2 = st.tabs(["📈 Asset Forecast", "💡 Smart Recommender"])

# ==========================================
# TAB 1: EXISTING PROPHET FORECAST
# ==========================================
with tab1:
    st.markdown("### AI-Powered Trend Prediction")
    
    col_cfg1, col_cfg2 = st.columns(2)
    
    tickers = get_available_tickers()
    if not tickers:
        st.error("No data found. Run ETL Pipeline.")
        st.stop()
        
    with col_cfg1:
        selected_ticker = st.selectbox("Select Asset", tickers)
    with col_cfg2:
        horizon = st.slider("Forecast Horizon (Days)", 30, 365, 90)

    if selected_ticker:
        df = load_stock_data(selected_ticker)
        
        with st.spinner("Calculating Forecast..."):
            forecast = generate_forecast(df, horizon_days=horizon)
            
        # Metrics
        current_price = df['Close'].iloc[-1]
        pred_price = forecast['yhat'].iloc[-1]
        pct_change = (pred_price - current_price) / current_price
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Current Price", f"${current_price:,.2f}")
        m2.metric("Predicted Price", f"${pred_price:,.2f}", f"{pct_change:.2%}")
        m3.metric("Uncertainty Range", f"± ${(forecast['yhat_upper'].iloc[-1] - pred_price):.2f}")

        # Visualization
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df['Date'], y=df['Close'], name='History', line=dict(color='#00F0FF')))
        
        future = forecast[forecast['ds'] > df['Date'].max()]
        fig.add_trace(go.Scatter(x=future['ds'], y=future['yhat'], name='Forecast', line=dict(color='#FFA500', dash='dash')))
        
        # Confidence Cone
        fig.add_trace(go.Scatter(
            x=future['ds'].tolist() + future['ds'].tolist()[::-1],
            y=future['yhat_upper'].tolist() + future['yhat_lower'].tolist()[::-1],
            fill='toself', fillcolor='rgba(255, 165, 0, 0.15)', 
            line=dict(color='rgba(0,0,0,0)'), name='Confidence'
        ))
        
        fig.update_layout(template="plotly_dark", height=500, plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True)
        
        # --- FIXED SEASONALITY SECTION ---
        st.subheader(f"📅 Seasonality: {selected_ticker}")
        
        # 1. Create Month Name Column
        df['Month'] = df['Date'].dt.month_name()
        
        # 2. Calculate Daily Returns FIRST
        df['Daily_Return'] = df['Close'].pct_change()
        
        # 3. Group by Month and take Mean of Returns (The Fix)
        # We dropna() to avoid errors with the first row being NaN
        monthly_stats = df.dropna().groupby('Month')['Daily_Return'].mean().reset_index()
        
        # 4. Sort by calendar order
        month_order = ['January', 'February', 'March', 'April', 'May', 'June', 
                       'July', 'August', 'September', 'October', 'November', 'December']
        monthly_stats['Month'] = pd.Categorical(monthly_stats['Month'], categories=month_order, ordered=True)
        monthly_stats = monthly_stats.sort_values('Month')

        # 5. Visualize
        fig_season = go.Figure(go.Bar(
            x=monthly_stats['Month'], 
            y=monthly_stats['Daily_Return'],
            marker_color=['#00FF00' if x > 0 else '#FF0000' for x in monthly_stats['Daily_Return']]
        ))
        
        # Format Y-axis as percentage
        fig_season.update_layout(
            template="plotly_dark", 
            height=300, 
            title="Avg Monthly Returns ( Seasonality Pattern )",
            yaxis_tickformat=".2%" 
        )
        st.plotly_chart(fig_season, use_container_width=True)

# ==========================================
# TAB 2: SMART RECOMMENDER
# ==========================================
with tab2:
    st.header("🤖 AI Opportunity Finder")
    st.markdown("""
    **How it works:** Tell us your budget, your target month, and the market 'vibe' (sentiment) you are looking for. 
    The AI will scan **all assets** to find historical matches.
    """)
    
    # 1. User Inputs
    c1, c2, c3 = st.columns(3)
    
    with c1:
        budget = st.number_input("💰 Investment Amount ($)", value=10000, step=1000)
    
    with c2:
        target_month = st.selectbox("📅 Target Month", 
            ['January', 'February', 'March', 'April', 'May', 'June', 
             'July', 'August', 'September', 'October', 'November', 'December'],
            index=10) # Default to November
            
    with c3:
        sentiment_pref = st.slider("🧠 Sentiment Score", -1.0, 1.0, 0.5, 
            help="1.0 = Very Positive News, -1.0 = Extreme Fear/Negative News")

    st.divider()

    # 2. Run the Scan
    if st.button("🔍 Scan Market for Opportunities", type="primary"):
        with st.spinner(f"Analyzing all assets for {target_month} with Sentiment ~ {sentiment_pref}..."):
            
            # Call the backend function
            results = find_market_opportunities(target_month, sentiment_pref)
            
            if results.empty:
                st.warning("No perfect matches found. Try adjusting the sentiment score.")
            else:
                # 3. Display Top 3 Recommendations
                top_picks = results.head(3)
                
                st.subheader(f"🏆 Top Recommendations for {target_month}")
                
                # Display Cards
                cols = st.columns(3)
                for index, (i, row) in enumerate(top_picks.iterrows()):
                    # Handle varying number of results (if < 3)
                    if index < len(cols):
                        with cols[index]:
                            # Calculate Projected Profit
                            projected_profit = budget * row['Avg_Monthly_Return']
                            color = "#4CAF50" if row['Avg_Monthly_Return'] > 0 else "#FF5252"
                            
                            st.markdown(f"""
                            <div style="background-color: #1f2937; padding: 20px; border-radius: 10px; border: 1px solid #374151;">
                                <h3 style="color: #00F0FF; margin:0;">{row['Ticker']}</h3>
                                <p style="color: #9ca3af; font-size: 0.9em;">Hist. Avg Return: <span style="color:{color}">{row['Avg_Monthly_Return']:.1%}</span></p>
                                <p style="color: #9ca3af; font-size: 0.9em;">Hist. Sentiment: <b>{row['Avg_Sentiment']:.2f}</b></p>
                                <hr style="border-color: #374151;">
                                <p style="color: white; font-size: 1.1em; margin-bottom: 0;">Proj. Value: <b>${(budget + projected_profit):,.2f}</b></p>
                                <p style="color: {color}; font-size: 0.9em; margin-top: 0;">({"+" if projected_profit>0 else ""}${projected_profit:,.2f})</p>
                            </div>
                            """, unsafe_allow_html=True)

                # 4. Detailed Table
                st.markdown("<br>", unsafe_allow_html=True)
                with st.expander("📊 View All Candidates"):
                    st.dataframe(
                        results.style.format({
                            "Avg_Monthly_Return": "{:.2%}",
                            "Avg_Sentiment": "{:.2f}",
                            "Win_Rate": "{:.1%}"
                        })
                    )