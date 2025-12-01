import pandas as pd
from prophet import Prophet
import logging
import os
from pathlib import Path

# --- CONFIGURATION ---
logging.getLogger('cmdstanpy').setLevel(logging.WARNING)
logging.getLogger('prophet').setLevel(logging.WARNING)

PROCESSED_PATH = Path("data/processed")

def generate_forecast(df: pd.DataFrame, horizon_days: int = 90):
    """
    Existing Prophet Forecast Logic.
    """
    if df is None or df.empty:
        return pd.DataFrame()

    prophet_df = df[['Date', 'Close']].rename(columns={'Date': 'ds', 'Close': 'y'})
    
    model = Prophet(daily_seasonality=False, weekly_seasonality=True, yearly_seasonality=True)
    model.fit(prophet_df)
    
    future_dates = model.make_future_dataframe(periods=horizon_days)
    forecast = model.predict(future_dates)
    
    return forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']]

# --- NEW FUNCTION FOR THE RECOMMENDER ---
def find_market_opportunities(target_month_name: str, min_sentiment: float):
    """
    Scans ALL stocks to find those that historically perform best in the 
    Target Month with a sentiment score close to the User's preference.
    """
    opportunities = []
    
    # 1. Loop through all processed files
    if not PROCESSED_PATH.exists():
        return pd.DataFrame()

    for file in PROCESSED_PATH.glob("*_processed.csv"):
        ticker = file.name.replace("_processed.csv", "")
        
        try:
            df = pd.read_csv(file, parse_dates=['Date'])
            
            # 2. Add Month Column
            df['Month'] = df['Date'].dt.month_name()
            df['Returns'] = df['Close'].pct_change()
            
            # 3. Filter for the Target Month (e.g., "November")
            month_data = df[df['Month'] == target_month_name]
            
            if month_data.empty:
                continue
                
            # 4. Calculate Statistics
            avg_return = month_data['Returns'].mean() * 30 # Approx monthly return
            avg_sentiment = month_data['daily_sentiment'].mean()
            win_rate = len(month_data[month_data['Returns'] > 0]) / len(month_data)
            
            # 5. Sentiment Matching Logic
            # If user wants Positive (>0), we look for stocks with at least that sentiment.
            # If user wants Negative (Contrarian <0), we look for stocks below that.
            match = False
            if min_sentiment >= 0 and avg_sentiment >= (min_sentiment - 0.2):
                match = True # Good match for positive vibe
            elif min_sentiment < 0 and avg_sentiment <= (min_sentiment + 0.2):
                match = True # Good match for negative/fear vibe
            
            if match:
                opportunities.append({
                    "Ticker": ticker,
                    "Avg_Monthly_Return": avg_return,
                    "Avg_Sentiment": avg_sentiment,
                    "Win_Rate": win_rate
                })
                
        except Exception as e:
            continue

    # 6. Convert to DataFrame and Rank
    if not opportunities:
        return pd.DataFrame()
        
    opp_df = pd.DataFrame(opportunities)
    # Sort by highest historical return
    return opp_df.sort_values(by='Avg_Monthly_Return', ascending=False)