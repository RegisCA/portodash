"""Financial Modeling Prep (FMP) API integration for stock quotes.

Free tier: 250 requests/hour
API Key: Get from https://site.financialmodelingprep.com/developer/docs/pricing
Documentation: https://site.financialmodelingprep.com/developer/docs
"""
import os
import logging
from typing import Dict, Optional, List

import requests

logger = logging.getLogger(__name__)


def get_fmp_api_key() -> Optional[str]:
    """Get FMP API key from environment variable."""
    return os.environ.get('FMP_API_KEY')


def fetch_batch_quotes_fmp(tickers: List[str], api_key: str) -> Dict[str, Optional[float]]:
    """Fetch current prices for multiple tickers from FMP using batch quote endpoint.
    
    This is the most efficient method - fetches all tickers in a single API call.
    
    Args:
        tickers: List of ticker symbols (supports both US and TSX with .TO suffix)
        api_key: FMP API key
    
    Returns:
        Dictionary mapping ticker -> price (or None if unavailable)
    """
    prices = {t: None for t in tickers}
    
    if not tickers:
        return prices
    
    try:
        # FMP batch quote endpoint - all tickers in one call
        symbols = ','.join(tickers)
        url = f'https://financialmodelingprep.com/api/v3/quote/{symbols}'
        params = {'apikey': api_key}
        
        logger.info(f"Fetching {len(tickers)} tickers from FMP batch quote API")
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        # Check for error messages
        if isinstance(data, dict):
            if 'Error Message' in data:
                logger.error(f"FMP error: {data['Error Message']}")
                return prices
            if 'Information' in data:
                # Rate limit or other info message
                logger.warning(f"FMP info: {data['Information']}")
                return prices
        
        # Parse quote data
        if isinstance(data, list):
            for quote in data:
                symbol = quote.get('symbol')
                price = quote.get('price')
                
                if symbol and price is not None:
                    prices[symbol] = float(price)
                    logger.info(f"Got {symbol} from FMP: ${price}")
                else:
                    logger.warning(f"No price data in FMP response for {symbol}")
        else:
            logger.error(f"Unexpected FMP response format: {type(data)}")
        
        return prices
        
    except requests.exceptions.Timeout:
        logger.error("FMP request timed out after 30 seconds")
        return prices
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch from FMP: {e}")
        return prices
    except Exception as e:
        logger.exception(f"Unexpected error fetching from FMP: {e}")
        return prices


def fetch_quote_fmp(ticker: str, api_key: str) -> Optional[float]:
    """Fetch current price for a single ticker from FMP.
    
    Note: For multiple tickers, use fetch_batch_quotes_fmp() instead for efficiency.
    
    Args:
        ticker: Ticker symbol (supports both US and TSX with .TO suffix)
        api_key: FMP API key
    
    Returns:
        Current price or None if unavailable
    """
    result = fetch_batch_quotes_fmp([ticker], api_key)
    return result.get(ticker)
