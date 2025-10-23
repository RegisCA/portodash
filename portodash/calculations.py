import pandas as pd
import numpy as np


def compute_portfolio_df(holdings_list, prices_dict):
    """Return a DataFrame with portfolio calculations per ticker and totals.

    holdings_list: list of dicts with keys ticker, shares, cost_basis
    prices_dict: dict ticker->price
    """
    rows = []
    for h in holdings_list:
        ticker = h.get('ticker')
        shares = float(h.get('shares', 0))
        cost_basis = float(h.get('cost_basis', 0))
        price = prices_dict.get(ticker) or 0.0
        current_value = shares * price
        cost_total = shares * cost_basis
        gain = current_value - cost_total
        gain_pct = (gain / cost_total) if cost_total != 0 else None
        rows.append({
            'ticker': ticker,
            'shares': shares,
            'cost_basis': cost_basis,
            'price': price,
            'current_value': current_value,
            'cost_total': cost_total,
            'gain': gain,
            'gain_pct': gain_pct,
        })

    df = pd.DataFrame(rows)
    if df.empty:
        return df

    portfolio_value = df['current_value'].sum()
    df['allocation_pct'] = df['current_value'] / portfolio_value
    # format numeric columns
    df = df.sort_values(by='current_value', ascending=False).reset_index(drop=True)
    # Use numeric NaN for non-applicable numeric fields to avoid formatting errors
    totals = {
        'ticker': 'TOTAL',
        'shares': np.nan,
        'cost_basis': np.nan,
        'price': np.nan,
        'current_value': portfolio_value,
        'cost_total': df['cost_total'].sum(),
        'gain': df['gain'].sum(),
        'gain_pct': np.nan,
        'allocation_pct': 1.0,
    }
    df_tot = pd.DataFrame([totals])
    return pd.concat([df, df_tot], ignore_index=True)
