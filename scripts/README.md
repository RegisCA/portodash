# Scripts

Utility scripts for PortoDash maintenance and data management.

## backfill_snapshots.py

Backfill `historical.csv` with portfolio snapshots from past days using historical market prices from yfinance.

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
