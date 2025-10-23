# PortoDash

Lightweight Streamlit portfolio tracker using yfinance, pandas and Plotly.

Features (Phase 1):

- Load holdings from `portfolio.json`
- Fetch current prices using `yfinance` on page load
- Portfolio summary table with cost, current value and gains
- Allocation pie chart (Plotly)
- 30-day performance line chart (Plotly)
- Save a snapshot to `historical.csv` and download historical CSV

Run locally

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

2. Start the app:

```bash
streamlit run app.py
```

Conda (recommended on macOS Apple Silicon)
-----------------------------------------

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
