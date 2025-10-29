# Scripts

Utility scripts for PortoDash maintenance and data management.

## consolidate_yahoo_csvs.py

**Recommended approach** - Consolidate manually downloaded Yahoo Finance CSV files into `historical.csv`.

This bypasses yfinance rate limiting by using manually downloaded data from Yahoo Finance's website.

**Usage:**
```bash
# 1. Download historical data for each ticker from Yahoo Finance
#    - Go to https://finance.yahoo.com/quote/{TICKER}/history
#    - Set date range (e.g., last 1 month)
#    - Click "Download" to get CSV
#    - Save as: data/{TICKER}.csv

# 2. Create data directory
mkdir data

# 3. Move/rename downloaded files to data/
#    - FFFFX.csv
#    - FBGRX.csv
#    - XEQT.TO.csv (or XEQT_TO.csv)
#    - etc.

# 4. Run consolidation script
conda activate portodash  # or: source .venv/bin/activate
python scripts/consolidate_yahoo_csvs.py --dir data/
```

**Features:**
- No API rate limiting (uses pre-downloaded files)
- Processes standard Yahoo Finance CSV format
- Automatically matches tickers to your portfolio
- Flexible filename formats (XEQT.TO.csv or XEQT_TO.csv)
- Shows progress and reports missing tickers

**Use cases:**
- Reliable way to initialize historical data
- Bypassing yfinance rate limits
- One-time historical data backfill

## backfill_snapshots.py

Backfill `historical.csv` with portfolio snapshots using yfinance API.

**Warning:** May encounter rate limiting with Yahoo Finance. Use `consolidate_yahoo_csvs.py` for more reliable results.

**Usage:**
```bash
# Activate your environment first
conda activate portodash  # or: source .venv/bin/activate

# Backfill last 30 days (default)
python scripts/backfill_snapshots.py

# Backfill custom number of days
python scripts/backfill_snapshots.py --days 90

# Adjust delay between requests (default 2 seconds)
python scripts/backfill_snapshots.py --days 30 --delay 3
```

**Features:**
- Fetches historical closing prices for each trading day
- Skips weekends automatically
- Rate-limiting with configurable delay (default 2s between requests)
- Appends to existing `historical.csv` or creates new file
- Shows progress with clear indicators

**Use cases:**
- Initialize historical data for a new portfolio
- Fill gaps in historical data
- Testing the performance chart with historical snapshots

**Note:** The script will prompt for confirmation before appending to an existing `historical.csv` file.
