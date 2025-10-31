# Development History

## Project Timeline

**Duration:** October 23-30, 2025 (7 days)  
**Commits:** 57 commits across 34+ PRs  
**Milestone:** v1.0-mvp tag created October 30, 2025

---

## Overview

PortoDash was built as a lightweight Streamlit portfolio tracker focused on making multi-currency portfolios legible by separating market returns from FX effects. The project emphasizes data provenance, graceful API fallback, and a clear UX that remains usable when external services are flaky.

**Key Innovation:** Dual-series performance chart that isolates FX impact from market returns, enabling like-for-like portfolio analysis across currencies.

---

## Major Development Phases

### Phase 1: Initial Build (Oct 23-25)

**Goal:** Basic portfolio tracker with multi-currency support

**Key Features:**

- Portfolio loading from `portfolio.json` (git-ignored for privacy)
- yfinance integration for live price fetching
- Multi-currency conversion with automatic USD/CAD exchange rate handling
- Account-centric data model (TFSA, RRSP, Roth IRA, non-registered)
- Session state caching to avoid unnecessary API calls
- Portfolio summary table with cost basis, current value, and gains
- Allocation pie chart (Plotly)
- Basic 30-day performance line chart

**Technical Decisions:**

- Streamlit for rapid prototyping and Python-only stack
- Pandas for data manipulation
- Plotly for interactive charts
- yfinance for market data (free, no API key required)

### Phase 2: Resilience & Provenance (Oct 26-27)

**Goal:** Handle API failures gracefully, improve data trust

**Key Features:**

- Rate limiting with 60-second cooldown + 1-hour backoff after rate limit errors
- Automatic fallback to cached prices when yfinance unavailable
- Data provenance indicator (Live/Cache/Mixed) with precise timestamps
- Session state improvements for better cache coherence
- Account filtering (by account name, holder, and account type)
- Account value breakdown table

**Bug Fixes:**

- Fixed timezone handling for price timestamps
- Improved error messages and user feedback
- Better handling of missing tickers

### Phase 3: FX Impact Analysis (Oct 28-29)

**Goal:** Separate market returns from FX effects for clearer insights

