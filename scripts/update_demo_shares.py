#!/usr/bin/env python3
"""
Update historical.csv.sample with new share quantities from portfolio.json.sample.

This script:
1. Reads portfolio.json.sample to get updated share quantities
2. Reads historical.csv.sample
3. Updates shares for each holding based on account+ticker match
4. Recalculates current_value, portfolio_value, and allocation_pct
5. Writes updated historical.csv.sample

Usage:
    python scripts/update_demo_shares.py
"""
import json
import sys
from pathlib import Path

import pandas as pd

def main():
    base_dir = Path(__file__).parent.parent
    
    # Load portfolio.json.sample to get new share quantities
    portfolio_path = base_dir / 'portfolio.json.sample'
    with open(portfolio_path) as f:
        portfolio = json.load(f)
    
    # Build a map of (account, ticker) -> shares
    shares_map = {}
    for account in portfolio['accounts']:
        account_nick = account['nickname']
        for holding in account['holdings']:
            key = (account_nick, holding['ticker'])
            shares_map[key] = holding['shares']
    
    print(f"📊 Loaded {len(shares_map)} holdings from portfolio.json.sample")
    
    # Read historical.csv.sample
    hist_path = base_dir / 'historical.csv.sample'
    df = pd.read_csv(hist_path)
    
    print(f"📈 Loaded {len(df)} rows from historical.csv.sample")
    
    # Update shares for each row
    updated_count = 0
    for idx, row in df.iterrows():
        key = (row['account'], row['ticker'])
        if key in shares_map:
            old_shares = row['shares']
            new_shares = shares_map[key]
            if old_shares != new_shares:
                df.at[idx, 'shares'] = new_shares
                # Recalculate current_value
                df.at[idx, 'current_value'] = new_shares * row['price']
                updated_count += 1
    
    print(f"✏️  Updated {updated_count} rows with new share quantities")
    
    # Recalculate portfolio_value and allocation_pct for each date
    print("🔄 Recalculating portfolio values and allocations...")
    
    for date in df['date'].unique():
        date_mask = df['date'] == date
        date_df = df[date_mask]
        
        # Calculate total portfolio value for this date
        total_value = date_df['current_value'].sum()
        
        # Update portfolio_value and allocation_pct for all rows on this date
        df.loc[date_mask, 'portfolio_value'] = total_value
        df.loc[date_mask, 'allocation_pct'] = df.loc[date_mask, 'current_value'] / total_value
    
    # Write back to historical.csv.sample
    df.to_csv(hist_path, index=False)
    
    print(f"✅ Updated historical.csv.sample successfully!")
    print(f"   New total portfolio value on first date: ${df[df['date'] == df['date'].iloc[0]]['portfolio_value'].iloc[0]:,.2f}")

if __name__ == '__main__':
    main()
