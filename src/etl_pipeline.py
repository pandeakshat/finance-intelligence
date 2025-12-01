import pandas as pd
import numpy as np
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import os
import time

# --- CONFIGURATION ---
STOCK_FILE = "data/raw/stock_yfinance_data.csv"
TWEET_FILE = "data/raw/stock_tweets.csv"
OUTPUT_DIR = "data/processed"

def run_pipeline():
    print("🚀 Starting Global ETL Pipeline...")
    
    # 1. Load Data
    print("   📂 Loading Raw Files (This may take a moment)...")
    if not os.path.exists(STOCK_FILE) or not os.path.exists(TWEET_FILE):
        print(f"   ❌ Error: Files not found in data/raw/. Please check paths.")
        return

    df_stocks = pd.read_csv(STOCK_FILE)
    df_tweets = pd.read_csv(TWEET_FILE)
    
    # Standardize Dates immediately
    print("   📅 Standardizing Dates...")
    df_stocks['Date'] = pd.to_datetime(df_stocks['Date']).dt.date
    df_tweets['Date'] = pd.to_datetime(df_tweets['Date']).dt.date

    # 2. Global Sentiment Calculation
    # Optimization: It is faster to calculate sentiment on the whole dataset ONCE 
    # before splitting it up by stock.
    print(f"   🧠 Running VADER Sentiment on {len(df_tweets)} tweets...")
    analyzer = SentimentIntensityAnalyzer()
    
    def get_sentiment(text):
        try:
            return analyzer.polarity_scores(str(text))['compound']
        except:
            return 0

    # Apply sentiment analysis to all tweets
    df_tweets['sentiment_score'] = df_tweets['Tweet'].apply(get_sentiment)
    
    # 3. Identify Unique Tickers
    # We look at the Stock file to see which companies we have price data for
    unique_tickers = df_stocks['Stock Name'].unique()
    print(f"   🔍 Found {len(unique_tickers)} unique stocks to process: {unique_tickers}")
    
    # Ensure output directory exists
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    # 4. Loop Through Each Stock and Process
    print("   ⚙️  Processing individual assets...")
    
    for ticker in unique_tickers:
        try:
            # A. Filter Data for this specific ticker
            stock_subset = df_stocks[df_stocks['Stock Name'] == ticker].copy()
            tweet_subset = df_tweets[df_tweets['Stock Name'] == ticker].copy()
            
            if stock_subset.empty:
                print(f"      ⚠️ Skipping {ticker} (No price data)")
                continue

            # B. Aggregate Sentiment (Daily Mean)
            if not tweet_subset.empty:
                daily_sentiment = tweet_subset.groupby('Date')['sentiment_score'].mean().reset_index()
                daily_sentiment.rename(columns={'sentiment_score': 'daily_sentiment'}, inplace=True)
            else:
                # Handle case where a stock has prices but NO tweets
                daily_sentiment = pd.DataFrame(columns=['Date', 'daily_sentiment'])

            # C. Merge Price + Sentiment
            merged_df = pd.merge(stock_subset, daily_sentiment, on='Date', how='left')
            
            # Sort by Date for Market Memory to work
            merged_df = merged_df.sort_values(by='Date')

            # D. Apply "Market Memory" (Forward Fill)
            # If a tweet happens, its sentiment score lasts for 7 days
            merged_df['daily_sentiment'] = merged_df['daily_sentiment'].ffill(limit=7)
            merged_df['daily_sentiment'] = merged_df['daily_sentiment'].fillna(0) # Fill remaining NaNs with 0

            # E. Save to File
            output_file = os.path.join(OUTPUT_DIR, f"{ticker}_processed.csv")
            merged_df.to_csv(output_file, index=False)
            
            print(f"      ✅ Processed {ticker} ({len(merged_df)} rows)")
            
        except Exception as e:
            print(f"      ❌ Failed to process {ticker}: {e}")

    print("\n   🎉 ETL Pipeline Complete! All datasets are ready in 'data/processed/'.")

if __name__ == "__main__":
    run_pipeline()