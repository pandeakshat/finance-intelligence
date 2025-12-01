import pandas as pd
from pathlib import Path
import os

# --- CONFIGURATION ---
# The Librarian only looks here. 
# It does not touch raw data (that is the ETL pipeline's job).
PROCESSED_DATA_PATH = Path("data/processed") 

def get_available_tickers() -> list:
    """
    Scans the 'data/processed' folder to see which stocks 
    have been successfully processed by the ETL pipeline.
    
    Returns:
        list: Sorted list of tickers e.g., ['AAPL', 'TSLA']
    """
    if not PROCESSED_DATA_PATH.exists():
        # If folder doesn't exist, no data is available yet
        return []

    tickers = []
    # We look for files matching the pattern "TICKER_processed.csv"
    for file in PROCESSED_DATA_PATH.glob("*_processed.csv"):
        # Extract "TSLA" from "TSLA_processed.csv"
        ticker = file.name.replace("_processed.csv", "")
        tickers.append(ticker)
    
    return sorted(tickers)

def load_stock_data(ticker: str) -> pd.DataFrame:
    """
    Loads the processed data for a specific stock.
    
    Args:
        ticker (str): The stock symbol (e.g., 'TSLA')
        
    Returns:
        pd.DataFrame: DataFrame with 'Date', 'Close', 'daily_sentiment', etc.
    """
    file_path = PROCESSED_DATA_PATH / f"{ticker}_processed.csv"
    
    if not file_path.exists():
        raise FileNotFoundError(f"❌ Data for {ticker} not found. Run the ETL Pipeline first.")
    
    # Load and parse dates immediately
    df = pd.read_csv(file_path, parse_dates=['Date'])
    
    # valid_dates check (optional safety)
    if df.empty:
        print(f"⚠️ Warning: {ticker} data file is empty.")
    
    return df