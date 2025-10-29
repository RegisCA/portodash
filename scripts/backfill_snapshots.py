#!/usr/bin/env python3
"""
Backfill historical.csv with snapshots from past days.

This script fetches historical prices for your portfolio holdings and creates
snapshots for each day using a single batch request to avoid rate limiting.

Usage:
    python scripts/backfill_snapshots.py [--days 30]
"""
import argparse
import json
import os
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from portodash.data_fetch import fetch_and_store_snapshot
import yfinance as yf


def load_portfolio():
    """Load portfolio from portfolio.json."""
    portfolio_path = Path(__file__).parent.parent / 'portfolio.json'
    with open(portfolio_path) as f:
        data = json.load(f)
    
    # Flatten holdings with account metadata
    holdings = []
    for account in data['accounts']:
        for holding in account['holdings']:
            holdings.append({
                'ticker': holding['ticker'],
                'shares': holding['shares'],
                'cost_basis': holding['cost_basis'],
                'currency': holding.get('currency', account.get('base_currency', 'CAD')),
                'account_nickname': account['nickname'],
                'account_holder': account['holder'],
                'account_type': account['type'],
            })
    return holdings


def get_historical_prices_batch(tickers, start_date, end_date):
    """
    Fetch closing prices for all tickers across a date range in one request.
    
    Args:
        tickers: List of ticker symbols
        start_date: datetime object for start
        end_date: datetime object for end
    
    Returns:
        DataFrame with dates as index, tickers as columns (or empty on failure)
    """
    try:
        print(f"   Fetching all tickers for date range in one request...")
        data = yf.download(
            tickers=" ".join(tickers),
            start=start_date.strftime('%Y-%m-%d'),
            end=end_date.strftime('%Y-%m-%d'),
            progress=False,
            threads=False,
            timeout=30
        )
        
        if data.empty:
            return pd.DataFrame()
        
        # Extract Adj Close prices
        if 'Adj Close' in data.columns:
            # Multiple tickers
            if isinstance(data['Adj Close'], pd.DataFrame):
                prices_df = data['Adj Close']
            else:
                # Single ticker
                prices_df = data['Adj Close'].to_frame(name=tickers[0])
        else:
            # Fallback to Close if Adj Close not available
            if isinstance(data['Close'], pd.DataFrame):
                prices_df = data['Close']
            else:
                prices_df = data['Close'].to_frame(name=tickers[0])
        
        return prices_df
    
    except Exception as e:
        print(f"  ⚠️  Failed to fetch batch prices: {e}")
        return pd.DataFrame()


def backfill_snapshots(days=30, delay=2):
    """
    Backfill historical.csv with snapshots from the past N days.
    
    Uses a single yfinance request for the entire date range to avoid rate limiting.
    
    Args:
        days: Number of days to backfill (default 30)
        delay: Not used in batch mode (kept for API compatibility)
    """
    print(f"📊 Backfilling {days} days of portfolio snapshots...")
    
    # Load portfolio
    holdings = load_portfolio()
    tickers = list(set(h['ticker'] for h in holdings))
    print(f"📈 Found {len(holdings)} holdings with {len(tickers)} unique tickers")
    print(f"   Tickers: {', '.join(sorted(tickers))}")
    
    # Determine date range
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days)
    
    print(f"📅 Date range: {start_date} to {end_date}")
    print(f"⚡ Using batch download (single request for all dates)")
    print()
    
    # CSV path
    csv_path = Path(__file__).parent.parent / 'historical.csv'
    
    # Check if file exists and ask for confirmation
    if csv_path.exists():
        print(f"⚠️  historical.csv already exists with data.")
        response = input("   Append new snapshots? [y/N]: ")
        if response.lower() != 'y':
            print("Cancelled.")
            return
    
    # Fetch all historical prices in one batch request
    print("📥 Downloading historical prices...")
    prices_df = get_historical_prices_batch(
        tickers, 
        datetime.combine(start_date, datetime.min.time()),
        datetime.combine(end_date, datetime.min.time())
    )
    
    if prices_df.empty:
        print("❌ Failed to fetch historical data. Check your internet connection or try again later.")
        return
    
    print(f"✅ Downloaded {len(prices_df)} days of price data")
    print()
    
    # Iterate through each date in the data
    success_count = 0
    skip_count = 0
    
    for date_idx in prices_df.index:
        date_obj = pd.to_datetime(date_idx).date()
        
        # Skip weekends (although they shouldn't be in the data)
        if date_obj.weekday() >= 5:
            skip_count += 1
            continue
        
        # Get prices for this date
        day_prices = prices_df.loc[date_idx]
        prices_dict = {}
        
        for ticker in tickers:
            if ticker in day_prices and pd.notna(day_prices[ticker]):
                prices_dict[ticker] = float(day_prices[ticker])
        
        if prices_dict:
            # Create snapshot with the date's timestamp (market close time ~16:00 ET)
            timestamp = datetime.combine(date_obj, datetime.min.time().replace(hour=20, minute=0))
            fetched_at_iso = timestamp.isoformat() + '+00:00'
            
            # Save snapshot
            fetch_and_store_snapshot(holdings, prices_dict, str(csv_path), fetched_at_iso=fetched_at_iso)
            print(f"✅ {date_obj} ({len(prices_dict)}/{len(tickers)} tickers)")
            success_count += 1
        else:
            print(f"⏭️  {date_obj} (no data)")
            skip_count += 1
    
    print()
    print(f"✨ Backfill complete!")
    print(f"   ✅ {success_count} snapshots created")
    print(f"   ⏭️  {skip_count} days skipped (weekends or no data)")
    print(f"   📁 Data saved to: {csv_path}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Backfill historical portfolio snapshots')
    parser.add_argument('--days', type=int, default=30, help='Number of days to backfill (default: 30)')
    parser.add_argument('--delay', type=float, default=2.0, help='Seconds between requests (default: 2)')
    
    args = parser.parse_args()
    
    try:
        backfill_snapshots(days=args.days, delay=args.delay)
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        sys.exit(1)
