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


def make_snapshot_performance_chart(csv_path, days=30):
    """Create a performance chart from historical.csv snapshots.
    
    Args:
        csv_path: Path to historical.csv file
        days: Number of days to show (default 30)
    
    Returns:
        Plotly figure showing portfolio value over time from snapshots
    """
    import os
    from datetime import datetime, timedelta
    
    if not os.path.exists(csv_path):
        return px.line(title='Performance (no snapshot data)')
    
    try:
        # Read the CSV
        df = pd.read_csv(csv_path)
        
        if df.empty:
            return px.line(title='Performance (no snapshot data)')
        
        # Parse dates
        df['date'] = pd.to_datetime(df['date'])
        
        # Filter to last N days
        cutoff = datetime.now() - timedelta(days=days)
        df = df[df['date'] >= cutoff]
        
        if df.empty:
            return px.line(title=f'Performance (no data in last {days} days)')
        
        # Group by date and sum portfolio_value (each row has the same portfolio_value, so take first)
        daily_values = df.groupby('date')['portfolio_value'].first().reset_index()
        daily_values = daily_values.sort_values('date')
        
        # Create the chart
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
        return px.line(title=f'Performance (error: {str(e)[:50]})')
