import os
import pandas as pd
import yfinance as yf
from datetime import datetime
import logging
import pytz

from .cache import get_cached_prices
from .alpha_vantage import get_alpha_vantage_api_key, fetch_prices_alpha_vantage


logger = logging.getLogger(__name__)


def get_current_prices(tickers, csv_path=None):
    """Fetch most recent available adjusted close prices for tickers.

    Returns a tuple: (prices_dict, fetched_at_iso, source)

    - prices_dict: mapping ticker -> price (float or None)
    - fetched_at_iso: ISO-format UTC timestamp representing the authoritative
      timestamp for the returned prices (e.g. cache record time or fetch time)
    - source: one of 'live', 'cache', or 'mixed' depending on origins
    """
    prices = {t: None for t in tickers}
    origins = {t: None for t in tickers}  # 'live' or 'cache'
    times = {t: None for t in tickers}  # ISO timestamps per-ticker

    # Attempt live fetch via yfinance
    try:
        data = yf.download(tickers=" ".join(tickers), period="5d", interval="1d", group_by='ticker', threads=True, progress=False, auto_adjust=False)

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
    except Exception:
        logger.exception("Failed to fetch current prices from yfinance")
        for t in tickers:
            prices[t] = None
            origins[t] = None

    # If any prices are missing, try Alpha Vantage as fallback
    missing_tickers = [t for t in tickers if prices.get(t) is None]
    if missing_tickers:
        av_api_key = get_alpha_vantage_api_key()
        if av_api_key:
            logger.info(f"Attempting Alpha Vantage fallback for {len(missing_tickers)} tickers")
            try:
                av_prices = fetch_prices_alpha_vantage(missing_tickers, av_api_key)
                for t in missing_tickers:
                    if av_prices.get(t) is not None:
                        prices[t] = av_prices[t]
                        origins[t] = 'alphavantage'
                        times[t] = datetime.utcnow().replace(tzinfo=pytz.UTC).isoformat()
                        logger.info(f"Got {t} from Alpha Vantage: {av_prices[t]}")
            except Exception:
                logger.exception("Failed to fetch from Alpha Vantage")
        else:
            logger.info("Alpha Vantage API key not available (set ALPHAVANTAGE_API_KEY environment variable)")

    # If any prices are still missing and we have a cache path, try cache
    if csv_path and any(p is None for p in prices.values()):
        cached_prices, cached_times = get_cached_prices(tickers, csv_path)
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
    """
    try:
        df = yf.download(tickers=" ".join(tickers), period=period, interval="1d", auto_adjust=True, progress=False)
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
    """Append a snapshot for each holding to csv_path.

    holdings: list of dicts with keys ticker, shares, cost_basis, currency (optional), account (optional)
    prices: dict ticker->price
    Writes rows: date,account,ticker,shares,cost_basis,price,current_value,portfolio_value,allocation_pct
    """
    rows = []
    # Use provided fetched_at timestamp if available (should be ISO UTC),
    # otherwise fall back to current UTC time.
    if fetched_at_iso:
        now = fetched_at_iso
    else:
        now = datetime.utcnow().isoformat()
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
        account = h.get('account', 'Default')
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

    df = pd.DataFrame(rows)
    header = not os.path.exists(csv_path)
    df.to_csv(csv_path, mode='a', header=header, index=False)
    return df
