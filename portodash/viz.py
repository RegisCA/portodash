import plotly.express as px
import pandas as pd


def make_allocation_pie(df):
    """Return a Plotly pie chart for allocation. Expects df with ticker and current_value."""
    if df.empty:
        return px.pie(values=[], names=[], title="Allocation")

    # remove TOTAL row if present
    d = df[df['ticker'] != 'TOTAL'] if 'ticker' in df.columns else df
    fig = px.pie(d, names='ticker', values='current_value', title='Portfolio Allocation', hole=0.3)
    fig.update_traces(textposition='inside', textinfo='percent+label')
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


def make_snapshot_performance_chart(csv_path, days=30, fx_csv_path=None):
    """Create a performance chart from historical.csv snapshots with FX impact analysis.
    
    Shows two lines:
    1. Market performance: Portfolio value at fixed FX rate (from start of period)
    2. Actual performance: Portfolio value with daily FX rates (includes FX impact)
    
    Args:
        csv_path: Path to historical.csv file
        days: Number of days to show (default 30)
        fx_csv_path: Path to fx_rates.csv file (optional)
    
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
        
        # Parse dates
        df['date'] = pd.to_datetime(df['date'])
        
        # Filter to last N days - make cutoff timezone-aware to match df['date']
        cutoff = pd.Timestamp.now(tz='UTC') - timedelta(days=days)
        df = df[df['date'] >= cutoff]
        
        if df.empty:
            return px.line(title=f'Performance (no data in last {days} days)')
        
        # Load FX rates if available
        fx_rates = None
        if fx_csv_path and os.path.exists(fx_csv_path):
            try:
                fx_df = pd.read_csv(fx_csv_path)
                fx_df['date'] = pd.to_datetime(fx_df['date'])
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
        
        # Create the chart with two lines
        if fx_rate_by_date and first_fx_rate:
            # Show both lines if we have FX data
            fig = px.line(
                plot_df,
                x='date',
                y=['Market Performance (Fixed FX)', 'Actual Performance (with FX)'],
                title=f'Portfolio Performance — Last {days} Days',
                labels={'value': 'Portfolio Value (CAD)', 'date': 'Date', 'variable': 'Series'}
            )
            
            # Customize line styles
            fig.data[0].line.color = '#2E86AB'  # Blue for fixed FX
            fig.data[0].line.width = 2
            fig.data[0].line.dash = 'dash'
            
            fig.data[1].line.color = '#A23B72'  # Purple for actual
            fig.data[1].line.width = 2.5
            
            fig.update_layout(
                hovermode='x unified',
                yaxis_tickformat='$,.0f',
                legend=dict(
                    orientation='h',
                    yanchor='bottom',
                    y=1.02,
                    xanchor='right',
                    x=1
                )
            )
        else:
            # No FX data - show single line using portfolio_value from CSV
            daily_values = df.groupby('date')['portfolio_value'].first().reset_index()
            daily_values = daily_values.sort_values('date')
            
            fig = px.line(
                daily_values,
                x='date',
                y='portfolio_value',
                title=f'Portfolio Value — Last {days} Days',
                labels={'portfolio_value': 'Portfolio Value (CAD)', 'date': 'Date'}
            )
            
            fig.update_traces(line_color='#1f77b4', line_width=2)
            fig.update_layout(
                hovermode='x unified',
                yaxis_tickformat='$,.0f'
            )
        
        return fig
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return px.line(title=f'Performance (error: {str(e)[:50]})')
