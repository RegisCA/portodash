# Changelog

All notable changes to PortoDash will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.0] - 2025-10-31

### Added

- **Responsive Widescreen Layout** (PR #54)
  - Reorganized content with better information hierarchy for widescreen displays
  - Portfolio Insights moved above charts to be immediately visible without scrolling
  - Key metrics (Positions, Top Holding, FX Exposure, Average Gain) now on first page
  - Dynamic table heights that adapt to content (200-600px range)
  - Context-aware section headers that change based on filter state

### Changed

- **Information Hierarchy Redesign** (PR #54)
  - New order: Portfolio Overview → Portfolio Insights → Allocation → Performance → Holdings → Data Management
  - Allocation chart and Performance chart moved above Holdings tables
  - Creates logical narrative: high-level values → key insights → visual story → detailed tables
  - Addresses UX issue where critical insights were buried below large tables

- **Context-Aware Headers** (PR #54)
  - Headers adapt based on filter state to reflect current view
  - No filters: "Portfolio Overview" and "Portfolio Insights"
  - Filters active: "Overview" and "Insights" (drops "Portfolio" for accuracy)
  - More precise labeling when viewing filtered subsets

- **Dynamic Table Heights** (PR #54)
  - All Holdings table height now calculated based on number of rows
  - Formula: `rows × 35px + 42px header + 20px padding`
  - Minimum 200px, maximum 600px with internal scrolling
  - Eliminates wasted space when filtering to small subsets

- **Reduced Vertical Whitespace** (PR #54)
  - Removed horizontal rule before Portfolio Overview section
  - Optimized spacing to fit more content above the fold
  - Portfolio Insights cards now visible on first page with no scrolling

### Fixed

- **Context-Aware Headers Bug** (PR #54)
  - Fixed headers always showing "Overview" even when no filters active
  - Now correctly checks session state to determine filter status
  - Compares selected item count vs total available items

## [1.1.0] - 2025-10-31

### Added

- **WCAG 2.1 Level AA Accessibility Compliance** (PR #52, Issue #47)
  - Color contrast validation module (`portodash/accessibility.py`)
  - All theme colors validated: Primary (17.4:1), Neutral (4.83:1), Links (5.74:1)
  - Keyboard navigation with visible focus indicators (3px solid outline, 2px offset)
  - Skip navigation link for screen readers ("Skip to main content")
  - ARIA labels on all charts (allocation pie, performance line chart)
  - ARIA labels on all interactive elements (filters, sliders, buttons)
  - Print-friendly stylesheet (hides buttons, optimizes layout)
  - Reduced motion support (`prefers-reduced-motion` media query)
  - High contrast mode support (`prefers-contrast` media query)
  - Semantic HTML wrappers for charts (`role="img"` with descriptive labels)
  - Accessibility documentation (`ACCESSIBILITY.md`)
  - Accessibility guidelines in `DEVELOPMENT.md` with PR checklist

- **Enhanced Holdings Table** (PR #41, Issue #40)
  - Fund/ETF names displayed alongside tickers ("TICKER — Full Name" format)
  - Persistent fund name cache in `fund_names.json` (git-ignored)
  - Smart caching: fetch from yfinance only once per ticker, ever
  - Sample data in `fund_names.json.sample` for demo mode
  - New module `portodash/fund_names.py` for name fetching and caching

- **Collapsible Filter Sidebar** (PR #41, Issue #41)
  - Filter groups wrapped in `st.expander` with count badges (e.g., "Accounts (5)")
  - Accounts expander open by default, Holders and Types collapsed
  - Wider sidebar (20rem) for better account name readability
  - Custom expander styling with borders and hover states

- **Context-Aware Refresh UI** (PR #39, Issue #39)
  - Refresh button moved from sidebar to Data Management section
  - Simplified button states: enabled or disabled with tooltip
  - Clear messaging for rate limits and cooldown periods
  - Removed complex countdown timers from sidebar

- **Portfolio Metrics Cards** (PR #40)
  - New metric card grid showing positions count, top allocation, average gain
  - FX Exposure metric highlights non-CAD share and top foreign currency weight
  - Responsive card layout with modern fintech styling

- **Fintech Theme Utilities** (PR #41)
  - `inject_modern_fintech_css()` for consistent typography hierarchy
  - `render_metric_card()` and `render_metric_grid()` layout helpers
  - Standardized section headers and table styling

### Changed

- **Improved Filter Reset** (PR #41)
  - "Reset All Filters" button now properly resets both visual display and filter state
  - Session state management via widget keys to avoid conflicts
  - Fixed Streamlit warning about mixing `default` parameter with session state keys

- **Enhanced Messaging** (PR #39)
  - Tightened copy throughout app for refresh flows, scheduler health, and snapshots
  - Professional tone with clear action guidance
  - Extended scheduler health detection with log freshness and process checks

### Fixed

- **Print Stylesheet Bug** (PR #52)
  - Buttons no longer visible in print preview
  - Added multiple button selectors (`.stButton > button`, `button`) with `visibility: hidden` backup

- **Pandas Warning** (PR #52)
  - Fixed `SettingWithCopyWarning` in `viz.py`
  - Changed from `d = df[df['ticker'] != 'TOTAL']` to explicit `.copy()` call

### Documentation

- Added `ACCESSIBILITY.md` with comprehensive accessibility feature documentation
- Updated `DEVELOPMENT.md` with accessibility guidelines and PR testing checklist
- Updated `README.md` with v1.1 highlights and WCAG 2.1 Level AA badge
- Created `CHANGELOG.md` to track version history

---

## [1.0.0] - 2025-10-30

### Added

- **Multi-Currency Portfolio Tracking**
  - CAD home currency with native currency context per holding
  - Automatic USD/CAD exchange rate handling
  - Clear display of both native and home currency values

- **FX Impact Analysis** (PR #33)
  - Dual-series performance chart: Market Performance (Fixed FX) vs Actual Performance (with FX)
  - Clean separation of market returns from FX effects
  - Snapshot-based historical data from `historical.csv`
  - Forward-fill for missing dates (market closures)

- **Account-Centric Data Model**
  - Multiple account support (TFSA, RRSP, Roth IRA, non-registered)
  - Account metadata: nickname, holder, type, base_currency
  - Multi-account filtering by name, holder, and type

- **Data Provenance & Resilience**
  - Live/Cache/Mixed indicator with precise timestamps
  - Automatic fallback to cached prices when yfinance unavailable
  - Rate limiting: 60-second cooldown + 1-hour backoff after rate limit
  - Session state caching to avoid unnecessary API calls

- **Demo Mode** (PR #34)
  - Safe data swapping with `.real` file backups
  - Sample data generation script (`scripts/generate_demo_data.py`)
  - 21 days of realistic demo historical data
  - Interactive CLI with confirmation prompts
  - Status checking with `--status` flag

- **Snapshot Management**
  - Append-only `historical.csv` with manual/scheduled snapshots
  - Standalone scheduler with APScheduler (`scripts/run_scheduler.py`)
  - Snapshot deduplication (replaces same-day snapshots)
  - macOS LaunchAgent example for automated daily snapshots

- **Interactive Charts**
  - Allocation pie chart with Plotly
  - 30-day performance line chart with dual-series FX analysis
  - Hover tooltips with detailed information

### Technical Features

- Streamlit web UI framework
- yfinance for market data (free, no API key required)
- pandas for data manipulation
- Plotly for interactive charts
- APScheduler for automated snapshots
- Session state caching for performance
- Git-ignored sensitive files for privacy

### Documentation

- Comprehensive `README.md` with installation, configuration, and usage
- `DEVELOPMENT.md` with full project timeline and technical decisions
- MIT License for open-source distribution
- Sample data files for easy onboarding

### Bug Fixes

- Fixed timezone handling for price timestamps
- Fixed snapshot deduplication bug (clicking "Save snapshot" multiple times created duplicates)
- Fixed FX rates in demo mode (missing data in sample file)
- Standardized ISO8601 date parsing across all modules

---

## [Unreleased]

### Planned Features

- Configurable home currency (USD, EUR, etc.)
- Extended date ranges (YTD, 1Y, 3Y, Max)
- Contribution flow tracking
- Benchmarking against market indices
- CSV import from brokers
- Mobile-responsive design improvements

---

[1.2.0]: https://github.com/RegisCA/portodash/compare/v1.1.0...v1.2.0
[1.1.0]: https://github.com/RegisCA/portodash/compare/v1.0-mvp...v1.1.0
[1.0.0]: https://github.com/RegisCA/portodash/releases/tag/v1.0-mvp
