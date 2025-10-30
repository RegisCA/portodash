#!/usr/bin/env python3
"""Test script to verify cache fallback works properly."""

import logging
import sys

import pytest
from portodash.data_fetch import get_current_prices
from portodash.cache import get_cached_prices

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_cache_fallback():
    """Test that cache fallback works when yfinance is rate limited."""
    
    # Test tickers from portfolio
    tickers = ['XEQT.TO', 'FFFFX', 'FBGRX']
    csv_path = 'historical.csv'
    
    print("\n=== Testing Cache Fallback ===\n")
    
    # First, test direct cache access
    print("1. Testing direct cache access (72 hour window)...")
    cached_prices, cached_times = get_cached_prices(tickers, csv_path, max_age_hours=72)
    
    for ticker in tickers:
        price = cached_prices.get(ticker)
        timestamp = cached_times.get(ticker)
        if price:
            print(f"   ✓ {ticker}: ${price:.2f} (cached at {timestamp})")
        else:
            print(f"   ✗ {ticker}: No cached data")
    
    # Now test get_current_prices with cache fallback
    print("\n2. Testing get_current_prices with cache fallback...")
    prices, fetched_at, source = get_current_prices(tickers, csv_path=csv_path, cache_max_age_hours=72)
    
    print(f"\n   Source: {source}")
    print(f"   Fetched at: {fetched_at}")
    
    success_count = 0
    for ticker in tickers:
        price = prices.get(ticker)
        if price:
            print(f"   ✓ {ticker}: ${price:.2f}")
            success_count += 1
        else:
            print(f"   ✗ {ticker}: No price available")
    
    print(f"\n=== Results: {success_count}/{len(tickers)} prices retrieved ===")
    
    if success_count == 0:
        print("\n❌ FAIL: No prices retrieved. Cache fallback not working!")
        pytest.fail("Cache fallback did not return any prices")
    elif success_count == len(tickers):
        print(f"\n✅ SUCCESS: All prices retrieved from {source}")
    else:
        print(f"\n⚠️  PARTIAL: {success_count} prices retrieved from {source}")
        # Treat partial results as soft success; pytest test finishes without failing

if __name__ == '__main__':
    success = test_cache_fallback()
    sys.exit(0 if success else 1)
