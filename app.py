"""Streamlit dashboard for portfolio tracking (Phase 1).

Run: streamlit run app.py
"""
import os
import json
from datetime import datetime, timedelta
import pytz

import pandas as pd
import streamlit as st  # type: ignore

from portodash.data_fetch import get_current_prices, fetch_and_store_snapshot
from portodash.calculations import compute_portfolio_df
from portodash.fx import get_fx_rates
from portodash.viz import make_allocation_pie, make_30d_performance_chart, make_snapshot_performance_chart
from portodash.fund_names import get_fund_names, format_ticker_with_name
from portodash.theme import (
    inject_modern_fintech_css,
    inject_typography_css,
    inject_accessibility_css,
    render_metric_card,
    render_metric_grid,
    render_page_title,
    render_section_header,
    render_subsection_header,
    render_sidebar_subtitle,
    render_sidebar_title,
    get_section_label,
)


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


def main():
    st.set_page_config(page_title='PortoDash', layout='wide')
    # Inject CSS for modern styling and accessibility
    inject_modern_fintech_css()
    inject_typography_css()
    inject_accessibility_css()

    # Skip link for screen readers
    from portodash.theme import render_skip_link
    st.markdown(render_skip_link(), unsafe_allow_html=True)

    st.markdown(render_page_title('PortoDash'), unsafe_allow_html=True)
    st.caption('Real-time multi-currency overview with transparent FX attribution.')
    
    # Main content landmark for skip link
    st.markdown('<div id="main-content"></div>', unsafe_allow_html=True)

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
        st.error(f'Could not load the portfolio configuration: {e}')
        return

    holdings = cfg.get('holdings', [])
    accounts = cfg.get('accounts', [])

    # Sidebar
    with st.sidebar:
        st.markdown(render_sidebar_title(get_section_label("analytics")), unsafe_allow_html=True)
        st.markdown("<hr class='sidebar-divider' />", unsafe_allow_html=True)

        st.markdown(render_sidebar_subtitle(get_section_label("date")), unsafe_allow_html=True)
        
        # Date range selector with radio buttons for presets and custom option
        st.markdown('<div aria-label="Performance period selector: Choose a preset or custom date range for the performance chart">', unsafe_allow_html=True)
        
        range_option = st.radio(
            'Performance chart period',
            options=['Last day', 'Last 7 days', 'Last 30 days', 'Custom'],
            index=2,  # Default to 30 days
            key='range_preset',
            label_visibility='collapsed'
        )
        
        # Map selection to days value
        if range_option == 'Last day':
            days = 1
        elif range_option == 'Last 7 days':
            days = 7
        elif range_option == 'Last 30 days':
            days = 30
        else:  # Custom
            days = st.slider(
                'Days',
                min_value=1,
                max_value=30,
                value=30,
                step=1,
                help='Select a custom date range',
                key='custom_days_slider',
                label_visibility='collapsed'
            )
        
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown("<hr class='sidebar-divider' />", unsafe_allow_html=True)
        st.markdown(render_sidebar_title(get_section_label("filter")), unsafe_allow_html=True)
    
    # Extract unique values for each filter dimension
    all_nicknames = sorted(set(acc['nickname'] for acc in accounts))
    all_holders = sorted(set(acc['holder'] for acc in accounts))
    all_types = sorted(set(acc['type'] for acc in accounts))
    
    # Build account display map for showing details
    account_display_map = {}
    for account in accounts:
        nickname = account['nickname']
        account_display_map[nickname] = f"{account['type']} - {account['holder']}"
    
    # Initialize session state for filter selections (using widget keys directly)
    if 'filter_nicknames' not in st.session_state:
        st.session_state.filter_nicknames = all_nicknames
    if 'filter_holders' not in st.session_state:
        st.session_state.filter_holders = all_holders
    if 'filter_types' not in st.session_state:
        st.session_state.filter_types = all_types
    
    with st.sidebar:
        # Reset all filters button at the top for visibility
        st.markdown('<div aria-label="Reset all portfolio filters button: Click to clear all account, holder, and type filters">', unsafe_allow_html=True)
        if st.button('Reset All Filters', width='stretch', key='reset_filters_btn'):
            # Update session state to all options
            st.session_state.filter_nicknames = all_nicknames
            st.session_state.filter_holders = all_holders
            st.session_state.filter_types = all_types
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Account filter with count badge
        with st.expander(f"**Accounts** ({len(all_nicknames)})", expanded=True):
            st.markdown('<div aria-label="Account filter: Select one or more accounts to filter the portfolio view">', unsafe_allow_html=True)
            selected_nicknames = st.multiselect(
                "Select accounts",
                options=all_nicknames,
                format_func=lambda x: f"{x} — {account_display_map[x]}",
                help='Filter by specific account names',
                key='filter_nicknames',
                label_visibility='collapsed',
            )
            st.markdown('</div>', unsafe_allow_html=True)

        # Holder filter with count badge
        with st.expander(f"**Holders** ({len(all_holders)})", expanded=False):
            st.markdown('<div aria-label="Holder filter: Select one or more account holders to filter the portfolio view">', unsafe_allow_html=True)
            selected_holders = st.multiselect(
                "Select holders",
                options=all_holders,
                help='Filter by account holder',
                key='filter_holders',
                label_visibility='collapsed',
            )
            st.markdown('</div>', unsafe_allow_html=True)

        # Type filter with count badge
        with st.expander(f"**Account Types** ({len(all_types)})", expanded=False):
            st.markdown('<div aria-label="Account type filter: Select one or more account types (TFSA, RRSP, etc.) to filter the portfolio view">', unsafe_allow_html=True)
            selected_types = st.multiselect(
                "Select types",
                options=all_types,
                help='Filter by account type (TFSA, RRSP, etc.)',
                key='filter_types',
                label_visibility='collapsed',
            )
            st.markdown('</div>', unsafe_allow_html=True)
    
    # Rate limiting: cooldown period in seconds
    COOLDOWN_SECONDS = 60
    RATE_LIMIT_EXTENDED_COOLDOWN = 3600  # 1 hour if rate limited by yfinance
    tz = pytz.timezone('America/Toronto')
    now = datetime.now(tz)
    
    # Check if we're in cooldown period or rate limited
    can_refresh = True
    
    # Check if we're still in extended rate limit period
    if st.session_state.rate_limited_until:
        if now < st.session_state.rate_limited_until:
            can_refresh = False
        else:
            # Rate limit period expired
            st.session_state.rate_limited_until = None
            st.session_state.last_error = None
    
    # Check normal cooldown - only enforce if a fetch actually happened
    if can_refresh and st.session_state.last_fetch_time and st.session_state.fetch_in_progress:
        elapsed = (now - st.session_state.last_fetch_time).total_seconds()
        if elapsed < COOLDOWN_SECONDS:
            can_refresh = False
        else:
            # Cooldown period expired, clear the flag
            st.session_state.fetch_in_progress = False
    
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

    # Fetch current prices ONLY on first load with no cache
    # Manual refresh happens later in Data Management section
    should_fetch = not st.session_state.prices_cache
    
    # If rate-limited, bypass live fetch and use cache immediately
    if should_fetch and st.session_state.rate_limited_until and now < st.session_state.rate_limited_until:
        # Skip fetch, load from cache instead
        should_fetch = False
        if not st.session_state.prices_cache:
            # No session cache, try loading from CSV
            with st.sidebar:
                st.info('Loading cached prices while the Yahoo Finance limit clears...')
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
        # Show loading state in sidebar
        with st.sidebar:
            with st.spinner('Fetching latest prices...'):
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
                    
                    # Force rerun to show updated state
                    st.rerun()
                    
                except Exception as e:
                    # Check if it's a rate limit error
                    error_msg = str(e)
                    if 'YFRateLimitError' in error_msg or 'Rate limited' in error_msg or 'Too Many Requests' in error_msg:
                        # Set extended cooldown for rate limit
                        st.session_state.rate_limited_until = now + timedelta(seconds=RATE_LIMIT_EXTENDED_COOLDOWN)
                        st.session_state.last_error = (
                            "Rate limit reached. Using cached prices. Retry available in 1 hour."
                        )
                    else:
                        # Other error - show it but don't extend cooldown as much
                        st.session_state.last_error = f"Fetch failed: {error_msg}"
                    
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
                    
                    # Force rerun to show error state
                    st.rerun()
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
    st.markdown(render_section_header('Portfolio Status'), unsafe_allow_html=True)
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
                return False, 'log'
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
                    st.success('Scheduler process running')
                    shown = True
                elif status_json.get('next_run'):
                    try:
                        nr = datetime.fromisoformat(status_json.get('next_run'))
                        nr_local = nr.astimezone(tz)
                        if nr_local < datetime.now(tz):
                            st.warning(
                                f"Scheduler status is older than expected (last update {nr_local.strftime('%Y-%m-%d %H:%M')}). Verify the scheduler is running."
                            )
                        else:
                            st.info(f"Next scheduled update {nr_local.strftime('%Y-%m-%d %H:%M:%S %Z')}")
                        shown = True
                    except Exception:
                        st.info('Next scheduled update pending confirmation')
                        shown = True
                elif status_json.get('last_error'):
                    st.error(f"Most recent scheduler error: {status_json.get('last_error')}")
                    shown = True
            except Exception:
                # ignore corrupted status file and fall back
                shown = False

        if not shown:
            # Fall back to process/log detection heuristic
            running, method = _detect_scheduler_running()
            if running:
                if method == 'process':
                    st.success('Scheduler process detected via system check')
                else:
                    st.success('Scheduler log recently updated (scheduler healthy)')
            else:
                st.warning("Scheduler not detected. Run `python scripts/run_scheduler.py` to resume automated updates.")

    # compute portfolio data; collect currencies per holding (optional field `currency`)
    currencies = {h.get('currency', 'CAD').upper() for h in holdings}
    # Request FX rates for any currencies that are not the base
    fx_rates = get_fx_rates(currencies, base='CAD') if currencies else {}

    df = compute_portfolio_df(holdings, prices, fx_rates=fx_rates, base_currency='CAD')

    # Check if we have any data to display
    if df.empty or len(holdings) == 0:
        st.warning("No holdings match the current filters. Adjust your selections to view positions.")
        return

    # Determine if filters are active by checking session state
    # Filters are active if user has selected fewer items than total available
    filters_active = (
        len(st.session_state.get('filter_nicknames', [])) < len(all_nicknames) or
        len(st.session_state.get('filter_holders', [])) < len(all_holders) or
        len(st.session_state.get('filter_types', [])) < len(all_types)
    )
    
    # Summary KPIs - all values in CAD
    # Use context-aware headers: "Portfolio" when viewing all, "Overview" when filtered
    overview_header = 'Overview' if filters_active else 'Portfolio Overview'
    st.markdown(render_section_header(overview_header), unsafe_allow_html=True)
    
    total_value = df.loc[df['ticker'] == 'TOTAL', 'current_value'].squeeze() if 'TOTAL' in df['ticker'].values else df['current_value'].sum()
    total_cost = df.loc[df['ticker'] == 'TOTAL', 'cost_total'].squeeze() if 'TOTAL' in df['ticker'].values else df['cost_total'].sum()
    total_gain = df.loc[df['ticker'] == 'TOTAL', 'gain'].squeeze() if 'TOTAL' in df['ticker'].values else df['gain'].sum()
    
    gain_pct = (total_gain / total_cost * 100) if total_cost != 0 else 0

    metrics_html = render_metric_grid(
        render_metric_card('Portfolio Value', total_value, help_text='Total value in CAD'),
        render_metric_card('Total Cost', total_cost, help_text='Total cost basis in CAD'),
        render_metric_card(
            'Total Gain',
            total_gain,
            delta=gain_pct,
            delta_is_percent=True,
            delta_precision=1,
            help_text='Unrealized gain/loss in CAD',
            delta_label='vs cost',
        ),
    )
    st.markdown(metrics_html, unsafe_allow_html=True)
    
    # Show FX rates and calculation methodology if multi-currency
    if fx_rates:
        with st.expander("Multi-Currency Details", expanded=False):
            st.markdown(render_subsection_header('Exchange Rates'), unsafe_allow_html=True)
            st.markdown(
                "**Reporting currency:** CAD (Canadian Dollar)\n\n**Current exchange rates:**"
            )
            for curr, rate in sorted(fx_rates.items()):
                st.markdown(f"- 1 {curr} = **{rate:.4f}** CAD")
            st.caption('Exchange rates cache for up to 12 hours (open.er-api.com).')

    # Calculate portfolio insights and metrics
    # Split dataframe into holdings and remove the aggregate TOTAL row
    df_holdings = df[df['ticker'] != 'TOTAL'].copy()
    
    if not df_holdings.empty:
        positions_count = len(df_holdings)
        positive_positions = int((df_holdings['gain'] > 0).sum())
        positive_ratio = (positive_positions / positions_count * 100) if positions_count else 0

        currency_series = df_holdings['currency'].fillna('CAD').str.upper()
        portfolio_value = float(df_holdings['current_value'].sum())
        foreign_mask = currency_series != 'CAD'
        foreign_value = float(df_holdings.loc[foreign_mask, 'current_value'].sum()) if portfolio_value else 0
        fx_exposure_pct = (foreign_value / portfolio_value * 100) if portfolio_value else 0

        top_fx_label = None
        top_fx_pct = 0.0
        if foreign_mask.any() and portfolio_value:
            foreign_df = df_holdings.loc[foreign_mask].copy()
            foreign_df['currency_upper'] = currency_series[foreign_mask]
            fx_by_currency = foreign_df.groupby('currency_upper')['current_value'].sum().sort_values(ascending=False)
            if not fx_by_currency.empty:
                top_fx_label = fx_by_currency.index[0]
                top_fx_pct = fx_by_currency.iloc[0] / portfolio_value * 100

        top_holding = None
        if 'allocation_pct' in df_holdings.columns and not df_holdings['allocation_pct'].isna().all():
            top_holding = df_holdings.loc[df_holdings['allocation_pct'].idxmax()]

        avg_gain_pct = float(df_holdings['gain_pct'].mean()) * 100 if 'gain_pct' in df_holdings.columns else 0

        summary_cards = [
            render_metric_card(
                'Positions',
                positions_count,
                value_is_currency=False,
                help_text='Holdings visible after filters',
                delta=positive_ratio,
                delta_is_percent=True,
                delta_precision=1,
                delta_label='showing gains',
            )
        ]

        if top_holding is not None:
            summary_cards.append(
                render_metric_card(
                    'Top Holding',
                    str(top_holding.get('ticker', '–')),
                    value_is_currency=False,
                    delta=float(top_holding.get('allocation_pct', 0) * 100),
                    delta_is_percent=True,
                    delta_precision=1,
                    delta_label='of portfolio',
                    help_text=f"{top_holding.get('account', 'Account')} • {top_holding.get('currency', 'CAD')}",
                )
            )

        fx_help = 'All holdings in CAD'
        if fx_exposure_pct > 0:
            fx_detail = f"{top_fx_label} exposure {top_fx_pct:.1f}%" if top_fx_label else 'Diversified foreign currencies'
            fx_help = f"{fx_detail}"

        summary_cards.append(
            render_metric_card(
                'FX Exposure',
                f"{fx_exposure_pct:.1f}%",
                value_is_currency=False,
                help_text=f"Share of value in non-CAD currencies ({fx_help})",
            )
        )

        summary_cards.append(
            render_metric_card(
                'Average Gain',
                f"{avg_gain_pct:.1f}%",
                value_is_currency=False,
                help_text='Mean unrealized return across positions',
            )
        )

        # Portfolio Insights - display metric cards
        # Use context-aware header: just "Insights" to match other section headers
        insights_header = 'Insights' if filters_active else 'Portfolio Insights'
        st.markdown(render_section_header(insights_header), unsafe_allow_html=True)
        st.markdown(render_metric_grid(*summary_cards), unsafe_allow_html=True)

    # Allocation chart
    st.markdown("---")
    st.markdown(render_section_header('Allocation'), unsafe_allow_html=True)
    
    # Get fund names for pie chart labels
    pie_tickers = df[df['ticker'] != 'TOTAL']['ticker'].unique().tolist() if 'TOTAL' in df['ticker'].values else df['ticker'].unique().tolist()
    pie_fund_names = get_fund_names(pie_tickers)
    
    # Semantic wrapper with ARIA label for screen readers
    st.markdown('<div role="img" aria-label="Allocation pie chart showing portfolio distribution across funds">', unsafe_allow_html=True)
    pie = make_allocation_pie(df, fund_names_map=pie_fund_names)
    st.plotly_chart(pie, use_container_width=True, config={'displayModeBar': False})
    st.markdown('</div>', unsafe_allow_html=True)

    # Performance chart from snapshots
    st.markdown("---")
    st.markdown(render_section_header(f"Performance — Last {days} Days"), unsafe_allow_html=True)
    
    # Use snapshot-based chart (from historical.csv)
    if os.path.exists(HIST_CSV):
        # Semantic wrapper with ARIA label for screen readers
        st.markdown(f'<div role="img" aria-label="Performance line chart showing portfolio value over the last {days} days with FX impact analysis">', unsafe_allow_html=True)
        perf_fig = make_snapshot_performance_chart(HIST_CSV, days=days, fx_csv_path=FX_CSV, tickers=tickers)
        st.plotly_chart(perf_fig, use_container_width=True, config={'displayModeBar': False})
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.info('No historical snapshots yet. Capture a daily snapshot to build your performance history.')

    # Holdings section - detailed tables
    st.markdown("---")
    st.markdown(render_section_header('Holdings'), unsafe_allow_html=True)
    
    # Helper function for styling gain percentages
    def color_gain_pct(val):
        if pd.isna(val) or val is None:
            return ''
        if val > 0:
            return 'background-color: rgba(16, 185, 129, 0.12); color: #047857; font-weight: 600;'
        if val < 0:
            return 'background-color: rgba(239, 68, 68, 0.12); color: #B91C1C; font-weight: 600;'
        return 'color: var(--pd-neutral);'
    
    # Fetch fund names for all tickers in holdings
    tickers_in_table = df_holdings['ticker'].unique().tolist()
    fund_names_map = get_fund_names(tickers_in_table)
    
    # Add fund/ETF name column
    df_holdings['fund_name'] = df_holdings['ticker'].map(
        lambda t: format_ticker_with_name(t, fund_names_map.get(t, t))
    )
    
    # Reorder columns according to UX requirements:
    # Fund/ETF, Account, Currency, Allocation %, Price, Gain %, Gain, Shares, Cost/Share, Current Value, Total Cost
    # Note: 'ticker' column is excluded from display (ticker info already included in fund_name)
    cols = [
        'fund_name',      # Fund/ETF
        'account',        # Account
        'currency',       # Currency
        'allocation_pct', # Allocation %
        'price',          # Price
        'gain_pct',       # Gain %
        'gain',           # Gain
        'shares',         # Shares
        'cost_basis',     # Cost/Share
        'current_value',  # Current Value
        'cost_total'      # Total Cost
    ]
    df_holdings = df_holdings[cols]
    
    # Show account breakdown if viewing multiple accounts
    unique_accounts = set(h.get('account_nickname') for h in holdings if h.get('account_nickname'))
    if len(unique_accounts) > 1 and 'account' in df.columns:
        # Make "By Account" collapsible to save vertical space (default collapsed)
        with st.expander("**By Account**", expanded=False):
            # Group by account (excluding TOTAL row)
            accounts_df = df[df['account'] != 'TOTAL'].groupby('account').agg({
                'current_value': 'sum',
                'cost_total': 'sum',
                'gain': 'sum'
            }).reset_index()
            accounts_df['gain_pct'] = accounts_df['gain'] / accounts_df['cost_total']
            accounts_df = accounts_df.sort_values('current_value', ascending=False)
            
            # Reorder columns to place Gain % after Current Value
            accounts_df = accounts_df[['account', 'current_value', 'gain_pct', 'cost_total', 'gain']]

            st.dataframe(
                accounts_df.style
                .format({
                    'current_value': '${:,.2f}',
                    'cost_total': '${:,.2f}',
                    'gain': '${:,.2f}',
                    'gain_pct': '{:.2%}'
                })
                .map(color_gain_pct, subset=['gain_pct'])
                .set_table_attributes("class='data-table'"),
                width='stretch',
                hide_index=True,  # Remove the index column (row numbers)
                column_config={
                    'account': st.column_config.TextColumn('Account', width='medium'),
                    'current_value': st.column_config.NumberColumn('Current Value', width='medium'),
                    'gain_pct': st.column_config.NumberColumn('Gain %', width='small'),
                    'cost_total': st.column_config.NumberColumn('Total Cost', width='medium'),
                    'gain': st.column_config.NumberColumn('Gain', width='medium'),
                }
            )
    
    st.markdown(render_subsection_header('All Holdings'), unsafe_allow_html=True)
    
    # Calculate dynamic table height based on number of rows
    # Row height ~35px + header ~42px + padding, cap between 200px and 600px
    num_rows = len(df_holdings)
    row_height = 35
    header_height = 42
    padding = 20
    dynamic_height = min(max(num_rows * row_height + header_height + padding, 200), 600)
    
    # Display holdings table (sortable) with dynamic height
    # hide_index=True removes the first column (row numbers 0, 1, 2...)
    st.dataframe(
        df_holdings.style
        .format({
            'shares': '{:,.4f}',
            'cost_basis': '{:,.4f}',
            'price': '${:,.4f}',
            'current_value': '${:,.2f}',
            'cost_total': '${:,.2f}',
            'gain': '${:,.2f}',
            'allocation_pct': '{:.2%}',
            'gain_pct': '{:.2%}'
        })
        .map(color_gain_pct, subset=['gain_pct'])
        .set_table_attributes("class='data-table'"),
        width='stretch',
        height=dynamic_height,  # Dynamic height based on row count, capped at 600px
        hide_index=True,  # Remove the index column (row numbers)
        column_config={
            'fund_name': st.column_config.TextColumn('Fund/ETF', width='large'),
            'account': st.column_config.TextColumn('Account', width='medium'),
            'currency': st.column_config.TextColumn('Currency', width='small'),
            'allocation_pct': st.column_config.NumberColumn('Allocation %'),
            'price': st.column_config.NumberColumn('Price'),
            'gain_pct': st.column_config.NumberColumn('Gain %'),
            'gain': st.column_config.NumberColumn('Gain'),
            'shares': st.column_config.NumberColumn('Shares'),
            'cost_basis': st.column_config.NumberColumn('Cost/Share'),
            'current_value': st.column_config.NumberColumn('Current Value'),
            'cost_total': st.column_config.NumberColumn('Total Cost'),
        },
    )

    # Data Management
    st.markdown("---")
    st.markdown(render_section_header('Data Management'), unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        # Manual refresh button
        refresh_disabled = not can_refresh
        refresh_help = 'Fetch latest prices from Yahoo Finance'
        
        if st.session_state.rate_limited_until and now < st.session_state.rate_limited_until:
            remaining_mins = int((st.session_state.rate_limited_until - now).total_seconds()) // 60
            refresh_help = f'Rate limited - retry in {remaining_mins} minutes'
        elif not can_refresh:
            refresh_help = 'Cooldown active - wait before retrying'
        
        st.markdown('<div aria-label="Refresh prices button: Fetch latest prices from Yahoo Finance for all portfolio holdings">', unsafe_allow_html=True)
        if st.button('Refresh prices', disabled=refresh_disabled, width='stretch', help=refresh_help):
            # Trigger a manual refresh
            with st.spinner('Fetching latest prices...'):
                st.session_state.fetch_in_progress = True
                
                try:
                    prices, fetched_at_iso, price_source = get_current_prices(all_tickers, csv_path=HIST_CSV)
                    st.session_state.prices_cache = prices
                    st.session_state.fetched_at_iso = fetched_at_iso
                    st.session_state.price_source = price_source
                    st.session_state.last_fetch_time = now
                    st.session_state.last_error = None
                    st.session_state.rate_limited_until = None
                    st.success('Prices updated successfully')
                    st.rerun()
                except Exception as e:
                    error_msg = str(e)
                    if 'YFRateLimitError' in error_msg or 'Rate limited' in error_msg or 'Too Many Requests' in error_msg:
                        st.session_state.rate_limited_until = now + timedelta(seconds=RATE_LIMIT_EXTENDED_COOLDOWN)
                        st.session_state.last_error = "Rate limit reached"
                        st.error(f'Rate limited - retry available in 1 hour')
                    else:
                        st.session_state.last_error = error_msg
                        st.error(f'Fetch failed: {error_msg}')
                    st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Show error message if present
        if st.session_state.last_error:
            st.caption(f"⚠️ {st.session_state.last_error}")
    
    with col2:
        st.markdown('<div aria-label="Update daily snapshot button: Save current portfolio prices to historical data for performance tracking">', unsafe_allow_html=True)
        if st.button('Update daily snapshot', width='stretch', help='Save current prices to historical.csv'):
            written = fetch_and_store_snapshot(holdings, prices, HIST_CSV, fetched_at_iso=fetched_at_iso)
            st.success(f"Updated today's snapshot ({len(written)} holdings)")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col3:
        # Export historical CSV
        if os.path.exists(HIST_CSV):
            st.markdown('<div aria-label="Download snapshots CSV button: Export historical portfolio data to a CSV file">', unsafe_allow_html=True)
            st.download_button(
                'Download snapshots CSV', 
                data=open(HIST_CSV, 'rb').read(), 
                file_name='historical.csv',
                width='stretch',
                help='Export all historical snapshots'
            )
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.info('Historical dataset not started. Select "Update daily snapshot" to begin tracking performance.')


if __name__ == '__main__':
    main()
