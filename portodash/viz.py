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
