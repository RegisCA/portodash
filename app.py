"""Streamlit dashboard for portfolio tracking (Phase 1).

Run: streamlit run app.py
"""
import os
import json
from datetime import datetime, timedelta
import pytz

import pandas as pd
import streamlit as st # type: ignore

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

    # Initialize session state for price caching and rate limiting
    if 'prices_cache' not in st.session_state:
        st.session_state.prices_cache = {}
    if 'last_fetch_time' not in st.session_state:
        st.session_state.last_fetch_time = None
    if 'fetched_at_iso' not in st.session_state:
        st.session_state.fetched_at_iso = None
    if 'price_source' not in st.session_state:
        st.session_state.price_source = None
    if 'rate_limited_until' not in st.session_state:
        st.session_state.rate_limited_until = None
    if 'last_error' not in st.session_state:
        st.session_state.last_error = None

    # Load portfolio first
    try:
        cfg = load_portfolio(PORTFOLIO_PATH)
    except Exception as e:
        st.error(f'Failed to load portfolio.json: {e}')
        return

    holdings = cfg.get('holdings', [])

    # Sidebar
    st.sidebar.header('Controls')
    days = st.sidebar.slider('Days for performance', min_value=7, max_value=365, value=30, step=1)
    
    # Account filter
    all_accounts = sorted(set(h.get('account', 'Default') for h in holdings))
    selected_account = st.sidebar.selectbox(
        'Filter by Account',
        options=['All Accounts'] + all_accounts,
        index=0
    )
    
    # Rate limiting: cooldown period in seconds
    COOLDOWN_SECONDS = 60
    RATE_LIMIT_EXTENDED_COOLDOWN = 3600  # 1 hour if rate limited by yfinance
    tz = pytz.timezone('America/Toronto')
    now = datetime.now(tz)
    
    # Check if we're in cooldown period or rate limited
    can_refresh = True
    cooldown_remaining = 0
    button_label = 'Refresh prices'
    
    # Check if we're still in extended rate limit period
    if st.session_state.rate_limited_until:
        if now < st.session_state.rate_limited_until:
            can_refresh = False
            remaining_secs = int((st.session_state.rate_limited_until - now).total_seconds())
            remaining_mins = remaining_secs // 60
            button_label = f'⏳ Rate limited (wait {remaining_mins}m)'
        else:
            # Rate limit period expired
            st.session_state.rate_limited_until = None
            st.session_state.last_error = None
    
    # Check normal cooldown
    if can_refresh and st.session_state.last_fetch_time:
        elapsed = (now - st.session_state.last_fetch_time).total_seconds()
        if elapsed < COOLDOWN_SECONDS:
            can_refresh = False
            cooldown_remaining = int(COOLDOWN_SECONDS - elapsed)
            button_label = f'Refresh prices (wait {cooldown_remaining}s)'
    
    # Refresh button with appropriate state
    if can_refresh:
        refresh = st.sidebar.button('Refresh prices')
    else:
        st.sidebar.button(button_label, disabled=True)
        refresh = False
    
    # Show rate limit warning if we have one
    if st.session_state.last_error:
        st.sidebar.warning(f"⚠️ {st.session_state.last_error}")
    
    # Apply account filter
    if selected_account != 'All Accounts':
        holdings = [h for h in holdings if h.get('account', 'Default') == selected_account]
    
    tickers = [h['ticker'] for h in holdings]

    st.sidebar.markdown(f"**Tickers:** {', '.join(tickers)}")

    # Fetch current prices ONLY on explicit refresh or first load with no cache
    # This prevents refetches when filters change
    # However, if we're rate-limited, skip the fetch attempt and go straight to cache
    should_fetch = (refresh or not st.session_state.prices_cache)
    
    # If rate-limited, bypass live fetch and use cache immediately
    if should_fetch and st.session_state.rate_limited_until and now < st.session_state.rate_limited_until:
        # Skip fetch, load from cache instead
        should_fetch = False
        if not st.session_state.prices_cache:
            # No session cache, try loading from CSV
            with st.sidebar:
                st.text('Loading cached prices (rate limited)...')
            try:
                from portodash.data_fetch import get_cached_prices
                cached_prices, _ = get_cached_prices(tickers, csv_path=HIST_CSV)
                if cached_prices:
                    st.session_state.prices_cache = cached_prices
                    st.session_state.price_source = 'cache'
                    # Keep existing timestamp or use a placeholder
                    if not st.session_state.fetched_at_iso:
                        st.session_state.fetched_at_iso = datetime.utcnow().replace(tzinfo=pytz.UTC).isoformat()
            except Exception as e:
                st.sidebar.error(f"Could not load cached prices: {e}")
    
    if should_fetch:
        status_placeholder = st.sidebar.empty()
        status_placeholder.info('🔄 Fetching latest prices...')
        
        try:
            prices, fetched_at_iso, price_source = get_current_prices(tickers, csv_path=HIST_CSV)
            # Update session state on success
            st.session_state.prices_cache = prices
            st.session_state.fetched_at_iso = fetched_at_iso
            st.session_state.price_source = price_source
            st.session_state.last_fetch_time = now
            # Clear any previous errors
            st.session_state.last_error = None
            st.session_state.rate_limited_until = None
            
            # Clear the fetching message
            status_placeholder.empty()
            
        except Exception as e:
            # Clear the fetching message on error too
            status_placeholder.empty()
            
            # Check if it's a rate limit error
            error_msg = str(e)
            if 'YFRateLimitError' in error_msg or 'Rate limited' in error_msg or 'Too Many Requests' in error_msg:
                # Set extended cooldown for rate limit
                st.session_state.rate_limited_until = now + timedelta(seconds=RATE_LIMIT_EXTENDED_COOLDOWN)
                st.session_state.last_error = "Yahoo Finance rate limit reached. Using cached data. Will retry in ~1 hour."
                st.sidebar.error("🚫 Rate limit reached! Using cached prices.")
            else:
                # Other error - show it but don't extend cooldown as much
                st.session_state.last_error = f"Error fetching prices: {error_msg}"
                st.sidebar.error(f"❌ {st.session_state.last_error}")
            
            # Fall back to cached data if available
            if st.session_state.prices_cache:
                prices = st.session_state.prices_cache
                fetched_at_iso = st.session_state.fetched_at_iso
                price_source = 'cache (error fallback)'
            else:
                # No cache available - create empty prices
                prices = {t: None for t in tickers}
                fetched_at_iso = datetime.utcnow().replace(tzinfo=pytz.UTC).isoformat()
                price_source = 'unavailable'
    else:
        # Use cached prices
        prices = st.session_state.prices_cache
        fetched_at_iso = st.session_state.fetched_at_iso
        price_source = st.session_state.price_source

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

    # Summary KPIs - all values in CAD
    col1, col2, col3 = st.columns(3)
    total_value = df.loc[df['ticker'] == 'TOTAL', 'current_value'].squeeze() if 'TOTAL' in df['ticker'].values else df['current_value'].sum()
    total_cost = df.loc[df['ticker'] == 'TOTAL', 'cost_total'].squeeze() if 'TOTAL' in df['ticker'].values else df['cost_total'].sum()
    total_gain = df.loc[df['ticker'] == 'TOTAL', 'gain'].squeeze() if 'TOTAL' in df['ticker'].values else df['gain'].sum()

    col1.metric('Portfolio Value (CAD)', f"${total_value:,.2f}")
    col2.metric('Total Cost (CAD)', f"${total_cost:,.2f}")
    col3.metric('Total Gain (CAD)', f"${total_gain:,.2f}")
    
    # Show FX rates and calculation methodology if multi-currency
    if fx_rates:
        st.info(f"""
        **💱 Multi-Currency Portfolio** — All values displayed in **CAD** (Canadian Dollar)
        
        **Exchange Rates Used:**  
        {' · '.join([f"1 {curr} = {rate:.4f} CAD" for curr, rate in sorted(fx_rates.items())])}
        
        *Holdings in foreign currencies are converted to CAD using the above rates.  
        Exchange rates cached for 12 hours from open.er-api.com.*
        """)

    st.subheader('Holdings')
    
    # Show account breakdown if viewing all accounts
    if selected_account == 'All Accounts' and 'account' in df.columns:
        st.markdown("#### By Account (CAD equivalent)")
        # Group by account (excluding TOTAL row)
        accounts_df = df[df['account'] != 'TOTAL'].groupby('account').agg({
            'current_value': 'sum',
            'cost_total': 'sum',
            'gain': 'sum'
        }).reset_index()
        accounts_df['gain_pct'] = accounts_df['gain'] / accounts_df['cost_total']
        accounts_df = accounts_df.sort_values('current_value', ascending=False)
        
        # Apply color formatting for gain_pct
        def color_gain_pct(val):
            if pd.isna(val) or val is None:
                return ''
            color = '#90ee90' if val > 0 else '#ffcccb' if val < 0 else ''
            return f'background-color: {color}'
        
        st.dataframe(
            accounts_df.style.format({
                'current_value': '${:,.2f}',
                'cost_total': '${:,.2f}',
                'gain': '${:,.2f}',
                'gain_pct': '{:.2%}'
            }).map(color_gain_pct, subset=['gain_pct']),
            width='stretch',
            column_config={
                'account': st.column_config.TextColumn('Account', width='medium'),
                'current_value': st.column_config.NumberColumn('Current Value', width='medium'),
                'cost_total': st.column_config.NumberColumn('Total Cost', width='medium'),
                'gain': st.column_config.NumberColumn('Gain', width='medium'),
                'gain_pct': st.column_config.NumberColumn('Gain %', width='small'),
            }
        )
        
        st.markdown("#### All Holdings (values in CAD equivalent)")
    
    # Apply color formatting for gain_pct
    def color_gain_pct(val):
        if pd.isna(val) or val is None:
            return ''
        color = '#90ee90' if val > 0 else '#ffcccb' if val < 0 else ''
        return f'background-color: {color}'
    
    # Split dataframe into holdings and total row
    df_holdings = df[df['ticker'] != 'TOTAL'].copy()
    df_total = df[df['ticker'] == 'TOTAL'].copy()
    
    # Display holdings table (sortable)
    st.dataframe(
        df_holdings.style.format({
            'shares': '{:,.4f}',
            'cost_basis': '{:,.4f}',
            'price': '${:,.4f}',
            'current_value': '${:,.2f}',
            'cost_total': '${:,.2f}',
            'gain': '${:,.2f}',
            'allocation_pct': '{:.2%}',
            'gain_pct': '{:.2%}'
        }).map(color_gain_pct, subset=['gain_pct']),
        width='stretch',
        column_config={
            'account': st.column_config.TextColumn('Account', width='medium'),
            'ticker': st.column_config.TextColumn('Ticker', width='small'),
            'currency': st.column_config.TextColumn('Currency', width='small'),
            'shares': st.column_config.NumberColumn('Shares', width='small'),
            'cost_basis': st.column_config.NumberColumn('Cost/Share', width='small'),
            'price': st.column_config.NumberColumn('Price', width='small'),
            'current_value': st.column_config.NumberColumn('Current Value', width='medium'),
            'cost_total': st.column_config.NumberColumn('Total Cost', width='medium'),
            'gain': st.column_config.NumberColumn('Gain', width='medium'),
            'gain_pct': st.column_config.NumberColumn('Gain %', width='small'),
            'allocation_pct': st.column_config.NumberColumn('Allocation %', width='small'),
        },
    )
    
    # Display total row separately (not sortable)
    st.dataframe(
        df_total.style.format({
            'shares': '{:,.4f}',
            'cost_basis': '{:,.4f}',
            'price': '${:,.4f}',
            'current_value': '${:,.2f}',
            'cost_total': '${:,.2f}',
            'gain': '${:,.2f}',
            'allocation_pct': '{:.2%}',
            'gain_pct': '{:.2%}'
        }),
        width='stretch',
        column_config={
            'account': st.column_config.TextColumn('Account', width='medium'),
            'ticker': st.column_config.TextColumn('Ticker', width='small'),
            'currency': st.column_config.TextColumn('Currency', width='small'),
            'shares': st.column_config.NumberColumn('Shares', width='small'),
            'cost_basis': st.column_config.NumberColumn('Cost/Share', width='small'),
            'price': st.column_config.NumberColumn('Price', width='small'),
            'current_value': st.column_config.NumberColumn('Current Value', width='medium'),
            'cost_total': st.column_config.NumberColumn('Total Cost', width='medium'),
            'gain': st.column_config.NumberColumn('Gain', width='medium'),
            'gain_pct': st.column_config.NumberColumn('Gain %', width='small'),
            'allocation_pct': st.column_config.NumberColumn('Allocation %', width='small'),
        },
        hide_index=True,
    )

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
