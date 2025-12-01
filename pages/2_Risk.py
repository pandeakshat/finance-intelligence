import streamlit as st
import plotly.express as px
import sys
from pathlib import Path

# Add root to path so we can import from src
sys.path.append(str(Path(__file__).parent.parent))

# Import Backend Logic
from src.data_loader import get_available_tickers, load_stock_data
from src.risk_engine import calculate_risk_metrics

# --- PAGE CONFIG ---
st.set_page_config(page_title="Risk Dashboard", page_icon="🛡️", layout="wide")

# Load CSS
try:
    with open("assets/style.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
except FileNotFoundError:
    pass

st.title("🛡️ Risk Analysis Dashboard")
st.markdown("### Quantify Portfolio Exposure & Volatility")

# --- SIDEBAR: INPUTS ---
with st.sidebar:
    st.header("⚙️ Risk Parameters")
    
    # 1. Ticker Selection
    tickers = get_available_tickers()
    if not tickers:
        st.warning("⚠️ No data found. Go to 'Sentiment Monitor' to process data.")
        st.stop()
        
    selected_ticker = st.selectbox("Select Asset", tickers)
    
    st.markdown("---")
    
    # 2. Investment Simulation
    investment_amount = st.number_input(
        "Simulated Investment ($)", 
        min_value=1000, 
        value=10000, 
        step=1000,
        help="Input an amount to see how much money is at risk (VaR)."
    )

# --- MAIN CONTENT ---
if selected_ticker:
    # 1. Load Data
    df = load_stock_data(selected_ticker)
    
    # 2. Calculate Metrics (Using the Engine)
    risk_data = calculate_risk_metrics(df)
    
    # 3. Display KPI Cards
    col1, col2, col3 = st.columns(3)
    
    # Metric A: Value at Risk (The "Danger" Metric)
    var_percent = risk_data['var_95'] # e.g., -0.05
    var_dollar = var_percent * investment_amount
    
    with col1:
        st.metric(
            label="Value at Risk (95%)",
            value=f"${abs(var_dollar):,.2f}",
            delta=f"{var_percent:.2%}",
            delta_color="inverse", # Red is bad
            help="This is the maximum amount you are likely to lose on a 'bad day' (with 95% confidence). If the number is $500, it means 1 out of 20 days you might lose more than $500."
        )
        
    # Metric B: Volatility (The "Stress" Metric)
    with col2:
        st.metric(
            label="Annualized Volatility",
            value=f"{risk_data['volatility']:.1%}",
            help="How strictly the stock price swings. Higher = Riskier."
        )
        
    # Metric C: Sharpe Ratio (The "Efficiency" Metric)
    sharpe = risk_data['sharpe']
    sharpe_color = "normal" if sharpe > 1 else "off" # Highlight if good (>1)
    
    with col3:
        st.metric(
            label="Sharpe Ratio",
            value=f"{sharpe:.2f}",
            help="Risk-adjusted return. > 1.0 is considered good. < 0 means you are taking risk for no return."
        )
        
    st.markdown("---")
    
    # 4. Visualization: The Fat Tail Histogram
    st.subheader(f"⚠️ Market Reality Check: Return Distribution")
    
    # We need to ensure 'Returns' column exists for plotting
    df['Returns'] = df['Close'].pct_change()
    
    fig = px.histogram(
        df, 
        x="Returns", 
        nbins=60, 
        title=f"Distribution of Daily Returns for {selected_ticker}",
        template="plotly_dark",
        color_discrete_sequence=["#374151"] # Dark Grey bars
    )
    
    # Add the VaR Line (The cutoff for "Extreme Events")
    fig.add_vline(
        x=var_percent, 
        line_dash="dash", 
        line_color="#FF5252", 
        annotation_text="95% VaR Threshold", 
        annotation_position="top left"
    )
    
    fig.update_layout(
        xaxis_title="Daily Return (%)",
        yaxis_title="Frequency (Days)",
        showlegend=False,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)"
    )
    
    # Format x-axis as percentage
    fig.update_xaxes(tickformat=".1%")
    
    st.plotly_chart(fig, use_container_width=True)
    
    st.info(f"**Insight:** The red dotted line represents the VaR threshold. Any bars to the left of this line represent 'Crash Days' where losses exceeded {abs(var_percent):.1%}.")