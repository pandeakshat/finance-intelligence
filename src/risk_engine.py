import pandas as pd
import numpy as np

def calculate_risk_metrics(df: pd.DataFrame, risk_free_rate: float = 0.02) -> dict:
    """
    Calculates key financial risk metrics: VaR, Volatility, and Sharpe Ratio.
    
    Args:
        df (pd.DataFrame): Dataframe with a 'Close' column.
        risk_free_rate (float): Theoretical return of a safe asset (default 2% or 0.02).
        
    Returns:
        dict: Dictionary containing 'var_95', 'volatility', and 'sharpe'.
    """
    # 1. Validation
    if 'Close' not in df.columns:
        print("❌ Error: 'Close' column missing in risk engine.")
        return {"var_95": 0, "volatility": 0, "sharpe": 0}

    # 2. Calculate Daily Returns
    # pct_change() calculates (Today - Yesterday) / Yesterday
    df['Returns'] = df['Close'].pct_change()
    
    # Drop the first row (NaN) created by pct_change
    clean_returns = df['Returns'].dropna()
    
    if clean_returns.empty:
        return {"var_95": 0, "volatility": 0, "sharpe": 0}
    
    # --- METRIC 1: Value at Risk (VaR 95%) ---
    # Concept: "In the worst 5% of days, how much could we lose?"
    # We take the 5th percentile of the returns distribution.
    var_95 = np.percentile(clean_returns, 5) 
    
    # --- METRIC 2: Annualized Volatility ---
    # Standard Deviation of daily returns * Square Root of 252 (Trading Days)
    volatility = clean_returns.std() * np.sqrt(252)
    
    # --- METRIC 3: Sharpe Ratio ---
    # (Return - Risk Free Rate) / Risk
    # This measures "Is the return worth the risk?"
    risk_free_daily = risk_free_rate / 252
    excess_return = clean_returns.mean() - risk_free_daily
    
    # Avoid division by zero if volatility is 0
    if clean_returns.std() == 0:
        sharpe = 0
    else:
        sharpe = (excess_return / clean_returns.std()) * np.sqrt(252)
    
    return {
        "var_95": var_95,      # e.g., -0.04 means a 4% loss limit
        "volatility": volatility, # e.g., 0.30 means 30% annual fluctuation
        "sharpe": sharpe       # > 1.0 is generally good
    }