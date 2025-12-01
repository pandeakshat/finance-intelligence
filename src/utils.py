from datetime import date

# --- CONFIGURATION ---
# Since our dataset is static (ending in late 2022), we simulate "Today".
# This ensures charts show the "latest" data as relative to this date,
# rather than showing a blank chart for 2025.
SIMULATED_TODAY = date(2022, 11, 1)

def get_simulated_date():
    """
    Returns the 'simulated' today for the demo.
    """
    return SIMULATED_TODAY

def format_currency(value):
    """Formats 1234.56 as $1,234.56"""
    return f"${value:,.2f}"

def format_percentage(value):
    """Formats 0.0512 as 5.12%"""
    return f"{value:.2%}"

def format_large_number(num):
    """
    Formats large integers into readable strings (K, M, B).
    Example: 1,500,000 -> 1.5M
    """
    if num >= 1_000_000_000:
        return f"{num / 1_000_000_000:.1f}B"
    elif num >= 1_000_000:
        return f"{num / 1_000_000:.1f}M"
    elif num >= 1_000:
        return f"{num / 1_000:.1f}K"
    else:
        return str(num)