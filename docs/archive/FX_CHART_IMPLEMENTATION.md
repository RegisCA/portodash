# FX Impact Chart Implementation

## Overview
Implemented dual-line performance chart showing market performance vs. actual CAD returns with FX impact.

## Changes Made

### 1. Created `fx_rates.csv.sample`
Template showing required format:
```csv
date,usd_cad
2025-09-29,1.3500
2025-09-30,1.3520
```

### 2. Updated `.gitignore`
Added protection for FX rates data:
- `fx_rates.csv` (private)
- `!fx_rates.csv.sample` (exception for template)

### 3. Enhanced `make_snapshot_performance_chart()` in `viz.py`
**New parameters:**
- `fx_csv_path`: Optional path to fx_rates.csv

**New logic:**
- Loads FX rates from CSV if available
- Detects currency from ticker (`.TO` suffix = CAD, otherwise USD)
- Calculates two portfolio value series:
  1. **Fixed FX**: Uses FX rate from start of period (day 0)
  2. **Actual FX**: Uses daily FX rates
- Plots both lines when FX data available
- Falls back to single line if no FX data

**Chart styling:**
- Fixed FX line: Blue, dashed (#2E86AB)
- Actual FX line: Purple, solid (#A23B72)
- Horizontal legend at top

### 4. Updated `app.py`
- Added `FX_CSV` constant pointing to `fx_rates.csv`
- Pass `fx_csv_path=FX_CSV` to chart function

## How to Use

### Step 1: Populate FX Rates
Create `fx_rates.csv` in project root with format:
```csv
date,usd_cad
2024-10-01,1.3500
2024-10-02,1.3520
...
```

**Tips:**
- Date format: YYYY-MM-DD
- Rate direction: USD → CAD (1.35 means $1 USD = $1.35 CAD)
- Cover at least the same date range as `historical.csv`
- Download from Bank of Canada or Yahoo Finance

### Step 2: Run Dashboard
```bash
streamlit run app.py
```

### Step 3: View Chart
The performance chart will show:
- **Blue dashed line**: Market performance at fixed FX rate (from 30 days ago)
  - Shows pure portfolio/market movement
  - Removes FX noise
- **Purple solid line**: Actual performance with daily FX rates
  - Shows real CAD returns
  - Includes FX impact

## Currency Detection
- **TSX tickers** (ending in `.TO`): Assumed CAD, no conversion
- **US tickers**: Assumed USD, converted using FX rates

## Fallback Behavior
If `fx_rates.csv` is missing or has errors:
- Chart falls back to single line
- Uses `portfolio_value` directly from `historical.csv`
- No errors, graceful degradation

## Testing Checklist
- [ ] Create minimal `fx_rates.csv` with 3-5 days
- [ ] Run dashboard and check chart displays
- [ ] Verify two lines appear (if FX data present)
- [ ] Check line colors and styles (blue dashed vs purple solid)
- [ ] Hover over chart to verify values make sense
- [ ] Compare fixed FX vs actual FX lines (actual should vary more)
- [ ] Remove `fx_rates.csv` and verify fallback to single line

## Next Steps
1. User populates `fx_rates.csv` with historical data
2. Test with real 30-day dataset
3. Adjust styling/labels if needed
4. Create PR for feature branch
