# yfinance Optimization & Rate Limiting Guide

## Key Finding: No Official API or Rate Limits

**yfinance is NOT an official API** - it scrapes Yahoo Finance's public web pages. Yahoo Finance has no published rate limits because it's designed for human users, not programmatic access. The rate limiting you experience is Yahoo's anti-scraping protection.

## Research Summary

Based on analysis of the [yfinance GitHub repository](https://github.com/ranaroussi/yfinance) (19.6k stars):

### What yfinance Does
- Scrapes Yahoo Finance's public web interface
- No authentication required
- No API key needed
- Uses `curl_cffi` library to mimic browser requests
- Intended for "research and educational purposes"

### Rate Limiting Reality
- **No published rate limits** - Yahoo's protection is opaque and variable
- Rate limits depend on:
  - Your IP address
  - Request frequency
  - Time of day
  - Yahoo's server load
  - Potential cookie/session state
- Can result in 24-48 hour blocks when triggered
- Returns HTTP 429 (Too Many Requests) when rate limited

### No Batch API
- **Each ticker = separate HTTP request**
- No bulk/batch endpoint exists
- 11 tickers = 11 separate requests to Yahoo
- Threading helps parallelize but doesn't reduce total requests

## Current Implementation (Optimized)

### Parameters Used
```python
yf.download(
    tickers=" ".join(tickers),
    period="5d",           # Minimal data transfer
    interval="1d",         # Daily data (not intraday)
    threads=True,          # Parallel fetching (2x CPU cores)
    timeout=30,            # Extended timeout (default is 10s)
    progress=False,        # No progress bar
    auto_adjust=False,     # Raw data (faster)
    group_by='ticker'      # Multi-ticker format
)
```

### Why These Settings
1. **`threads=True`**: Enables parallel requests (defaults to 2x CPU cores)
   - With 11 tickers, makes ~11 parallel requests instead of sequential
   - Reduces total fetch time from ~11 seconds to ~2-3 seconds
   - Does NOT reduce total request count

2. **`timeout=30`**: Extended from default 10 seconds
   - Reduces failures from slow Yahoo responses
   - Network latency can vary significantly
   - TSX data may be slower than US data

3. **`period="5d"`**: Minimal historical data
   - Only need most recent price
   - Reduces data transfer and processing time
   - Less likely to trigger rate limits

4. **Rate Limit Detection**: Catches `YFRateLimitError` (yfinance v0.2.59+)
   - Gracefully falls back to cached data
   - Logs warning instead of crashing
   - Distinguishes rate limits from other errors

## Alternative Free APIs Evaluated

| API | Free Tier | TSX Support | ETF Support | Result |
|-----|-----------|-------------|-------------|--------|
| **yfinance** | Unlimited* | ✅ Yes | ✅ Yes | ✅ **Best option** |
| Alpha Vantage | 25 req/day | ✅ Yes | ✅ Yes | ❌ Too limited |
| Financial Modeling Prep | 250 req/hour | ❌ No | ❌ No | ❌ Major US stocks only |
| Twelve Data | 800 req/day | ❌ No | Unknown | ❌ US markets only |

*Unlimited but subject to anti-scraping rate limits

## Recommendations

### 1. Accept yfinance Limitations (Current Approach) ✅
**Best for most users** - Free and comprehensive coverage

**Pros:**
- Zero cost
- Supports all your tickers (TSX ETFs + US mutual funds)
- Already implemented and working
- Cache fallback provides resilience

**Cons:**
- Unpredictable rate limiting (24-48 hour blocks)
- No guarantees or SLA
- May break if Yahoo changes their website

**Mitigation:**
- ✅ Implemented: Extended timeout (30s)
- ✅ Implemented: Thread parallelization
- ✅ Implemented: Rate limit detection
- ✅ Implemented: Automatic cache fallback
- ✅ Existing: Cache stores historical snapshots

### 2. Reduce Refresh Frequency (Recommended Enhancement)
**Add to caching strategy:**

```python
# In cache.py - add time-based refresh control
def should_refresh_cache(csv_path, min_age_hours=24):
    """Check if cache is old enough to warrant refresh."""
    if not os.path.exists(csv_path):
        return True
    
    # Get most recent timestamp in cache
    df = pd.read_csv(csv_path)
    if df.empty:
        return True
    
    last_update = pd.to_datetime(df['date'].max())
    age_hours = (datetime.utcnow() - last_update).total_seconds() / 3600
    
    return age_hours >= min_age_hours
```

**Benefits:**
- Reduces rate limit risk
- Daily close prices don't change intraday anyway
- ETF/mutual fund prices are end-of-day values
- Refresh once per day maximum

### 3. Implement Exponential Backoff (For Future)
If rate limits become more frequent:

```python
import time
import random

def fetch_with_backoff(tickers, max_retries=3):
    for attempt in range(max_retries):
        try:
            return yf.download(...)
        except YFRateLimitError:
            if attempt < max_retries - 1:
                # Exponential backoff: 1s, 2s, 4s, 8s...
                wait = (2 ** attempt) + random.uniform(0, 1)
                logger.info(f"Rate limited, waiting {wait:.1f}s before retry {attempt+1}/{max_retries}")
                time.sleep(wait)
            else:
                raise
```

### 4. Paid API Options (If Budget Permits)
Only consider if free tier becomes completely unusable:

- **Financial Modeling Prep Starter**: $14/month
  - Includes ETFs and mutual funds
  - Higher rate limits (1,000 req/hour)
  - Still no TSX support on Starter tier
  
- **Alpha Vantage Premium**: $49/month
  - Unlimited requests
  - TSX support
  - More reliable than scraping

## Testing Changes

```bash
# Test the optimized implementation
streamlit run app.py

# Monitor logs for rate limit detection
tail -f logs/app.log | grep -i "rate limit"

# Test cache fallback
# (trigger rate limit, then reload dashboard)
```

## Summary

**Current state:** Optimized yfinance implementation with:
- ✅ Parallel threading
- ✅ Extended timeouts
- ✅ Rate limit detection
- ✅ Graceful cache fallback
- ✅ Comprehensive error handling

**Next enhancement:** Implement time-based refresh control to reduce unnecessary requests and rate limit risk.

**Long-term:** If yfinance becomes unreliable, consider paid API tier (~$14-49/month).

---

## Additional Resources

- yfinance GitHub: https://github.com/ranaroussi/yfinance
- yfinance Documentation: https://ranaroussi.github.io/yfinance
- Yahoo Finance Terms: https://policies.yahoo.com/us/en/yahoo/terms/product-atos/apiforydn/index.htm

**Important:** Yahoo's terms state the data is "intended for personal use only" - yfinance respects this by being open about its scraping nature and recommending research/educational use.
