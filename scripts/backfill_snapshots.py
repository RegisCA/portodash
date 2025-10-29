#!/usr/bin/env python3
"""
Backfill historical.csv with snapshots from past days.

This script fetches historical prices for your portfolio holdings and creates
snapshots for each day, respecting yfinance rate limits with delays between requests.

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


def get_historical_prices_for_date(tickers, target_date):
    """
    Fetch closing prices for a specific date.
    
    Args:
        tickers: List of ticker symbols
        target_date: datetime object for the target date
    
    Returns:
        dict: ticker -> price, or empty dict on failure
    """
    # Fetch a small window around the target date (3 days to account for weekends)
    start = target_date - timedelta(days=2)
    end = target_date + timedelta(days=1)
    
    try:
        data = yf.download(
            tickers=" ".join(tickers),
            start=start.strftime('%Y-%m-%d'),
            end=end.strftime('%Y-%m-%d'),
            progress=False,
            threads=False,
            timeout=30
        )
        
        if data.empty:
            return {}
        
        # Get the Adj Close prices for the target date (or closest available)
        if 'Adj Close' in data.columns:
            # Multiple tickers
            prices = {}
            for ticker in tickers:
                if ticker in data['Adj Close'].columns:
                    series = data['Adj Close'][ticker].dropna()
                    if not series.empty:
                        # Get the last available price (closest to target date)
                        prices[ticker] = float(series.iloc[-1])
            return prices
        else:
            # Single ticker
            ticker = tickers[0]
            series = data['Adj Close'].dropna() if 'Adj Close' in data else data['Close'].dropna()
            if not series.empty:
                return {ticker: float(series.iloc[-1])}
            return {}
    
    except Exception as e:
        print(f"  ⚠️  Failed to fetch prices for {target_date.strftime('%Y-%m-%d')}: {e}")
        return {}


def backfill_snapshots(days=30, delay=2):
    """
    Backfill historical.csv with snapshots from the past N days.
    
    Args:
        days: Number of days to backfill (default 30)
        delay: Seconds to wait between requests to avoid rate limiting (default 2)
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
    print(f"⏱️  Rate limiting: {delay}s delay between requests")
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
    
    # Iterate through each day
    current_date = start_date
    success_count = 0
    skip_count = 0
    
    while current_date <= end_date:
        # Skip weekends (markets closed)
        if current_date.weekday() >= 5:  # Saturday=5, Sunday=6
            print(f"⏭️  {current_date} (weekend, skipping)")
            current_date += timedelta(days=1)
            skip_count += 1
            continue
        
        print(f"📥 Fetching {current_date}...", end=' ', flush=True)
        
        # Fetch prices for this date
        prices = get_historical_prices_for_date(tickers, datetime.combine(current_date, datetime.min.time()))
        
        if prices:
            # Create snapshot with the date's timestamp (market close time ~16:00 ET)
            timestamp = datetime.combine(current_date, datetime.min.time().replace(hour=20, minute=0))  # 20:00 UTC ≈ 16:00 ET
            fetched_at_iso = timestamp.isoformat() + '+00:00'
            
            # Save snapshot
            fetch_and_store_snapshot(holdings, prices, str(csv_path), fetched_at_iso=fetched_at_iso)
            print(f"✅ ({len(prices)}/{len(tickers)} tickers)")
            success_count += 1
        else:
            print("❌ (no data)")
            skip_count += 1
        
        # Move to next day
        current_date += timedelta(days=1)
        
        # Rate limiting delay (except for last day)
        if current_date <= end_date:
            time.sleep(delay)
    
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
