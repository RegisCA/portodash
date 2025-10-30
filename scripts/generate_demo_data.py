#!/usr/bin/env python3
"""
Generate demo historical data for portfolio.json.sample.

This script:
1. Downloads 30 days of historical prices for tickers in portfolio.json.sample
2. Generates historical.csv.sample with demo snapshots
3. Uses consolidate_yahoo_csvs.py logic

Usage:
    python scripts/generate_demo_data.py
"""
import json
import os
import sys
from pathlib import Path

import yfinance as yf

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def download_demo_ticker_data():
    """Download 30 days of data for all tickers in portfolio.json.sample."""
    # Load sample portfolio
    sample_path = Path(__file__).parent.parent / 'portfolio.json.sample'
    with open(sample_path) as f:
        data = json.load(f)
    
    # Extract unique tickers
    tickers = set()
    for account in data['accounts']:
        for holding in account['holdings']:
            tickers.add(holding['ticker'])
    
    print(f"📊 Found {len(tickers)} unique tickers in portfolio.json.sample")
    print(f"   {', '.join(sorted(tickers))}")
    print()
    
    # Download data
    demo_data_dir = Path(__file__).parent.parent / 'demo_data'
    demo_data_dir.mkdir(exist_ok=True)
    
    success_count = 0
    for ticker in sorted(tickers):
        print(f"📥 Downloading {ticker}...", end=' ')
        try:
            df = yf.download(
                ticker,
                period='30d',
                progress=False,
                timeout=30
            )
            
            if df.empty:
                print(f"❌ No data")
                continue
            
            # Save as CSV
            output_path = demo_data_dir / f"{ticker}.csv"
            df.to_csv(output_path)
            print(f"✅ ({len(df)} days)")
            success_count += 1
            
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print()
    print(f"✨ Downloaded {success_count}/{len(tickers)} tickers to demo_data/")
    return success_count == len(tickers)


def generate_historical_csv_sample():
    """Generate historical.csv.sample using consolidate script."""
    import subprocess
    
    print("📊 Generating historical.csv.sample...")
    print()
    
    # Temporarily rename portfolio.json if it exists
    portfolio_path = Path(__file__).parent.parent / 'portfolio.json'
    portfolio_backup = None
    if portfolio_path.exists():
        portfolio_backup = Path(__file__).parent.parent / 'portfolio.json.tmp'
        portfolio_path.rename(portfolio_backup)
    
    # Copy sample to active location
    sample_path = Path(__file__).parent.parent / 'portfolio.json.sample'
    portfolio_path_copy = Path(__file__).parent.parent / 'portfolio.json'
    import shutil
    shutil.copy(sample_path, portfolio_path_copy)
    
    # Temporarily rename historical.csv if it exists
    hist_path = Path(__file__).parent.parent / 'historical.csv'
    hist_backup = None
    if hist_path.exists():
        hist_backup = Path(__file__).parent.parent / 'historical.csv.tmp'
        hist_path.rename(hist_backup)
    
    try:
        # Run consolidate script
        consolidate_script = Path(__file__).parent / 'consolidate_yahoo_csvs.py'
        result = subprocess.run(
            ['python', str(consolidate_script), '--dir', 'demo_data'],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent
        )
        
        print(result.stdout)
        if result.stderr:
            print(result.stderr)
        
        if result.returncode == 0:
            # Rename generated historical.csv to historical.csv.sample
            hist_path = Path(__file__).parent.parent / 'historical.csv'
            sample_hist_path = Path(__file__).parent.parent / 'historical.csv.sample'
            if hist_path.exists():
                hist_path.rename(sample_hist_path)
                print(f"✅ Created historical.csv.sample")
                return True
        else:
            print(f"❌ Consolidation failed with code {result.returncode}")
            return False
            
    finally:
        # Restore original files
        if portfolio_path_copy.exists():
            portfolio_path_copy.unlink()
        if portfolio_backup:
            portfolio_backup.rename(portfolio_path)
        if hist_backup:
            hist_backup.rename(hist_path)


if __name__ == '__main__':
    print("🎨 Generating Demo Data for Portfolio Dashboard")
    print("=" * 60)
    print()
    
    # Step 1: Download ticker data
    if not download_demo_ticker_data():
        print("⚠️  Some tickers failed to download")
        response = input("Continue anyway? [y/N]: ")
        if response.lower() != 'y':
            print("Cancelled.")
            sys.exit(1)
    
    print()
    
    # Step 2: Generate historical.csv.sample
    if generate_historical_csv_sample():
        print()
        print("✨ Demo data generation complete!")
        print()
        print("Files created:")
        print("  - demo_data/*.csv (ticker price data)")
        print("  - historical.csv.sample (30 days of snapshots)")
        print()
        print("Next: Run 'python scripts/demo_mode.py' to switch to demo mode")
    else:
        print()
        print("❌ Failed to generate historical.csv.sample")
        sys.exit(1)