**Key Features (PR #33):**

- Dual-series performance chart:
  - **Market Performance (Fixed FX):** Shows portfolio returns using first day's FX rates
  - **Actual Performance (with FX):** Shows real portfolio value including FX changes
- Tooltip with both series for easy comparison
- Snapshot-based historical data from `historical.csv`
- Forward-fill for missing dates (market closures)

**Technical Implementation:**

- Calculate hypothetical portfolio value by freezing FX rates at Day 0
- Compare to actual portfolio value with real FX rates
- Requires historical snapshots with both price and FX data
- All calculations in CAD (home currency)

**Bug Fixes:**

- **Snapshot Deduplication Bug:** Clicking "Save snapshot" multiple times created duplicates
  - Solution: Renamed button to "Update daily snapshot"
  - Modified `fetch_and_store_snapshot()` to replace same-day snapshots
  - Added chart deduplication logic to handle existing duplicates
  - Standardized ISO8601 date parsing across all modules (viz.py, cache.py, data_fetch.py)

### Phase 4: Demo Mode (Oct 29-30)

**Goal:** Enable new users to try the app without setup, allow safe screenshots

**Key Features (PR #34):**

- Demo mode toggle script (`scripts/demo_mode.py`)
- Safe backup/restore mechanism with `.real` files
- Interactive CLI with confirmation prompts
- Status checking with `--status` flag
- Sample data generation script (`scripts/generate_demo_data.py`)
- 21 days of realistic demo historical data (Oct 1-29, 2025)
- Updated `portfolio.json.sample` with realistic holdings (~$130K portfolio)

**Technical Implementation:**

- Swaps `portfolio.json` and `historical.csv` with `.sample` versions
- Creates `.demo_mode` marker file for state tracking
- `fx_rates.csv` is NOT swapped (portfolio-agnostic data)
- Reversible toggle preserves real data in `*.real` backups
- README documentation with clear usage instructions

**Bug Fixes:**

- **FX Rates in Demo Mode:** Fixed missing "Fixed FX" line in performance chart
  - Root cause: `fx_rates.csv.sample` only had 2 days of data
  - Solution: Copy full `fx_rates.csv` to sample (30 days of USD/CAD rates)
  - Removed `fx_rates.csv` from demo mode swap logic (it's portfolio-agnostic)

### Phase 5: Public Release Preparation (Oct 30)

**Goal:** Make repository ready for public sharing

**Changes:**

- Added MIT LICENSE
- Updated `.gitignore` with demo mode entries (`.demo_mode`, `*.real`)
- Added badges to README (Python 3.11+, MIT License, Streamlit 1.30+)
- Made Table of Contents functional with markdown anchor links
- Comprehensive README rewrite with clear structure and examples
- Git tag created: `v1.0-mvp`

### Phase 6: UX Polish & Metrics (Oct 30)

**Goal:** Align dashboard visuals with fintech styling while elevating FX context and clarity.

**Key Enhancements:**

- Injected modern theme helpers (`inject_modern_fintech_css`, typography hierarchy) and new layout utilities (`render_metric_card`, `render_metric_grid`) to standardize headings, tables, and KPI spacing.
- Reworked holdings summary into a responsive card grid, highlighting positions count, top allocation, average gain, and the new FX Exposure metric that surfaces non-CAD share plus the top foreign currency weight.
- Harmonized empty-state, rate-limit, and scheduler copy so every message carries a professional tone and clear action guidance.
- Extended scheduler health detection to report log freshness, system process checks, and next-run status with explicit instructions when intervention is required.

**Follow-up Tasks:**

- Refresh README screenshots to capture the new theme and KPI cards.
- Document typography tokens and card spacing guidelines in future design docs if the Streamlit implementation evolves.

### Phase 7: Interactive UX Refinements (Oct 30, continued)

**Goal:** Complete Phase 2 UX backlog with smart interaction patterns and cleaner information architecture.

**Key Features:**

- **Context-Aware Refresh (Issue #39):**
  - Moved refresh button from sidebar to Data Management section alongside snapshot controls
  - Removed complex countdown timers and status messages from sidebar
  - Simplified to automatic fetch on load + manual refresh when needed
  - Clear button states: enabled (normal), disabled with tooltip (rate limited or cooldown)

- **Collapsible Filter Sidebar (Issue #41):**
  - Filter groups wrapped in `st.expander` with count badges (e.g., "Accounts (5)")
  - Accounts expander open by default, Holders and Types collapsed
  - "Reset All Filters" button properly resets both visual display and filter state
  - Session state management via widget keys to avoid conflicts
  - Wider sidebar (20rem default) for better account name readability

- **Enhanced Holdings Table (Issue #40):**
  - New "Fund/ETF" column showing "TICKER — Full Name" format
  - Persistent fund name cache in `fund_names.json` (git-ignored)
  - Smart caching: fetch from yfinance only once per ticker, ever
  - Sample data in `fund_names.json.sample` for demo mode
  - Module `portodash/fund_names.py` handles all name fetching and caching
  - Compact numeric columns (width='small') to maximize space for fund names

**Technical Implementation:**

- Session state now uses widget keys directly (`filter_nicknames`, etc.) to avoid default/key conflicts
- Fund names fetched using `yf.Ticker(ticker).info['longName']` with fallback to `shortName` or ticker
- Cache persists across sessions as JSON for instant loading
- Sidebar width increased via CSS: `width: 20rem !important`
- Filter expanders styled with custom CSS for borders and hover states

**Bug Fixes:**

- Fixed reset button by updating widget keys in session state before rerun
- Resolved Streamlit warning about mixing `default` parameter with session state keys
- Account name display now uses em dash (—) for cleaner separation

---

## Architecture Decisions

### Data Model: Account-Centric

**Decision:** Organize holdings by account with metadata (nickname, holder, type, base_currency)

**Rationale:**

- Matches how investors think about their portfolios
- Enables account-level filtering and reporting
- Supports tax-advantaged account tracking (TFSA, RRSP, etc.)
- Clear holder attribution for joint portfolios

### Currency Handling

**Decision:** CAD as home currency, but preserve native currency context per holding

**Rationale:**

- Avoids conversion ambiguity ("Is this value in USD or CAD?")
- Shows both native and home currency values side-by-side
- Enables FX impact analysis by comparing fixed vs. actual rates
- Transparent exchange rate display builds trust

### Caching Strategy

**Decision:** Multi-layer caching with session state + CSV fallback

**Rationale:**

- Session state: Fast in-memory cache for active session
- `historical.csv`: Persistent fallback when API unavailable
- Explicit "Last Updated" + provenance indicator builds user trust
- 60-second cooldown prevents API thrashing
- 1-hour backoff after rate limit respects API limits

### Snapshot Architecture

**Decision:** Append-only CSV with manual/scheduled snapshots

**Rationale:**

- Simple, auditable data format
- No database setup required
- Easy to version control (though git-ignored for privacy)
- Enables historical charts and performance analysis
- Standalone scheduler decouples data collection from UI

### Demo Mode Design

**Decision:** File swapping with safe backups rather than separate config

**Rationale:**

- Zero code changes required (app doesn't know about demo mode)
- Safe backup mechanism with `.real` files
- Interactive script prevents accidental data loss
- Easy to verify current mode with `--status`
- Sample files tracked in git for easy distribution

---

## Technical Stack

### Core Dependencies

- **Streamlit:** Interactive web UI framework
- **yfinance:** Market data fetching (free, no API key)
- **pandas:** Data manipulation and analysis
- **Plotly:** Interactive charts
- **APScheduler:** (Planned) Automated snapshot scheduling

### File Structure

```text
portodash/
├── app.py                          # Main Streamlit application
├── portodash/
│   ├── data_fetch.py              # Price fetching and snapshot management
│   ├── viz.py                     # Chart generation (Plotly)
│   ├── cache.py                   # Price caching from historical.csv
│   └── scheduler.py               # (Skeleton) Snapshot scheduling
├── scripts/
│   ├── demo_mode.py               # Demo mode toggle script
│   ├── generate_demo_data.py      # Demo data generation
│   ├── run_scheduler.py           # Standalone scheduler runner
│   └── create_conda_env.sh        # Conda environment helper
├── portfolio.json                 # User's portfolio (git-ignored)
├── portfolio.json.sample          # Sample portfolio for demo mode
├── historical.csv                 # Historical snapshots (git-ignored)
├── historical.csv.sample          # Sample historical data
├── fx_rates.csv                   # USD/CAD exchange rates (git-ignored)
└── fx_rates.csv.sample            # Sample FX rates (30 days)
```

### Key Data Files

**portfolio.json** (git-ignored, user-specific):

- Account-centric structure
- Holdings with ticker, shares, cost_basis, currency
- Account metadata: nickname, holder, type, base_currency

**historical.csv** (git-ignored, append-only):

- Columns: date, ticker, price, currency
- One row per ticker per snapshot
- Powers performance charts and caching fallback

**fx_rates.csv** (portfolio-agnostic, shared):

- Columns: date, usd_cad
- Daily USD/CAD exchange rates
- Used for multi-currency conversions and FX impact analysis

---

## Key Learnings

### 1. Data Provenance is Critical

Users need to know if data is live or cached. The "Last Updated" timestamp + Source indicator (Live/Cache/Mixed) builds trust and prevents confusion when API is down.

### 2. Graceful Degradation > Perfect Uptime

yfinance has rate limits and occasional failures. Automatic fallback to cached prices keeps the app usable even when external APIs are flaky.

### 3. ISO8601 Date Parsing Must Be Explicit

Mixed date formats in CSV files caused AttributeErrors. Solution: Always specify `format='ISO8601'` in `pd.to_datetime()` calls. For backward compatibility with simple dates, use `format='mixed'`.

### 4. Timezone-Aware Datetimes for Comparisons

Comparing timezone-naive and timezone-aware datetimes raises TypeError. Solution: Normalize all datetimes to UTC with `tz_localize('UTC')` before comparisons.

### 5. Demo Mode Requires Portfolio-Agnostic Data

FX rates are the same for everyone, so no need to swap them. This simplifies demo mode and ensures the "Fixed FX" chart works correctly with sample data.

### 6. GitHub CLI Auth ≠ Git Config

`gh` CLI uses separate authentication from git. Use `gh auth login` to switch accounts for PR creation, even if git config is already set.

### 7. Feature Branches > Direct Commits

Always create feature branch before first commit. If you accidentally commit to main, use `git reset --hard HEAD~1` to move commit to feature branch.

---

## Testing Approach

### Manual Testing Workflow

1. **Real Data → Demo Data → Real Data:**
   - Start with real portfolio
   - Toggle to demo mode
   - Verify all features work with sample data
   - Toggle back to real mode
   - Verify real data restored correctly

2. **API Failure Simulation:**
   - Disconnect network
   - Click "Refresh prices"
   - Verify fallback to cached prices
   - Check "Last Updated" shows cached timestamp

3. **Rate Limit Handling:**
   - Rapid refresh clicks trigger 60-second cooldown
   - Wait for cooldown, verify refresh works again
   - If rate limited by yfinance, verify 1-hour backoff

### Edge Cases Handled

- Missing tickers in yfinance
- Market closures (weekends, holidays)
- Duplicate snapshots (same date, multiple times)
- Mixed date formats in CSV files
- Empty historical.csv (first run)
- Missing fx_rates for historical dates

---

## Known Limitations

### Current State (v1.0-mvp)

1. **Single Home Currency:** Only CAD supported as home currency (USD/other not yet configurable)
2. **30-Day Window:** Performance chart fixed at 30 days (no YTD, 1Y, 3Y options yet)
3. **Manual Snapshots:** User must click "Update daily snapshot" (scheduler exists but not integrated)
4. **Limited Ticker Support:** Relies on yfinance coverage (some mutual funds unavailable)
5. **No Contribution Tracking:** Can't separate portfolio growth from cash contributions
6. **Basic Styling:** Uses default Streamlit theme (UX polish needed)

### Future Enhancements (Roadmap)

- Configurable home currency
- Extended date ranges (YTD, 1Y, 3Y, Max)
- Automated scheduler integration with APScheduler
- Contribution flow tracking
- Benchmarking against market indices
- CSV import from brokers
- Enhanced UX with custom Streamlit theming
- Mobile-responsive design

---

## Git Workflow

### Branch Strategy

- `main`: Production-ready code
- `feature/*`: Feature branches for new work
- PRs created by `regisca-bot` for automated change tracking

### Commit Message Convention

- `feat:` New features
- `fix:` Bug fixes
- `docs:` Documentation changes
- `chore:` Maintenance tasks (dependencies, config, etc.)
- `refactor:` Code restructuring without functional changes

### PR Workflow

1. Create feature branch: `git checkout -b feature/description`
2. Make changes and commit
3. Push to origin: `git push -u origin feature/description`
4. Create PR with `gh pr create` (authenticated as regisca-bot)
5. Review and merge on GitHub
6. Pull main and delete feature branch: `git checkout main && git pull && git branch -d feature/description`

---

## Notable PRs

### PR #30: Portfolio UI and Data Model Improvements

- Multi-account filtering enhancements
- Holdings breakdown by account
- Improved provenance display

### PR #33: FX Impact Analysis (Dual-Series Chart)

- Market Performance (Fixed FX) vs Actual Performance (with FX)
- Clean separation of market returns from FX effects
- Snapshot-based historical data

### PR #34: Demo Mode

- Safe data swapping for screenshots and testing
- Sample data generation scripts
- 21 days of realistic demo historical data
- Fixed FX rates bug (missing data in sample file)

---

## Next Phase: UX Enhancement

### Goals

- Polish visual design (potentially match Wealthsimple aesthetic)
- Improve chart readability and interactivity
- Better mobile responsiveness
- Custom Streamlit theming
- Consider React migration if Streamlit limitations hit

### Design Inspiration: Wealthsimple

- Clean sans-serif typography (Grilli Type)
- High contrast (black on white)
- Mint green accent color (#00D46A)
- Generous whitespace
- Rounded corners (8-12px)
- Minimal shadows

### Starting Point for Next Chat

> "I'm working on PortoDash (github.com/RegisCA/portodash), a Streamlit portfolio tracker. The MVP is complete with demo mode, FX impact charts, and multi-currency support. Now I want to polish the UX, potentially matching Wealthsimple's clean design aesthetic. The app is at commit 6c085f7 (v1.0-mvp tag)."

---

## Development Tools & Environment

### Python Environment

- **venv** or **Conda** for dependency isolation
- Python 3.11+ required
- Apple Silicon: Conda recommended (prebuilt pyarrow binaries)

### Key Dependencies

```text
streamlit>=1.30
yfinance
pandas
plotly
APScheduler (planned)
psutil (optional, for scheduler detection)
```

### Development Workflow

```bash
# Activate environment
source .venv/bin/activate  # or: conda activate portodash

# Run app
streamlit run app.py

# Run scheduler (standalone)
python scripts/run_scheduler.py

# Toggle demo mode
python scripts/demo_mode.py
```

---

## Accessibility Guidelines

### WCAG 2.1 Level AA Compliance

PortoDash follows WCAG 2.1 Level AA accessibility standards to ensure the dashboard is usable by everyone, including users with disabilities.

**Key Requirements:**

- **Color Contrast:** Minimum 4.5:1 for normal text, 3:1 for large text
- **Keyboard Navigation:** All interactive elements accessible via keyboard
- **Screen Readers:** ARIA labels on charts and interactive controls
- **Focus Indicators:** Visible focus outlines (3px solid, 2px offset)
- **Reduced Motion:** Respects `prefers-reduced-motion` media query

### Testing Checklist for PRs

Before submitting a PR that adds or modifies UI elements, verify:

1. **Keyboard Navigation:**
   - [ ] Tab through all interactive elements in logical order
   - [ ] All buttons, links, and filters reachable via keyboard
   - [ ] Focus indicators visible on all interactive elements

2. **Color Contrast (if adding colors):**
   - [ ] Run `check_color_contrast()` from `portodash/accessibility.py`
   - [ ] Normal text: minimum 4.5:1 contrast ratio
   - [ ] Large text (18pt+ or 14pt+ bold): minimum 3:1 contrast ratio
   - [ ] Use online tools: [WebAIM Contrast Checker](https://webaim.org/resources/contrastchecker/)

3. **ARIA Labels (if adding charts or interactive elements):**
   - [ ] Charts wrapped in semantic HTML with `role="img"` and descriptive `aria-label`
   - [ ] Filter controls have clear `aria-label` attributes explaining their purpose
   - [ ] Buttons have descriptive labels or `aria-label` if icon-only

4. **Screen Reader Testing (recommended):**
   - [ ] Test with VoiceOver (macOS): `Cmd+F5` to enable
   - [ ] Verify all content is announced correctly
   - [ ] Check skip navigation link works (appears on Tab)

5. **Print Stylesheet:**
   - [ ] Open print preview (`Cmd+P` or browser menu)
   - [ ] Verify interactive elements (buttons, filters) are hidden
   - [ ] Check content is readable and properly formatted

### Code Examples

**Adding ARIA Labels to Charts:**

```python
# Wrap Plotly chart in semantic HTML with ARIA label
st.markdown('<div role="img" aria-label="Allocation pie chart showing portfolio distribution across funds">', unsafe_allow_html=True)
st.plotly_chart(chart_figure, use_container_width=True)
st.markdown('</div>', unsafe_allow_html=True)
```

**Adding ARIA Labels to Interactive Controls:**

```python
# Wrap filter controls with descriptive ARIA label
st.markdown('<div aria-label="Account filter: Select one or more accounts to filter the portfolio view">', unsafe_allow_html=True)
selected_accounts = st.multiselect("Select accounts", options=all_accounts)
st.markdown('</div>', unsafe_allow_html=True)
```

**Validating Color Contrast:**

```python
from portodash.accessibility import check_color_contrast

# Check if new color meets WCAG AA standards
is_valid, ratio = check_color_contrast('#1a1a1a', '#00ff88')
print(f"Contrast ratio: {ratio:.2f}:1 — {'PASS' if is_valid else 'FAIL'}")
```

### Accessibility Resources

- **WCAG 2.1 Guidelines:** https://www.w3.org/WAI/WCAG21/quickref/
- **WebAIM Contrast Checker:** https://webaim.org/resources/contrastchecker/
- **Keyboard Navigation Testing:** https://webaim.org/articles/keyboard/
- **VoiceOver User Guide:** https://support.apple.com/guide/voiceover/welcome/mac
- **Project Documentation:** `ACCESSIBILITY.md` in repository root

### Accessibility Modules

- **portodash/accessibility.py:** Color contrast validation, ARIA label generation
- **portodash/theme.py:** Accessibility CSS injection (focus styles, skip links, print stylesheet)

For detailed accessibility feature documentation, see `ACCESSIBILITY.md`.

---

## Credits

Built primarily with **GitHub Copilot** (Claude Sonnet 4.5) over 7 days in October 2025. All commits made through `@regisca-bot` account to properly track AI-assisted development.

Core technologies: Streamlit, yfinance, pandas, Plotly.

---

## Version History

### v1.0-mvp (October 30, 2025)

**Commit:** 6c085f7  
**Tag:** v1.0-mvp

**Features:**

- Multi-currency portfolio tracking with CAD home currency
- FX impact analysis (Market vs Actual performance)
- Demo mode for safe exploration
- Rate limiting and graceful API fallback
- Data provenance indicators (Live/Cache/Mixed)
- Account filtering by name, holder, and type
- Snapshot-based historical tracking
- MIT licensed and ready for public sharing

**Stats:**

- 57 commits
- 34+ PRs
- 7 days of development
- ~3,000 lines of Python code
- 5 core modules + 3 utility scripts

---

*This document will be referenced at the start of the UX enhancement phase to provide context for future development.*
