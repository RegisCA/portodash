import os
import pandas as pd
import yfinance as yf
from datetime import datetime
import logging
import pytz

from .cache import get_cached_prices


logger = logging.getLogger(__name__)


def get_current_prices(tickers, csv_path=None, cache_max_age_hours=72):
    """Fetch most recent available adjusted close prices for tickers.

    Returns a tuple: (prices_dict, fetched_at_iso, source)

    - prices_dict: mapping ticker -> price (float or None)
    - fetched_at_iso: ISO-format UTC timestamp representing the authoritative
      timestamp for the returned prices (e.g. cache record time or fetch time)
    - source: one of 'live', 'cache', or 'mixed' depending on origins
    
    yfinance Best Practices Applied:
    - threads=True: Enables parallel fetching (defaults to 2x CPU cores)
    - timeout=30: Extended timeout to reduce transient failures
    - period="5d": Short period to minimize data transfer and processing
    - progress=False: Disables progress bar for cleaner logs
    - YFRateLimitError detection: Gracefully falls back to cache on rate limits
    
    Note: yfinance has no official rate limits as it scrapes Yahoo Finance.
    Rate limiting is Yahoo's protection mechanism and varies unpredictably.
    Each ticker requires a separate HTTP request (no batch API exists).
    
    Cache fallback: If yfinance fails, cached prices up to cache_max_age_hours old
    (default 72 hours) are used. This ensures data availability during rate limits.
    """
    prices = {t: None for t in tickers}
    origins = {t: None for t in tickers}  # 'live' or 'cache'
    times = {t: None for t in tickers}  # ISO timestamps per-ticker

    # Import YFRateLimitError for detection (do this at function level)
    try:
        from yfinance.exceptions import YFRateLimitError
    except ImportError:
        # Older versions of yfinance don't have this exception
        YFRateLimitError = None

    # Attempt live fetch via yfinance with optimized parameters
    try:
        
        data = yf.download(
            tickers=" ".join(tickers), 
            period="5d", 
            interval="1d", 
            group_by='ticker', 
            threads=True,  # Enable parallel fetching
            progress=False, 
            auto_adjust=False,
            timeout=30  # Extended timeout (default is 10s)
        )

        if isinstance(data.columns, pd.MultiIndex):
            for t in tickers:
                try:
                    ser = data[t]["Adj Close"].dropna()
                    prices[t] = float(ser.iloc[-1])
                    origins[t] = 'live'
                    times[t] = datetime.utcnow().replace(tzinfo=pytz.UTC).isoformat()
                except Exception:
                    prices[t] = None
                    origins[t] = None
        else:
            # single ticker or simplified DF
            try:
                ser = data["Adj Close"].dropna()
                last = float(ser.iloc[-1])
                for t in tickers:
                    prices[t] = last
                    origins[t] = 'live'
                    times[t] = datetime.utcnow().replace(tzinfo=pytz.UTC).isoformat()
            except Exception:
                for t in tickers:
                    prices[t] = None
                    origins[t] = None
    except Exception as e:
        # Check if it's a rate limit error
        is_rate_limit = False
        if YFRateLimitError and isinstance(e, YFRateLimitError):
            is_rate_limit = True
            logger.warning("Yahoo Finance rate limit detected (YFRateLimitError). Falling back to cache.")
        elif "429" in str(e) or "Too Many Requests" in str(e) or "Rate limited" in str(e):
            is_rate_limit = True
            logger.warning(f"Yahoo Finance rate limit detected: {str(e)[:200]}. Falling back to cache.")
        
        if is_rate_limit:
            # Don't log full exception for rate limits, it's expected
            logger.info("Rate limit hit - will use cached data if available")
        else:
            # Log full exception for other errors
            logger.exception("Failed to fetch current prices from yfinance")
        
        for t in tickers:
            prices[t] = None
            origins[t] = None

    # If any prices are missing and we have a cache path, try cache
    if csv_path and any(p is None for p in prices.values()):
        cached_prices, cached_times = get_cached_prices(tickers, csv_path, max_age_hours=cache_max_age_hours)
        for t in tickers:
            if prices.get(t) is None and cached_prices.get(t) is not None:
                prices[t] = cached_prices[t]
                origins[t] = 'cache'
                times[t] = cached_times.get(t)
                logger.info(f"Using cached price for {t}: {cached_prices[t]} (ts={cached_times.get(t)})")

    # Determine authoritative fetched_at as the newest timestamp among returned data
    fetched_datetimes = []
    for t in tickers:
        ts = times.get(t)
        if ts:
            try:
                # parse ISO timestamp
                dt = pd.to_datetime(ts)
                if dt.tzinfo is None:
                    dt = dt.tz_localize(pytz.UTC)
                fetched_datetimes.append(dt)
            except Exception:
                continue

    if fetched_datetimes:
        overall = max(fetched_datetimes)
        fetched_at_iso = overall.tz_convert(pytz.UTC).isoformat()
    else:
        # no timestamps available: use now UTC
        fetched_at_iso = datetime.utcnow().replace(tzinfo=pytz.UTC).isoformat()

    # Source: 'live' if all live, 'cache' if all cache, else 'mixed'
    uniq = set(o for o in origins.values() if o is not None)
    if len(uniq) == 1:
        source = list(uniq)[0]
    elif len(uniq) == 0:
        source = 'unknown'
    else:
        source = 'mixed'

    return prices, fetched_at_iso, source


