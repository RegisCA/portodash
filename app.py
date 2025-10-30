"""Streamlit dashboard for portfolio tracking (Phase 1).

Run: streamlit run app.py
"""
import os
import json
from datetime import datetime, timedelta
import pytz

import pandas as pd
import streamlit as st # type: ignore

from portodash.data_fetch import get_current_prices, fetch_and_store_snapshot
from portodash.calculations import compute_portfolio_df
from portodash.fx import get_fx_rates
from portodash.viz import make_allocation_pie, make_30d_performance_chart, make_snapshot_performance_chart


BASE_DIR = os.path.dirname(__file__)
PORTFOLIO_PATH = os.path.join(BASE_DIR, 'portfolio.json') if not os.path.exists('portfolio.json') else 'portfolio.json'
HIST_CSV = os.path.join(BASE_DIR, 'historical.csv')
FX_CSV = os.path.join(BASE_DIR, 'fx_rates.csv')


def load_portfolio(path):
    """Load portfolio from new account-centric JSON structure.
    
    Returns:
        dict with keys:
        - 'accounts': list of account metadata dicts
        - 'holdings': flat list of holdings with account metadata attached
    """
    with open(path, 'r') as f:
        data = json.load(f)
    
    # Validate new structure
    if 'accounts' not in data:
        raise ValueError(
            "Portfolio file must use new account-centric structure with 'accounts' key. "
            "See portfolio_new_format.json for the required format."
        )
    
    # Store accounts metadata
    accounts = data['accounts']
    
    # Flatten holdings and enrich with account metadata
    holdings = []
    for account in accounts:
        for holding in account.get('holdings', []):
            # Create enriched holding with account metadata
            enriched_holding = {
                'ticker': holding['ticker'],
                'shares': holding['shares'],
                'cost_basis': holding['cost_basis'],
                'currency': holding['currency'],
                # Account metadata
                'account_nickname': account['nickname'],
                'account_holder': account['holder'],
                'account_type': account['type'],
                'account_base_currency': account['base_currency']
            }
            holdings.append(enriched_holding)
    
    return {
        'accounts': accounts,
        'holdings': holdings
    }


def inject_custom_css():
    """Inject custom CSS for Wealthsimple-inspired clean design."""
    st.markdown("""
        <style>
        /* Typography enhancements */
        h1 {
            font-weight: 700 !important;
            letter-spacing: -0.02em !important;
            margin-bottom: 0.5rem !important;
        }
        
        h2, h3 {
            font-weight: 600 !important;
            letter-spacing: -0.01em !important;
            margin-top: 2rem !important;
        }
        
        /* Card-style containers */
        .stContainer > div {
            background-color: #F7F9FA;
            border-radius: 12px;
            padding: 1.5rem;
            border: 1px solid #E8EBED;
        }
        
        /* Metric styling - larger, more prominent */
        [data-testid="stMetricValue"] {
            font-size: 2rem !important;
            font-weight: 700 !important;
        }
        
        [data-testid="stMetricLabel"] {
            font-size: 0.875rem !important;
            font-weight: 500 !important;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: #6B7280 !important;
        }
        
        /* Button styling - more prominent */
        .stButton > button {
            border-radius: 8px !important;
            font-weight: 600 !important;
            padding: 0.5rem 1.5rem !important;
            transition: all 0.2s ease !important;
            border: 1px solid #E8EBED !important;
        }
        
        .stButton > button:hover {
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08) !important;
        }
        
        .stButton > button[kind="primary"] {
            background-color: #00D46A !important;
            border: none !important;
            color: white !important;
        }
        
        .stButton > button[kind="primary"]:hover {
            background-color: #00BD5E !important;
        }
        
        /* Dataframe styling */
        [data-testid="stDataFrame"] {
            border-radius: 8px;
            overflow: hidden;
        }
        
        /* Info/warning boxes */
        .stAlert {
            border-radius: 8px !important;
            border-left: 4px solid #00D46A !important;
        }
        
        /* Sidebar styling */
        [data-testid="stSidebar"] {
            background-color: #F7F9FA;
            border-right: 1px solid #E8EBED;
        }
        
        /* Status badges */
        .status-badge {
            display: inline-block;
            padding: 0.25rem 0.75rem;
            border-radius: 12px;
            font-size: 0.875rem;
            font-weight: 600;
            margin-left: 0.5rem;
        }
        
        .status-live {
            background-color: #D1FAE5;
            color: #065F46;
        }
        
        .status-cache {
            background-color: #FEF3C7;
            color: #92400E;
        }
        
        .status-mixed {
            background-color: #DBEAFE;
            color: #1E40AF;
        }
        
        /* Reduce padding for tighter layout */
        .block-container {
            padding-top: 2rem !important;
            padding-bottom: 2rem !important;
        }
        
        /* Chart container styling */
        .js-plotly-plot {
            border-radius: 8px;
            overflow: hidden;
        }
        </style>
    """, unsafe_allow_html=True)


