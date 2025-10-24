# PortoDash

Lightweight Streamlit portfolio tracker using yfinance, pandas and Plotly.

Features (Phase 1):

- Load holdings from `portfolio.json` (private file, not tracked in git)
- Fetch current prices using `yfinance` on page load
- Portfolio summary table with cost, current value and gains
- Allocation pie chart (Plotly)
- 30-day performance line chart (Plotly)
- Save a snapshot to `historical.csv` and download historical CSV

## Configuration

1. Create your portfolio configuration:

```bash
# Copy the sample config
cp portfolio.json.sample portfolio.json

# Edit portfolio.json with your holdings
```

The portfolio.json format:

```json
{
    "holdings": [
        {
            "ticker": "XEQT.TO",     # Yahoo Finance ticker symbol
            "shares": 100.5,         # Number of shares (float)
            "cost_basis": 25.75,     # Average cost per share
            "currency": "CAD",       # Currency code (optional, defaults to CAD)
            "account": "TFSA"        # Account name (optional, for grouping)
        }
    ]
}
```

Notes:

- Use `.TO` suffix for TSX-listed securities (e.g., "XEQT.TO")
- US-listed securities need no suffix (e.g., "SPY")
- `currency`: Optional field for multi-currency support. Defaults to CAD if omitted. Exchange rates are fetched automatically and values are displayed in CAD.
- `account`: Optional field to track holdings across multiple accounts (e.g., "TFSA", "RRSP", "401k"). Use the account filter in the UI to view specific accounts or all accounts together.
- The `portfolio.json` file is git-ignored to keep your holdings private
- Historical snapshots are saved to `historical.csv` (also git-ignored)

## Installation

### Quick Start with venv

1. Create and activate a Python environment (recommended). On macOS use `python3` (many systems don't have a `python` alias):

```bash
# check you have python3 available
which python3 || echo "python3 not found — install with: brew install python@3.11"

# create and activate a venv
python3 -m venv .venv
source .venv/bin/activate

# install dependencies using the venv's pip
python -m pip install -r requirements.txt
```

1. Start the app:

```bash
streamlit run app.py
```

### Conda (recommended on macOS Apple Silicon)

If pip is attempting to build heavy compiled packages (for example `pyarrow`) you can avoid that by using a conda environment which provides prebuilt binaries on macOS arm64. A ready `environment.yml` is included.

```bash
# install Miniforge (only if you don't have conda)
# https://github.com/conda-forge/miniforge

# create the environment
conda env create -f environment.yml
conda activate portodash

# run the app
streamlit run app.py
```

Or use the helper script:

```bash
./scripts/create_conda_env.sh
```

## Features

### Current Features

- **Multi-currency support**: Holdings in different currencies (USD, CAD, etc.) are automatically converted to CAD base currency with transparent exchange rate display
- **Multi-account tracking**: Filter and view holdings across different accounts (TFSA, RRSP, 401k, etc.)
- **Rate limiting**: Intelligent 60-second cooldown between price refreshes with extended 1-hour cooldown when rate limited
- **Session state caching**: Prices cached in session to avoid unnecessary API calls
- **Graceful fallback**: Automatically uses cached prices when yfinance is unavailable
- **Account breakdown**: View portfolio value grouped by account
- **Data provenance**: Clear indication of data source (Live/Cache/Mixed) and last update timestamp

### Roadmap (Phase 2/3)

- Schedule daily snapshots with APScheduler (skeleton in `portodash/scheduler.py`)
- Add more charts and date range filters
- Performance analytics and benchmarking

## Data Freshness and Provenance

The dashboard displays a **"Last Updated"** timestamp showing when the portfolio prices were last fetched. This timestamp reflects the actual time the data was retrieved, whether from:

- **Live**: All prices were fetched from yfinance in real-time.
- **Cache**: All prices were loaded from the most recent local snapshot (within the cache TTL, default 24 hours).
- **Mixed**: Some prices came from live fetch, others from cache (e.g., if some tickers failed to fetch).

The source indicator appears next to the "Last Updated" timestamp in the dashboard. When you click **"Refresh prices"**, both the timestamp and source are updated based on the actual data retrieval result.

If yfinance is unavailable or fails, the app automatically falls back to the most recent cached prices from `historical.csv`, ensuring you always see your portfolio data even during network issues.

## Scheduler (standalone)

You can run the scheduler as a separate process to save daily snapshots to `historical.csv` without running the Streamlit UI. The scheduler writes a small status file `logs/scheduler_status.json` which the Streamlit app reads to show scheduler status.

Recommended quick run:

```bash
# (activate your environment first)
python scripts/run_scheduler.py
```

Notes:

- The scheduler uses the `America/Toronto` timezone by default and schedules a weekday job at 16:30 local time.
- The scheduler will append snapshots to `historical.csv` and write logs to `logs/scheduler_YYYYMMDD.log`.
- The scheduler also writes `logs/scheduler_status.json` with keys: `last_run`, `next_run`, `job_running`, `last_error`.

## Helpful tooling

- `psutil` (optional): if installed, the dashboard can detect the scheduler process directly. Install with:

```bash
python -m pip install psutil
```

## Service / boot integration (macOS LaunchAgent example)

Below is a minimal LaunchAgent plist you can use to run the scheduler on login. Save it as `~/Library/LaunchAgents/com.yourname.portodash.scheduler.plist` and `launchctl load` it.

Replace `/path/to` with your project path and adjust the Python interpreter if you use a conda env.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
    <dict>
        <key>Label</key>
        <string>com.yourname.portodash.scheduler</string>
        <key>ProgramArguments</key>
        <array>
            <string>/usr/bin/python3</string>
            <string>/Users/yourname/Projects/portodash/scripts/run_scheduler.py</string>
        </array>
        <key>RunAtLoad</key>
        <true/>
        <key>KeepAlive</key>
        <true/>
        <key>StandardOutPath</key>
        <string>/Users/yourname/Projects/portodash/logs/scheduler_launchtmp.out</string>
        <key>StandardErrorPath</key>
                <string>/Users/yourname/Projects/portodash/logs/scheduler_launchtmp.err</string>
                </dict>
</plist>
```

## Development

Commits to this repository are made through a bot account (@regisca-bot) to properly track automated changes.

