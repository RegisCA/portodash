import os
import pandas as pd
import yfinance as yf
from datetime import datetime


def get_current_prices(tickers):
    """Fetch most recent available adjusted close prices for tickers.

    Returns dict ticker -> price (float) or None on failure for that ticker.
    """
    prices = {t: None for t in tickers}
    try:
        # yfinance can download multiple tickers at once
        data = yf.download(tickers=" ".join(tickers), period="5d", interval="1d", group_by='ticker', threads=True, progress=False, auto_adjust=False)

        # Handle multi-column result
        if isinstance(data.columns, pd.MultiIndex):
            for t in tickers:
                try:
                    ser = data[t]["Adj Close"].dropna()
                    prices[t] = float(ser.iloc[-1])
                except Exception:
                    prices[t] = None
        else:
            # Single ticker or simplified DF
            try:
                ser = data["Adj Close"].dropna()
                last = float(ser.iloc[-1])
                for t in tickers:
                    prices[t] = last
            except Exception:
                prices = {t: None for t in tickers}
    except Exception:
        prices = {t: None for t in tickers}

    return prices


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


def fetch_and_store_snapshot(holdings, prices, csv_path):
    """Append a snapshot for each holding to csv_path.

    holdings: list of dicts with keys ticker, shares, cost_basis
    prices: dict ticker->price
    Writes rows: date,ticker,shares,cost_basis,price,current_value
    Also writes portfolio_value (same value repeated for each row) and allocation_pct
    """
    rows = []
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
        shares = float(h.get('shares', 0))
        cost_basis = float(h.get('cost_basis', 0))
        price = prices.get(t) or 0.0
        current_value = shares * price
        allocation = (current_value / total) if total > 0 else 0.0
        rows.append({
            'date': now,
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
