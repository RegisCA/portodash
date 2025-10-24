"""Streamlit dashboard for portfolio tracking (Phase 1).

Run: streamlit run app.py
"""
import os
import json
from datetime import datetime, timedelta
import pytz

import pandas as pd
import streamlit as st

from portodash.data_fetch import get_current_prices, get_historical_prices, fetch_and_store_snapshot
from portodash.calculations import compute_portfolio_df
from portodash.fx import get_fx_rates
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
    
    # Account filter
    holdings = cfg.get('holdings', [])
    all_accounts = sorted(set(h.get('account', 'Default') for h in holdings))
    selected_account = st.sidebar.selectbox(
        'Filter by Account',
        options=['All Accounts'] + all_accounts,
        index=0
    )
    
    refresh = st.sidebar.button('Refresh prices')

    # Load portfolio
    try:
        cfg = load_portfolio(PORTFOLIO_PATH)
    except Exception as e:
        st.error(f'Failed to load portfolio.json: {e}')
        return

    holdings = cfg.get('holdings', [])
    
    # Apply account filter
    if selected_account != 'All Accounts':
        holdings = [h for h in holdings if h.get('account', 'Default') == selected_account]
    
    tickers = [h['ticker'] for h in holdings]

    st.sidebar.markdown(f"**Tickers:** {', '.join(tickers)}")

    # Fetch current prices on load or refresh. get_current_prices now returns
    # (prices, fetched_at_iso, source) where fetched_at_iso is an ISO UTC timestamp.
    with st.sidebar:
        if refresh:
            st.text('Fetching latest prices...')
        prices, fetched_at_iso, price_source = get_current_prices(tickers, csv_path=HIST_CSV)  # Enable cache fallback
        tz = pytz.timezone('America/Toronto')  # Use Toronto for TSX market time

    # Use the authoritative fetched_at timestamp returned by get_current_prices.
    # This will reflect the cache snapshot time if cached data were used.
    try:
        fetched_dt = datetime.fromisoformat(fetched_at_iso)
        # convert to local tz for display
        fetch_time = fetched_dt.astimezone(tz).strftime("%Y-%m-%d %H:%M:%S %Z")
    except Exception:
        # Fallback: if parsing fails, use now
        fetch_time = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S %Z")

    # Show fetch time and scheduler status prominently
    st.markdown("### Portfolio Status")
    col1, col2 = st.columns(2)

    with col1:
        # Display source indicator with the timestamp
        source_label = price_source.capitalize() if price_source else 'Unknown'
        st.markdown(f"**Last Updated:** {fetch_time} ({source_label})")

    # Show scheduler status if available; prefer process check (psutil) then fall back to logs
    def _detect_scheduler_running():
        """Return (running_bool, method) where method is 'process' or 'log' or None."""
        # Try psutil first
        try:
            import psutil
            for p in psutil.process_iter(['cmdline']):
                try:
                    cmd = p.info.get('cmdline') or []
                    if any('run_scheduler.py' in str(c) for c in cmd):
                        return True, 'process'
                except Exception:
                    continue
        except Exception:
            # psutil not available; fall back to log inspection
            pass

        # Check today's scheduler log as a heuristic
        log_path = os.path.join(BASE_DIR, 'logs', f'scheduler_{datetime.now().strftime("%Y%m%d")}.log')
        try:
            if os.path.exists(log_path):
                # if log exists and was modified recently, consider scheduler running
                mtime = datetime.fromtimestamp(os.path.getmtime(log_path), tz)
                if (datetime.now(tz) - mtime).total_seconds() < 24 * 3600:
                    return True, 'log'
                return True, 'log'
        except Exception:
            pass

        return False, None

    with col2:
        # Prefer a persisted status file written by the scheduler (most reliable)
        status_file = os.path.join(BASE_DIR, 'logs', 'scheduler_status.json')
        shown = False
        if os.path.exists(status_file):
            try:
                with open(status_file, 'r') as fh:
                    status_json = json.load(fh)
                # show running state or next run
                if status_json.get('job_running'):
                    st.success('⚡ Scheduler running (job active)')
                    shown = True
                elif status_json.get('next_run'):
                    try:
                        nr = datetime.fromisoformat(status_json.get('next_run'))
                        nr_local = nr.astimezone(tz)
                        st.info(f"📅 Next scheduled update: {nr_local.strftime('%Y-%m-%d %H:%M:%S %Z')}")
                    except Exception:
                        st.info('📅 Next scheduled update available')
                    shown = True
                elif status_json.get('last_error'):
                    st.error(f"❌ Last scheduler error: {status_json.get('last_error')}")
                    shown = True
            except Exception:
                # ignore corrupted status file and fall back
                shown = False

        if not shown:
            # Fall back to process/log detection heuristic
            running, method = _detect_scheduler_running()
            if running:
                if method == 'process':
                    st.success('⚡ Scheduler process detected')
                else:
                    st.success('⚡ Scheduler log found (scheduler probably running)')
            else:
                st.warning("⚠️ Scheduler not running — start it with: python scripts/run_scheduler.py")

    # compute portfolio data; collect currencies per holding (optional field `currency`)
    currencies = {h.get('currency', 'CAD').upper() for h in holdings}
    # Request FX rates for any currencies that are not the base
    fx_rates = get_fx_rates(currencies, base='CAD') if currencies else {}

    df = compute_portfolio_df(holdings, prices, fx_rates=fx_rates, base_currency='CAD')

    # Summary KPIs
    col1, col2, col3 = st.columns(3)
    total_value = df.loc[df['ticker'] == 'TOTAL', 'current_value'].squeeze() if 'TOTAL' in df['ticker'].values else df['current_value'].sum()
    total_cost = df.loc[df['ticker'] == 'TOTAL', 'cost_total'].squeeze() if 'TOTAL' in df['ticker'].values else df['cost_total'].sum()
    total_gain = df.loc[df['ticker'] == 'TOTAL', 'gain'].squeeze() if 'TOTAL' in df['ticker'].values else df['gain'].sum()

    col1.metric('Portfolio Value', f"{total_value:,.2f}")
    col2.metric('Total Cost', f"{total_cost:,.2f}")
    col3.metric('Total Gain', f"{total_gain:,.2f}")

    st.subheader('Holdings')
    
    # Show account breakdown if viewing all accounts
    if selected_account == 'All Accounts' and 'account' in df.columns:
        st.markdown("#### By Account")
        # Group by account (excluding TOTAL row)
        accounts_df = df[df['account'] != 'TOTAL'].groupby('account').agg({
            'current_value': 'sum',
            'cost_total': 'sum',
            'gain': 'sum'
        }).reset_index()
        accounts_df['gain_pct'] = accounts_df['gain'] / accounts_df['cost_total']
        accounts_df = accounts_df.sort_values('current_value', ascending=False)
        
        st.dataframe(accounts_df.style.format({
            'current_value': '{:,.2f}',
            'cost_total': '{:,.2f}',
            'gain': '{:,.2f}',
            'gain_pct': '{:.2%}'
        }))
        
        st.markdown("#### All Holdings")
    
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
        written = fetch_and_store_snapshot(holdings, prices, HIST_CSV, fetched_at_iso=fetched_at_iso)
        st.success(f'Wrote {len(written)} rows to {HIST_CSV}')

    # Export historical CSV
    if os.path.exists(HIST_CSV):
        st.download_button('Download historical snapshots CSV', data=open(HIST_CSV, 'rb').read(), file_name='historical.csv')
    else:
        st.info('No historical CSV yet. Click "Save snapshot to CSV" to create one.')


if __name__ == '__main__':
    main()
