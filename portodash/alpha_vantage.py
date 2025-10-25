"""Alpha Vantage data fetcher as backup when yfinance is rate-limited.

Free tier: 500 requests/day, 5 requests/minute
API Key: Get from https://www.alphavantage.co/support/#api-key
"""
import os
import time
import logging
from typing import Dict, Optional

import requests

logger = logging.getLogger(__name__)


def get_alpha_vantage_api_key() -> Optional[str]:
    """Get Alpha Vantage API key from environment variable."""
    return os.environ.get('ALPHAVANTAGE_API_KEY')


def fetch_quote_alpha_vantage(ticker: str, api_key: str) -> Optional[float]:
    """Fetch current price for a single ticker from Alpha Vantage.
    
    Returns the current price or None if unavailable.
    """
    try:
        # Alpha Vantage uses different ticker format for some exchanges
        # TSX tickers need .TO suffix removed and replaced with .TRT
        av_ticker = ticker
        if ticker.endswith('.TO'):
            # Toronto Stock Exchange
            av_ticker = ticker[:-3] + '.TRT'
        
        url = 'https://www.alphavantage.co/query'
        params = {
            'function': 'GLOBAL_QUOTE',
            'symbol': av_ticker,
            'apikey': api_key
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Check for error messages
        if 'Error Message' in data:
            logger.warning(f"Alpha Vantage error for {ticker}: {data['Error Message']}")
            return None
        
        if 'Note' in data:
            # Rate limit message
            logger.warning(f"Alpha Vantage rate limit: {data['Note']}")
            return None
        
        # Extract price from Global Quote
        quote = data.get('Global Quote', {})
        price_str = quote.get('05. price')
        
        if price_str:
            return float(price_str)
        
        logger.warning(f"No price data in Alpha Vantage response for {ticker}")
        return None
        
    except Exception as e:
        logger.error(f"Failed to fetch {ticker} from Alpha Vantage: {e}")
        return None


def fetch_prices_alpha_vantage(tickers: list, api_key: str, rate_limit_delay: float = 12.5) -> Dict[str, Optional[float]]:
    """Fetch prices for multiple tickers from Alpha Vantage.
    
    Args:
        tickers: List of ticker symbols
        api_key: Alpha Vantage API key
        rate_limit_delay: Seconds to wait between requests (default 12.5s = ~5 req/min)
    
    Returns:
        Dictionary mapping ticker -> price (or None if unavailable)
    """
    prices = {}
    
    for i, ticker in enumerate(tickers):
        logger.info(f"Fetching {ticker} from Alpha Vantage ({i+1}/{len(tickers)})")
        prices[ticker] = fetch_quote_alpha_vantage(ticker, api_key)
        
        # Rate limiting: wait between requests (except after the last one)
        if i < len(tickers) - 1:
            time.sleep(rate_limit_delay)
    
    return prices