def get_historical_prices(tickers, period="30d"):
    """Return DataFrame of adjusted close prices with dates as index and columns as tickers.

    period examples: '30d', '90d', '1y'
    
    Optimized for yfinance:
    - threads=False: Historical data fetches are already optimized by Yahoo
    - progress=False: Cleaner output
    - timeout=30: Extended timeout for larger datasets
    """
    try:
        df = yf.download(
            tickers=" ".join(tickers), 
            period=period, 
            interval="1d", 
            auto_adjust=True, 
            progress=False,
            threads=False,  # Historical fetches don't benefit from threading
            timeout=30
        )
        # If multi-index columns (multiple tickers)
        if isinstance(df.columns, pd.MultiIndex):
            adj = df['Adj Close']
            # Ensure all requested tickers are columns
            adj = adj.reindex(columns=tickers)
            return adj.dropna(how='all')
        else:
            # single ticker -> series
            ser = df['Adj Close']
            return ser.to_frame(name=tickers[0])
    except Exception:
        # return empty df on failure
        return pd.DataFrame()


def fetch_and_store_snapshot(holdings, prices, csv_path, fetched_at_iso=None):
    """Update or append a daily snapshot for each holding to csv_path.
    
    If a snapshot already exists for today (same date), it will be replaced.
    This prevents duplicate snapshots for the same day.

    holdings: list of dicts with keys ticker, shares, cost_basis, account_nickname (or legacy 'account')
    prices: dict ticker->price
    Writes rows: date,account,ticker,shares,cost_basis,price,current_value,portfolio_value,allocation_pct
    Note: 'account' column in CSV contains the account_nickname value for clarity
    """
    rows = []
    # Use provided fetched_at timestamp if available (should be ISO UTC),
    # otherwise fall back to current UTC time.
    if fetched_at_iso:
        now = fetched_at_iso
    else:
        now = datetime.utcnow().isoformat()
    
    # Parse the timestamp to get the date portion
    snapshot_date = pd.to_datetime(now).normalize()
    
    # calculate current values
    total = 0.0
    for h in holdings:
        t = h.get('ticker')
        shares = float(h.get('shares', 0))
        price = prices.get(t) or 0.0
        val = shares * price
        total += val

    for h in holdings:
        t = h.get('ticker')
        # Use account_nickname (new format) with fallback to old 'account' field
        account = h.get('account_nickname') or h.get('account', 'Default')
        shares = float(h.get('shares', 0))
        cost_basis = float(h.get('cost_basis', 0))
        price = prices.get(t) or 0.0
        current_value = shares * price
        allocation = (current_value / total) if total > 0 else 0.0
        rows.append({
            'date': now,
            'account': account,
            'ticker': t,
            'shares': shares,
            'cost_basis': cost_basis,
            'price': price,
            'current_value': current_value,
            'portfolio_value': total,
            'allocation_pct': allocation,
        })

    new_df = pd.DataFrame(rows)
    
    # If CSV exists, remove any existing snapshots for the same date
    if os.path.exists(csv_path):
        existing_df = pd.read_csv(csv_path)
        existing_df['date'] = pd.to_datetime(existing_df['date'], format='ISO8601')
        
        # Ensure both dates are timezone-aware for comparison
        if existing_df['date'].dt.tz is None:
            existing_df['date'] = existing_df['date'].dt.tz_localize('UTC')
        if snapshot_date.tz is None:
            snapshot_date = snapshot_date.tz_localize('UTC')
        
        # Filter out snapshots from the same date (normalized to day)
        existing_df = existing_df[existing_df['date'].dt.normalize() != snapshot_date]
        
        # Convert new_df dates to datetime with timezone for consistency
        new_df['date'] = pd.to_datetime(new_df['date'])
        if new_df['date'].dt.tz is None:
            new_df['date'] = new_df['date'].dt.tz_localize('UTC')
        
        # Append new snapshot
        combined_df = pd.concat([existing_df, new_df], ignore_index=True)
        combined_df.to_csv(csv_path, index=False)
    else:
        # First time - just write the new snapshot
        new_df.to_csv(csv_path, index=False)
    
    return new_df
