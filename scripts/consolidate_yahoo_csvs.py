#!/usr/bin/env python3
"""
Consolidate manually downloaded Yahoo Finance CSV files into historical.csv.

This script reads individual ticker CSV files downloaded from Yahoo Finance
and creates portfolio snapshots in historical.csv format.

Yahoo Finance CSV format expected:
Date,Open,High,Low,Close,Adj Close,Volume

Usage:
    1. Download historical data for each ticker from Yahoo Finance
    2. Save as: data/{TICKER}.csv (e.g., data/FFFFX.csv, data/XEQT.TO.csv)
    3. Run: python scripts/consolidate_yahoo_csvs.py --dir data/
"""
import argparse
import json
import os
import sys
from datetime import datetime, time
from pathlib import Path

import pandas as pd

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from portodash.data_fetch import fetch_and_store_snapshot


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


def load_ticker_csv(csv_path):
    """
    Load a Yahoo Finance CSV and return as DataFrame with date index.
    
    Expected format:
    Date,Open,High,Low,Close,Adj Close,Volume
    """
    try:
        df = pd.read_csv(csv_path)
        
        # Check for required columns
        if 'Date' not in df.columns or 'Adj Close' not in df.columns:
            print(f"  ⚠️  Missing required columns (Date, Adj Close)")
            return None
        
        # Parse dates and set as index
        df['Date'] = pd.to_datetime(df['Date'])
        df = df.set_index('Date')
        
        # Use Adj Close as the price
        df = df[['Adj Close']].rename(columns={'Adj Close': 'price'})
        
        return df
    
    except Exception as e:
        print(f"  ⚠️  Error reading CSV: {e}")
        return None


def consolidate_csvs(csv_dir, days=30):
    """
    Consolidate individual ticker CSVs into historical.csv.
    
    Args:
        csv_dir: Directory containing ticker CSV files (e.g., data/)
        days: Only include last N days (default 30)
    """
    print(f"📊 Consolidating Yahoo Finance CSV files from: {csv_dir}")
    print()
    
    # Load portfolio
    holdings = load_portfolio()
    tickers = list(set(h['ticker'] for h in holdings))
    print(f"📈 Portfolio has {len(tickers)} unique tickers:")
    print(f"   {', '.join(sorted(tickers))}")
    print()
    
    # Load each ticker's CSV
    ticker_data = {}
    missing_tickers = []
    
    for ticker in tickers:
        # Try various filename formats
        possible_filenames = [
            f"{ticker}.csv",
            f"{ticker.replace('.', '_')}.csv",  # XEQT.TO -> XEQT_TO.csv
        ]
        
        csv_path = None
        for filename in possible_filenames:
            potential_path = Path(csv_dir) / filename
            if potential_path.exists():
                csv_path = potential_path
                break
        
        if csv_path:
            print(f"📥 Loading {ticker}...", end=' ')
            df = load_ticker_csv(csv_path)
            if df is not None:
                ticker_data[ticker] = df
                print(f"✅ ({len(df)} days)")
            else:
                print(f"❌")
                missing_tickers.append(ticker)
        else:
            print(f"⏭️  {ticker} - CSV not found (tried: {', '.join(possible_filenames)})")
            missing_tickers.append(ticker)
    
    print()
    
    if not ticker_data:
        print("❌ No ticker data loaded. Please check:")
        print("   1. CSV files are in the correct directory")
        print("   2. Files are named with ticker symbols (e.g., FFFFX.csv)")
        print("   3. Files contain Date and Adj Close columns")
        return
    
    if missing_tickers:
        print(f"⚠️  Warning: {len(missing_tickers)} tickers missing data: {', '.join(missing_tickers)}")
        print()
    
    # Find common date range across all loaded tickers
    all_dates = set()
    for ticker, df in ticker_data.items():
        all_dates.update(df.index.tolist())
    
    all_dates = sorted(all_dates)
    
    # Filter to last N days
    cutoff_date = datetime.now() - pd.Timedelta(days=days)
    filtered_dates = [d for d in all_dates if d >= cutoff_date]
    
    print(f"📅 Date range: {filtered_dates[0].date()} to {filtered_dates[-1].date()}")
    print(f"   {len(filtered_dates)} trading days")
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
        print()
    
    # Create snapshots for each date
    success_count = 0
    skip_count = 0
    
    for date in filtered_dates:
        # Get prices for this date
        prices = {}
        for ticker, df in ticker_data.items():
            if date in df.index and pd.notna(df.loc[date, 'price']):
                prices[ticker] = float(df.loc[date, 'price'])
        
        if prices:
            # Create snapshot with market close time (20:00 UTC ≈ 16:00 ET)
            timestamp = datetime.combine(date.date(), time(hour=20, minute=0))
            fetched_at_iso = timestamp.isoformat() + '+00:00'
            
            # Save snapshot
            fetch_and_store_snapshot(holdings, prices, str(csv_path), fetched_at_iso=fetched_at_iso)
            print(f"✅ {date.date()} ({len(prices)}/{len(tickers)} tickers)")
            success_count += 1
        else:
            print(f"⏭️  {date.date()} (no data)")
            skip_count += 1
    
    print()
    print(f"✨ Consolidation complete!")
    print(f"   ✅ {success_count} snapshots created")
    print(f"   ⏭️  {skip_count} days skipped")
    print(f"   📁 Data saved to: {csv_path}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Consolidate manually downloaded Yahoo Finance CSVs into historical.csv',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/consolidate_yahoo_csvs.py --dir data/
  python scripts/consolidate_yahoo_csvs.py --dir ~/Downloads/yahoo_data/ --days 90

CSV files should be named with ticker symbols (e.g., FFFFX.csv, XEQT.TO.csv)
and contain Yahoo Finance format: Date,Open,High,Low,Close,Adj Close,Volume
        """
    )
    parser.add_argument('--dir', required=True, help='Directory containing ticker CSV files')
    parser.add_argument('--days', type=int, default=30, help='Number of days to include (default: 30)')
    
    args = parser.parse_args()
    
    try:
        consolidate_csvs(args.dir, days=args.days)
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
