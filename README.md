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
            "ticker": "XEQT.TO",  # Yahoo Finance ticker symbol
            "shares": 100.5,      # Number of shares (float)
            "cost_basis": 25.75   # Average cost per share
        }
    ]
}
```

Notes:
- Use `.TO` suffix for TSX-listed securities (e.g., "XEQT.TO")
- US-listed securities need no suffix (e.g., "SPY")
- The `portfolio.json` file is git-ignored to keep your holdings private
- Historical snapshots are saved to `historical.csv` (also git-ignored)

## Installation

## Quick Start

1. Create and activate a Python environment (recommended). On macOS use `python3` (many systems don't have a `python` alias):

```bash

```bash
# check you have python3 available
which python3 || echo "python3 not found — install with: brew install python@3.11"

# create and activate a venv
python3 -m venv .venv
source .venv/bin/activate

# install dependencies using the venv's pip
python -m pip install -r requirements.txt
```

2. Start the app:

```bash
streamlit run app.py
```

## Conda (recommended on macOS Apple Silicon)

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

Next steps (Phase 2/3):

- Schedule daily snapshots with APScheduler (skeleton in `portodash/scheduler.py`)
- Add retry/fallback logic and caching
- Add more charts and date range filters
