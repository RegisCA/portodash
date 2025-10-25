"""Cache utilities for price data."""
from datetime import datetime, timedelta
import pandas as pd
import os
import logging
import pytz


logger = logging.getLogger(__name__)


def get_cached_prices(tickers, csv_path, max_age_hours=24):
    """Get most recent cached prices for tickers from historical CSV.
    
    Args:
        tickers: List of ticker symbols
        csv_path: Path to historical.csv file
        max_age_hours: Maximum age in hours for cached prices (default 24)
        
    Returns:
        Dict mapping ticker->price, or None if ticker not found or too old
    """
    if not os.path.exists(csv_path):
        return {t: None for t in tickers}, {t: None for t in tickers}
        
    try:
        # Read historical CSV
        df = pd.read_csv(csv_path, parse_dates=['date'])
        if df.empty:
            return {t: None for t in tickers}, {t: None for t in tickers}

        # Get latest price for each ticker within max age
        now = pd.to_datetime(datetime.utcnow()).tz_localize(pytz.UTC)
        cutoff = now - timedelta(hours=max_age_hours)

        # Ensure date column is tz-aware for comparison
        if df['date'].dt.tz is None:
            df['date'] = df['date'].dt.tz_localize(pytz.UTC)

        recent = df[df['date'] >= cutoff]
        if recent.empty:
            return {t: None for t in tickers}, {t: None for t in tickers}

        # Get most recent price for each ticker
        latest = recent.sort_values('date').groupby('ticker').last()

        prices = {}
        times = {}
        for t in tickers:
            if t in latest.index:
                prices[t] = float(latest.loc[t, 'price'])
                # Ensure we return an ISO-format UTC timestamp string
                try:
                    ts = pd.Timestamp(latest.loc[t, 'date'])
                    # convert to UTC if tz-naive
                    if ts.tzinfo is None:
                        ts = ts.tz_localize(pytz.UTC)
                    times[t] = ts.isoformat()
                except Exception:
                    # fallback: use string coercion
                    times[t] = str(latest.loc[t, 'date'])
            else:
                prices[t] = None
                times[t] = None

        return prices, times

    except Exception as e:
        logger.exception("Failed to read cached prices")
        return {t: None for t in tickers}, {t: None for t in tickers}