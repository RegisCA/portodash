"""Fund/ETF name caching for PortoDash.

Fetches long names from yfinance and caches them permanently in fund_names.json.
Names are fetched only once per ticker and persist across sessions.
"""
import json
import os
from typing import Dict

import yfinance as yf


def get_cache_path() -> str:
    """Return the path to the fund names cache file."""
    base_dir = os.path.dirname(os.path.dirname(__file__))
    return os.path.join(base_dir, 'fund_names.json')


def load_fund_names_cache() -> Dict[str, str]:
    """Load the fund names cache from disk.
    
    Returns:
        Dict mapping ticker symbols to long names.
    """
    cache_path = get_cache_path()
    if not os.path.exists(cache_path):
        return {}
    
    try:
        with open(cache_path, 'r') as f:
            return json.load(f)
    except Exception:
        return {}


def save_fund_names_cache(cache: Dict[str, str]) -> None:
    """Save the fund names cache to disk.
    
    Args:
        cache: Dict mapping ticker symbols to long names.
    """
    cache_path = get_cache_path()
    try:
        with open(cache_path, 'w') as f:
            json.dump(cache, f, indent=2, sort_keys=True)
    except Exception:
        pass  # Fail silently if cache can't be written


def fetch_fund_name(ticker: str) -> str:
    """Fetch the long name for a ticker from yfinance.
    
    Args:
        ticker: The ticker symbol.
    
    Returns:
        The long name, or the ticker itself if fetch fails.
    """
    try:
        info = yf.Ticker(ticker).info
        # Try different possible name fields
        name = info.get('longName') or info.get('shortName') or ticker
        return name
    except Exception:
        return ticker


def get_fund_names(tickers: list) -> Dict[str, str]:
    """Get fund names for a list of tickers, using cache when available.
    
    Fetches missing names from yfinance and updates the cache.
    
    Args:
        tickers: List of ticker symbols.
    
    Returns:
        Dict mapping each ticker to its long name.
    """
    # Load existing cache
    cache = load_fund_names_cache()
    
    # Find tickers not in cache
    missing_tickers = [t for t in tickers if t not in cache]
    
    # Fetch missing names
    if missing_tickers:
        for ticker in missing_tickers:
            name = fetch_fund_name(ticker)
            cache[ticker] = name
        
        # Save updated cache
        save_fund_names_cache(cache)
    
    # Return names for all requested tickers
    return {ticker: cache.get(ticker, ticker) for ticker in tickers}


def format_ticker_with_name(ticker: str, name: str) -> str:
    """Format a ticker and name for display.
    
    Args:
        ticker: The ticker symbol.
        name: The long name.
    
    Returns:
        Formatted string like "TICKER - Name" or just "TICKER" if name == ticker.
    """
    if name == ticker:
        return ticker
    return f"{ticker} — {name}"
