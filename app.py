"""Streamlit dashboard for portfolio tracking (Phase 1).

Run: streamlit run app.py
"""
import os
import json
from datetime import datetime, timedelta

import pandas as pd
import streamlit as st

from portodash.data_fetch import get_current_prices, get_historical_prices, fetch_and_store_snapshot
from portodash.calculations import compute_portfolio_df
from portodash.viz import make_allocation_pie, make_30d_performance_chart


BASE_DIR = os.path.dirname(__file__)
PORTFOLIO_PATH = os.path.join(BASE_DIR, 'portfolio.json') if not os.path.exists('portfolio.json') else 'portfolio.json'
HIST_CSV = os.path.join(BASE_DIR, 'historical.csv')


def load_portfolio(path):
    with open(path, 'r') as f:
        return json.load(f)


def main():
    st.set_page_config(page_title='PortoDash', layout='wide')
    st.title('PortoDash — Portfolio Tracker')

    # Sidebar
    st.sidebar.header('Controls')
    days = st.sidebar.slider('Days for performance', min_value=7, max_value=365, value=30, step=1)
    refresh = st.sidebar.button('Refresh prices')

    # Load portfolio
    try:
        cfg = load_portfolio(PORTFOLIO_PATH)
    except Exception as e:
        st.error(f'Failed to load portfolio.json: {e}')
        return

    holdings = cfg.get('holdings', [])
    tickers = [h['ticker'] for h in holdings]

    st.sidebar.markdown(f"**Tickers:** {', '.join(tickers)}")

    # Fetch current prices on load or refresh
    st.sidebar.text('Fetching latest prices...')
    prices = get_current_prices(tickers)

    # compute portfolio data
    df = compute_portfolio_df(holdings, prices)

    # Summary KPIs
    col1, col2, col3 = st.columns(3)
    total_value = df.loc[df['ticker'] == 'TOTAL', 'current_value'].squeeze() if 'TOTAL' in df['ticker'].values else df['current_value'].sum()
    total_cost = df.loc[df['ticker'] == 'TOTAL', 'cost_total'].squeeze() if 'TOTAL' in df['ticker'].values else df['cost_total'].sum()
    total_gain = df.loc[df['ticker'] == 'TOTAL', 'gain'].squeeze() if 'TOTAL' in df['ticker'].values else df['gain'].sum()

    col1.metric('Portfolio Value', f"{total_value:,.2f}")
    col2.metric('Total Cost', f"{total_cost:,.2f}")
    col3.metric('Total Gain', f"{total_gain:,.2f}")

    st.subheader('Holdings')
    st.dataframe(df.style.format({
        'shares': '{:,.4f}',
        'cost_basis': '{:,.4f}',
        'price': '{:,.4f}',
        'current_value': '{:,.2f}',
        'cost_total': '{:,.2f}',
        'gain': '{:,.2f}',
        'allocation_pct': '{:.2%}',
        'gain_pct': '{:.2%}'
    }))

    # Allocation chart
    st.subheader('Allocation')
    pie = make_allocation_pie(df)
    st.plotly_chart(pie, use_container_width=True)

    # 30-day performance
    st.subheader(f'Performance — Last {days} days')
    hist = get_historical_prices(tickers, period=f"{days}d")
    perf_fig = make_30d_performance_chart(hist, holdings)
    st.plotly_chart(perf_fig, use_container_width=True)

    # Snapshot storage
    if st.button('Save snapshot to CSV'):
        written = fetch_and_store_snapshot(holdings, prices, HIST_CSV)
        st.success(f'Wrote {len(written)} rows to {HIST_CSV}')

    # Export historical CSV
    if os.path.exists(HIST_CSV):
        st.download_button('Download historical snapshots CSV', data=open(HIST_CSV, 'rb').read(), file_name='historical.csv')
    else:
        st.info('No historical CSV yet. Click "Save snapshot to CSV" to create one.')


if __name__ == '__main__':
    main()
