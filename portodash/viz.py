import plotly.express as px
import pandas as pd


def make_allocation_pie(df, fund_names_map=None):
    """Return a Plotly pie chart for allocation with clean, modern styling.
    
    Args:
        df: DataFrame with ticker and current_value columns
        fund_names_map: Optional dict mapping tickers to long names
    """
    if df.empty:
        return px.pie(values=[], names=[], title="Allocation")

    # remove TOTAL row if present - use .copy() to avoid SettingWithCopyWarning
    if 'ticker' in df.columns:
        d = df[df['ticker'] != 'TOTAL'].copy()
    else:
        d = df.copy()
    
    # Calculate percentages for label threshold
    total_value = d['current_value'].sum()
    d['percentage'] = (d['current_value'] / total_value * 100)
    
    # Add display labels with fund names (for hover and legend)
    if fund_names_map:
        d['display_label'] = d['ticker'].apply(
            lambda t: f"{t} — {fund_names_map[t]}" if t in fund_names_map and fund_names_map[t] != t else t
        )
    else:
        d['display_label'] = d['ticker']
    
    # Create callout text: show ticker + % only if >= 5%, otherwise empty
    d['callout_text'] = d.apply(
        lambda row: f"{row['ticker']}<br>{row['percentage']:.1f}%" if row['percentage'] >= 5 else '',
        axis=1
    )
    
    # Clean color palette - Wealthsimple inspired
    colors = ['#00D46A', '#2E86AB', '#A23B72', '#F18F01', '#C73E1D', 
              '#6B7280', '#10B981', '#3B82F6', '#8B5CF6', '#EC4899']
    
    fig = px.pie(
        d, 
        names='display_label', 
        values='current_value',
        hole=0.4,
        color_discrete_sequence=colors
    )
    
    fig.update_traces(
        textposition='outside',
        text=d['callout_text'].tolist(),
        textinfo='text',
        textfont=dict(size=13, family='system-ui, -apple-system, sans-serif'),
        marker=dict(line=dict(color='#FFFFFF', width=2)),
        hovertemplate='<b>%{label}</b><br>Value: %{value:$,.0f} CAD<br>Share: %{percent}<extra></extra>'
    )
    
    fig.update_layout(
        showlegend=True,
        legend=dict(
            orientation='v',
            yanchor='middle',
            y=0.5,
            xanchor='left',
            x=1.05,
            font=dict(size=12)
        ),
        margin=dict(l=20, r=120, t=40, b=20),
        font=dict(family='system-ui, -apple-system, sans-serif', color='#1A1A1A'),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        hoverlabel=dict(
            bgcolor='white',
            font=dict(size=13, family='system-ui, -apple-system, sans-serif')
        )
    )
    
    return fig


def make_30d_performance_chart(hist_prices, holdings_list):
    """Given a prices DataFrame (dates x tickers) and holdings list, return a Plotly line fig.

    The chart shows portfolio value over time and optionally individual ticker lines.
    """
    if hist_prices is None or hist_prices.empty:
        return px.line(title='30-day Performance (no data)')

    # ensure columns match holdings tickers
    tickers = [h['ticker'] for h in holdings_list]
    # intersect
    present = [t for t in tickers if t in hist_prices.columns]
    if not present:
        return px.line(title='30-day Performance (no tickers found)')

    # compute portfolio total series
    df = hist_prices[present].fillna(method='ffill').fillna(0)
    shares = {h['ticker']: float(h.get('shares', 0)) for h in holdings_list}
    weighted = pd.DataFrame({t: df[t] * shares.get(t, 0) for t in present})
    weighted['portfolio_value'] = weighted.sum(axis=1)

    fig = px.line(weighted, y='portfolio_value', title='Portfolio value (last 30 days)')
    fig.update_layout(yaxis_title='Value (currency)')
    return fig