def main():
    st.set_page_config(page_title='PortoDash', layout='wide', page_icon='📊')
    inject_custom_css()
    
    st.title('📊 PortoDash')
    st.caption('Multi-currency portfolio tracker with FX impact analysis')

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
    if 'fetch_in_progress' not in st.session_state:
        st.session_state.fetch_in_progress = False

    # Load portfolio first
    try:
        cfg = load_portfolio(PORTFOLIO_PATH)
    except Exception as e:
        st.error(f'Failed to load portfolio.json: {e}')
        return

    holdings = cfg.get('holdings', [])
    accounts = cfg.get('accounts', [])

    # Sidebar
    with st.sidebar:
        st.markdown("## ⚙️ Controls")
        st.markdown("---")
        
        st.markdown("### 📅 Time Range")
        days = st.slider('Performance chart period', min_value=7, max_value=365, value=30, step=1, help='Number of days to display in performance chart')
        
        # Account filters - filter by nickname, holder, and/or account type
        st.markdown("---")
        st.markdown('### 🔍 Filters')
    
    # Extract unique values for each filter dimension
    all_nicknames = sorted(set(acc['nickname'] for acc in accounts))
    all_holders = sorted(set(acc['holder'] for acc in accounts))
    all_types = sorted(set(acc['type'] for acc in accounts))
    
    # Build account display map for showing details
    account_display_map = {}
    for account in accounts:
        nickname = account['nickname']
        account_display_map[nickname] = f"{account['type']} - {account['holder']}"
    
    with st.sidebar:
        # Filter 1: Account nickname (with type and holder in display)
        selected_nicknames = st.multiselect(
            '📁 Account Name',
            options=all_nicknames,
            default=all_nicknames,
            format_func=lambda x: f"{x} ({account_display_map[x]})",
            help='Filter by specific account names'
        )
        
        # Filter 2: Account holder
        selected_holders = st.multiselect(
            '👤 Account Holder',
            options=all_holders,
            default=all_holders,
            help='Filter by account holder'
        )
        
        # Filter 3: Account type
        selected_types = st.multiselect(
            '🏦 Account Type',
            options=all_types,
            default=all_types,
            help='Filter by account type (TFSA, RRSP, etc.)'
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
    
    # Check normal cooldown - only enforce if a fetch actually happened
    # (not just because time passed since last fetch during unrelated reruns)
    if can_refresh and st.session_state.last_fetch_time and st.session_state.fetch_in_progress:
        elapsed = (now - st.session_state.last_fetch_time).total_seconds()
        if elapsed < COOLDOWN_SECONDS:
            can_refresh = False
            cooldown_remaining = int(COOLDOWN_SECONDS - elapsed)
            button_label = f'Refresh prices (wait {cooldown_remaining}s)'
        else:
            # Cooldown period expired, clear the flag
            st.session_state.fetch_in_progress = False
    
    # Refresh button with appropriate state
    with st.sidebar:
        if can_refresh:
            refresh = st.button('🔄 Refresh Prices', use_container_width=True, type='primary')
        else:
            st.button(button_label, disabled=True, use_container_width=True)
            refresh = False
        
        # Show rate limit warning if we have one
        if st.session_state.last_error:
            st.warning(f"⚠️ {st.session_state.last_error}")
    
        st.markdown("---")
        st.markdown("### 🔄 Data Refresh")
    
    # Get ALL tickers before filtering (needed for price fetching)
    all_tickers = list(set(h['ticker'] for h in holdings))
    
    # Apply account filters - holdings must match ALL selected criteria (AND logic)
    # Filter by nickname, holder, and type
    if selected_nicknames or selected_holders or selected_types:
        holdings = [
            h for h in holdings
            if (h.get('account_nickname') in selected_nicknames or not selected_nicknames)
            and (h.get('account_holder') in selected_holders or not selected_holders)
            and (h.get('account_type') in selected_types or not selected_types)
        ]
    # If all filters empty, show empty portfolio (user deselected everything)
    
    tickers = [h['ticker'] for h in holdings]

    with st.sidebar:
        st.caption(f"**Tracking:** {len(tickers)} tickers")
        if len(tickers) <= 10:
            st.caption(f"_{', '.join(tickers)}_")

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
                cached_prices, _ = get_cached_prices(all_tickers, csv_path=HIST_CSV)
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
        
        # Mark that a fetch is in progress for cooldown tracking
        st.session_state.fetch_in_progress = True
        
        try:
            prices, fetched_at_iso, price_source = get_current_prices(all_tickers, csv_path=HIST_CSV)
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
                prices = {t: None for t in all_tickers}
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
    st.markdown("---")
    st.markdown("### 📊 Portfolio Status")
    col1, col2 = st.columns(2)

    with col1:
        # Display source indicator with styled badge
        source_label = price_source.capitalize() if price_source else 'Unknown'
        badge_class = f"status-{price_source}" if price_source in ['live', 'cache', 'mixed'] else 'status-cache'
        st.markdown(f"""
            **Last Updated:** {fetch_time}  
            <span class="{badge_class} status-badge">{source_label}</span>
        """, unsafe_allow_html=True)

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
                        # Check if next_run is in the past (stale status file)
                        if nr_local < datetime.now(tz):
                            # Status file is stale - scheduler probably not running
                            st.warning(f"⚠️ Scheduler status outdated (last update: {nr_local.strftime('%Y-%m-%d %H:%M')}). Scheduler may not be running.")
                        else:
                            st.info(f"📅 Next scheduled update: {nr_local.strftime('%Y-%m-%d %H:%M:%S %Z')}")
                        shown = True
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

    # Check if we have any data to display
    if df.empty or len(holdings) == 0:
        st.warning("📭 No holdings to display with current filter selections. Please adjust your filters.")
        return

    # Summary KPIs - all values in CAD
    st.markdown("---")
    st.markdown("### 💰 Portfolio Overview")
    
    col1, col2, col3 = st.columns(3)
    total_value = df.loc[df['ticker'] == 'TOTAL', 'current_value'].squeeze() if 'TOTAL' in df['ticker'].values else df['current_value'].sum()
    total_cost = df.loc[df['ticker'] == 'TOTAL', 'cost_total'].squeeze() if 'TOTAL' in df['ticker'].values else df['cost_total'].sum()
    total_gain = df.loc[df['ticker'] == 'TOTAL', 'gain'].squeeze() if 'TOTAL' in df['ticker'].values else df['gain'].sum()
    
    gain_pct = (total_gain / total_cost * 100) if total_cost != 0 else 0

    col1.metric('Portfolio Value', f"${total_value:,.0f}", help='Total value in CAD')
    col2.metric('Total Cost', f"${total_cost:,.0f}", help='Total cost basis in CAD')
    col3.metric('Total Gain', f"${total_gain:,.0f}", delta=f"{gain_pct:.1f}%", help='Unrealized gain/loss in CAD')
    
    # Show FX rates and calculation methodology if multi-currency
    if fx_rates:
        with st.expander("💱 Multi-Currency Details", expanded=False):
            st.markdown("""
            All values displayed in **CAD** (Canadian Dollar)
            
            **Exchange Rates:**
            """)
            for curr, rate in sorted(fx_rates.items()):
                st.markdown(f"- 1 {curr} = **{rate:.4f}** CAD")
            st.caption("_Exchange rates cached for 12 hours from open.er-api.com_")

    st.markdown("---")
    st.markdown("### 📈 Holdings")
    
    # Show account breakdown if viewing multiple accounts (based on filtered results)
    # Count unique account nicknames in the filtered holdings
    unique_accounts = set(h.get('account_nickname') for h in holdings if h.get('account_nickname'))
    if len(unique_accounts) > 1 and 'account' in df.columns:
        st.markdown("#### 📁 By Account")
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
        
        st.markdown("#### 📊 All Holdings")
    
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
    st.markdown("---")
    st.markdown("### 🎯 Allocation")
    pie = make_allocation_pie(df)
    st.plotly_chart(pie, use_container_width=True)

    # Performance chart from snapshots
    st.markdown("---")
    st.markdown(f"### 📉 Performance — Last {days} Days")
    
    # Use snapshot-based chart (from historical.csv)
    if os.path.exists(HIST_CSV):
        perf_fig = make_snapshot_performance_chart(HIST_CSV, days=days, fx_csv_path=FX_CSV)
        st.plotly_chart(perf_fig, use_container_width=True)
    else:
        st.info('📊 No historical snapshots yet. Save snapshots to see performance over time.')

    # Snapshot storage
    st.markdown("---")
    st.markdown("### 💾 Data Management")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        if st.button('📸 Update daily snapshot', use_container_width=True, help='Save current prices to historical.csv'):
            written = fetch_and_store_snapshot(holdings, prices, HIST_CSV, fetched_at_iso=fetched_at_iso)
            st.success(f'✅ Updated today\'s snapshot ({len(written)} holdings)')
    
    with col2:
        # Export historical CSV
        if os.path.exists(HIST_CSV):
            st.download_button(
                '📥 Download snapshots CSV', 
                data=open(HIST_CSV, 'rb').read(), 
                file_name='historical.csv',
                use_container_width=True,
                help='Export all historical snapshots'
            )
        else:
            st.info('💡 No historical data yet. Click "Update daily snapshot" to begin tracking.')


if __name__ == '__main__':
    main()