def make_snapshot_performance_chart(csv_path, days=30, fx_csv_path=None, tickers=None):
    """Create a performance chart from historical.csv snapshots with FX impact analysis.
    
    Shows two lines:
    1. Market performance: Portfolio value at fixed FX rate (from start of period)
    2. Actual performance: Portfolio value with daily FX rates (includes FX impact)
    
    Args:
        csv_path: Path to historical.csv file
        days: Number of days to show (default 30)
        fx_csv_path: Path to fx_rates.csv file (optional)
        tickers: List of tickers to include (optional, for filtering by account/holder/type)
    
    Returns:
        Plotly figure showing portfolio value over time from snapshots
    """
    import os
    from datetime import datetime, timedelta
    
    if not os.path.exists(csv_path):
        return px.line(title='Performance (no snapshot data)')
    
    try:
        # Read the historical snapshots CSV
        df = pd.read_csv(csv_path)
        
        if df.empty:
            return px.line(title='Performance (no snapshot data)')
        
        # Filter by tickers if provided (for account/holder/type filtering)
        if tickers is not None:
            df = df[df['ticker'].isin(tickers)]
            
            if df.empty:
                return px.line(title='Performance (no data for selected filters)')
        
        # Parse dates - handle ISO8601 format
        df['date'] = pd.to_datetime(df['date'], format='ISO8601')
        
        # Filter to last N days - make cutoff timezone-aware to match df['date']
        cutoff = pd.Timestamp.now(tz='UTC') - timedelta(days=days)
        df = df[df['date'] >= cutoff]
        
        if df.empty:
            return px.line(title=f'Performance (no data in last {days} days)')
        
        # Deduplicate: if multiple snapshots exist for the same date, keep only the latest
        # Group by normalized date and keep only the rows with the max timestamp for each date
        df = df.sort_values('date')
        df['date_only'] = df['date'].dt.normalize()
        # For each date_only, find the max timestamp and keep only those rows
        latest_timestamps = df.groupby('date_only')['date'].max().reset_index()
        latest_timestamps.columns = ['date_only', 'latest_date']
        df = df.merge(latest_timestamps, on='date_only')
        df = df[df['date'] == df['latest_date']]
        df = df.drop(['date_only', 'latest_date'], axis=1)
        
        # Load FX rates if available
        fx_rates = None
        if fx_csv_path and os.path.exists(fx_csv_path):
            try:
                fx_df = pd.read_csv(fx_csv_path)
                # FX rates CSV should be simple YYYY-MM-DD format, but handle ISO8601 too
                fx_df['date'] = pd.to_datetime(fx_df['date'], format='mixed')
                # Ensure timezone-aware
                if fx_df['date'].dt.tz is None:
                    fx_df['date'] = fx_df['date'].dt.tz_localize('UTC')
                fx_rates = fx_df.set_index('date')['usd_cad'].to_dict()
            except Exception as e:
                print(f"Could not load FX rates: {e}")
        
        # Calculate daily portfolio values
        # Group by date and calculate for each holding
        unique_dates = sorted(df['date'].unique())
        
        # Forward-fill FX rates for missing dates (similar to how we handle prices)
        # Normalize FX rates to date-only for matching (ignore time component)
        fx_rate_by_date = {}
        last_known_fx = None
        
        if fx_rates:
            # Normalize FX rates dict to use date-only keys
            # This handles the case where FX rates are at 00:00 and snapshots are at 20:00
            fx_rates_by_date_only = {}
            for dt, rate in fx_rates.items():
                date_only = pd.Timestamp(dt).normalize()  # Remove time component
                fx_rates_by_date_only[date_only] = rate
            
            for date in unique_dates:
                date_ts = pd.Timestamp(date).normalize()  # Normalize to date-only
                if date_ts in fx_rates_by_date_only:
                    last_known_fx = fx_rates_by_date_only[date_ts]
                    fx_rate_by_date[pd.Timestamp(date)] = last_known_fx  # Store with original timestamp
                elif last_known_fx is not None:
                    # Forward-fill: use last known rate
                    fx_rate_by_date[pd.Timestamp(date)] = last_known_fx
        
        # Get the first FX rate (for fixed FX calculation)
        first_fx_rate = fx_rate_by_date.get(unique_dates[0]) if fx_rate_by_date else None
        
        # Check if there are any USD holdings (for FX labeling)
        has_usd_holdings = any(not ticker.endswith('.TO') for ticker in df['ticker'].unique())
        
        # Calculate portfolio values with and without FX impact
        portfolio_values_fixed_fx = []
        portfolio_values_actual_fx = []
        dates = []
        
        for date, group in df.groupby('date'):
            # Get FX rate for this date (forward-filled if missing)
            date_ts = pd.Timestamp(date)
            actual_fx = fx_rate_by_date.get(date_ts, first_fx_rate)
            
            # Calculate portfolio value with fixed FX (first date's rate)
            value_fixed = 0
            value_actual = 0
            
            for _, holding in group.iterrows():
                ticker = holding['ticker']
                shares = holding['shares']
                price = holding['price']
                
                # Infer currency from ticker (TSX tickers end with .TO)
                is_usd = not ticker.endswith('.TO')
                
                # Value in native currency
                native_value = shares * price
                
                # Convert to CAD if needed
                if is_usd:
                    if first_fx_rate:
                        value_fixed += native_value * first_fx_rate
                    else:
                        value_fixed += native_value  # No conversion if no FX data
                    
                    if actual_fx:
                        value_actual += native_value * actual_fx
                    else:
                        value_actual += native_value
                else:
                    # Already in CAD (TSX ticker)
                    value_fixed += native_value
                    value_actual += native_value
            
            dates.append(date)
            portfolio_values_fixed_fx.append(value_fixed)
            portfolio_values_actual_fx.append(value_actual)
        
        # Create DataFrame for plotting
        plot_df = pd.DataFrame({
            'date': dates,
            'Market Performance (Fixed FX)': portfolio_values_fixed_fx,
            'Actual Performance (with FX)': portfolio_values_actual_fx
        }).sort_values('date')
        
        # Create the chart - show two lines only if we have FX data AND USD holdings
        if fx_rate_by_date and first_fx_rate and has_usd_holdings:
            # Show both lines if we have FX data and multi-currency portfolio
            fig = px.line(
                plot_df,
                x='date',
                y=['Market Performance (Fixed FX)', 'Actual Performance (with FX)'],
                labels={'value': 'Portfolio Value (CAD)', 'date': '', 'variable': 'Series'}
            )
            
            # Customize line styles - cleaner, more modern
            fig.data[0].line.color = '#6B7280'  # Gray for fixed FX baseline
            fig.data[0].line.width = 2
            fig.data[0].line.dash = 'dot'
            fig.data[0].name = 'Market (Fixed FX)'
            fig.data[0].hovertemplate = '%{y:$,.0f}<extra></extra>'
            
            fig.data[1].line.color = '#00D46A'  # Mint green for actual (Wealthsimple signature)
            fig.data[1].line.width = 3
            fig.data[1].name = 'Actual (with FX)'
            fig.data[1].hovertemplate = '%{y:$,.0f}<extra></extra>'
            
            fig.update_layout(
                hovermode='x unified',
                yaxis_tickformat='$,.0f',
                legend=dict(
                    orientation='h',
                    yanchor='top',
                    y=-0.15,
                    xanchor='center',
                    x=0.5,
                    font=dict(size=13)
                ),
                font=dict(family='system-ui, -apple-system, sans-serif', color='#1A1A1A'),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                xaxis=dict(
                    showgrid=True,
                    gridcolor='#E8EBED',
                    gridwidth=1,
                    title=''
                ),
                yaxis=dict(
                    showgrid=True,
                    gridcolor='#E8EBED',
                    gridwidth=1
                ),
                margin=dict(l=20, r=20, t=20, b=80),
                hoverlabel=dict(
                    bgcolor='white',
                    font=dict(size=13, family='system-ui, -apple-system, sans-serif')
                )
            )
            
            # Update x-axis to show formatted date in hover
            fig.update_xaxes(hoverformat='%b %-d, %Y')
        else:
            # Single currency or no FX data - show single line
            # Use the actual values (they'll be the same as fixed if single currency)
            single_line_df = pd.DataFrame({
                'date': dates,
                'portfolio_value': portfolio_values_actual_fx
            }).sort_values('date')
            
            fig = px.line(
                single_line_df,
                x='date',
                y='portfolio_value',
                labels={'portfolio_value': 'Portfolio Value (CAD)', 'date': ''}
            )
            
            fig.update_traces(
                line_color='#00D46A',
                line_width=3,
                name='Portfolio Value',
                showlegend=True,
                hovertemplate='%{y:$,.0f}<extra></extra>'
            )
            
            fig.update_layout(
                hovermode='x unified',
                yaxis_tickformat='$,.0f',
                showlegend=True,
                legend=dict(
                    orientation='h',
                    yanchor='top',
                    y=-0.15,
                    xanchor='center',
                    x=0.5,
                    font=dict(size=13)
                ),
                font=dict(family='system-ui, -apple-system, sans-serif', color='#1A1A1A'),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                xaxis=dict(
                    showgrid=True,
                    gridcolor='#E8EBED',
                    gridwidth=1,
                    title=''
                ),
                yaxis=dict(
                    showgrid=True,
                    gridcolor='#E8EBED',
                    gridwidth=1
                ),
                margin=dict(l=20, r=20, t=20, b=80),
                hoverlabel=dict(
                    bgcolor='white',
                    font=dict(size=13, family='system-ui, -apple-system, sans-serif')
                )
            )
            
            # Update x-axis to show formatted date in hover
            fig.update_xaxes(hoverformat='%b %-d, %Y')
        
        return fig
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return px.line(title=f'Performance (error: {str(e)[:50]})')
