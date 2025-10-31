# PortoDash

![Python](https://img.shields.io/badge/python-3.11+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Streamlit](https://img.shields.io/badge/streamlit-1.30+-red.svg)
![WCAG 2.1 Level AA](https://img.shields.io/badge/accessibility-WCAG%202.1%20Level%20AA-brightgreen.svg)

A lightweight Streamlit portfolio tracker that makes multi-currency portfolios legible by separating market returns from FX effects while keeping a trustworthy CAD home‑currency total and native‑currency context per holding.
Built for Canadian and cross‑border investors who want decision‑ready insights, clear data provenance, and a responsive UI optimized for widescreen displays.

**v1.2 Update:** Redesigned information hierarchy puts key insights front and center — see your portfolio health (FX exposure, top holdings, average gains) immediately without scrolling. Context-aware headers and dynamic tables adapt to your view, whether analyzing your full portfolio or diving into specific accounts.

## Table of contents

- [Overview](#overview)
- [User features](#user-features)
- [Technical features](#technical-features)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Demo mode](#demo-mode)
- [Data freshness](#data-freshness)
- [Scheduler](#scheduler)
- [macOS startup](#macos-startup)
- [Roadmap](#roadmap)
- [Contributing](#contributing)
- [Credits](#credits)

***

## Overview

PortoDash shows native‑currency values alongside CAD totals so you instantly see what moved because of markets versus what moved because of FX.
A clear Live/Cache/Mixed indicator with precise timestamps builds trust in every number on screen, while an insights‑first layout ensures critical portfolio metrics are visible immediately without scrolling — perfect for quick portfolio health checks on widescreen displays.

### Demo

[Screencast Demo](https://github.com/user-attachments/assets/9642aa6a-9977-4935-bed6-60177fab051a)

***

## User features

- **Insights‑First Layout:** Portfolio Insights cards (Positions, Top Holding, FX Exposure, Average Gain) visible immediately on first page — no scrolling needed to assess portfolio health.
- **Clear CAD home‑currency total** with native‑currency context preserved on each holding to avoid conversion ambiguity.
- **Multi‑account browsing** with collapsible filters by account, holder, and account type for focused analysis slices.
- **Context‑aware headers** that adapt to your view: "Portfolio Overview" when viewing all accounts, "Overview" when filtered to specific accounts.
- **Allocation pie chart** for a high‑signal snapshot of portfolio composition with fund/ETF names displayed.
- **30‑day performance view** with two series that isolate FX impact: Market Performance (Fixed FX) vs Actual Performance (with FX).
- **Dynamic table heights** that adapt to content — compact when filtering to a few holdings, larger with scrolling when viewing full portfolio.
- **Transparent data‑provenance** indicator (Live, Cache, Mixed) and Last Updated timestamp for immediate data quality awareness.
- **WCAG 2.1 Level AA Accessibility:** Keyboard navigation, screen reader support, validated color contrast, ARIA labels, print‑friendly layouts.
- **Demo Mode** with realistic sample data for safe exploration and screenshot‑friendly runs without exposing personal holdings.

What's new in v1.2

- **Responsive Widescreen Layout** (PR #54): Complete redesign of information hierarchy — Portfolio Insights moved above charts, key metrics visible on first page, logical flow from overview to insights to visual charts to detailed tables. Dynamic table heights (200-600px) adapt to filtered content.
- **Context-Aware UI** (PR #54): Headers change based on filter state ("Portfolio Overview" vs "Overview"), tables resize based on content, optimized vertical spacing ensures insights are visible without scrolling.
- **Better UX** (PR #54): First page now shows complete portfolio health, reduced from 3 screenshots to 2 to capture full interface, dramatically reduced vertical scrolling on widescreen displays.

***

## Technical features

- Resilient price retrieval with session‑state caching, local‑history fallback, and guarded refresh flows to keep the app responsive.
- Practical rate limiting: 60‑second cooldown between refreshes and automatic 1‑hour backoff after a rate‑limit response to avoid thrashing.
- Local snapshot pipeline that appends to `historical.csv` via a standalone scheduler, decoupling data collection from the UI.
- Operational visibility through per‑run logs and `logs/scheduler_status.json`, which the UI reads to surface scheduler health with contextual copy.
- Optional `psutil` integration to detect the scheduler process directly from the dashboard.
- Theme utilities (`inject_modern_fintech_css`, typography hierarchy, metric card/grid helpers) deliver consistent layout and spacing without inline hacks.
- macOS LaunchAgent example for running the scheduler at login in a stable, user‑space manner.

***

## Installation

### Option A — venv (all platforms)

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
streamlit run app.py
```

### Option B — Conda (convenient on Apple Silicon)

```bash
conda env create -f environment.yml
conda activate portodash
streamlit run app.py

# optional helper
./scripts/create_conda_env.sh
```

***

## Configuration

Copy the sample and edit your private, git‑ignored `portfolio.json`.

```bash
cp portfolio.json.sample portfolio.json
```

Example schema

```bash
{
  "accounts": [
    {
      "nickname": "Main Tax-Free",
      "holder": "Your Name",
      "type": "TFSA",
      "base_currency": "CAD",
      "holdings": [
        {
          "ticker": "XEQT.TO",
          "shares": 100.5,
          "cost_basis": 25.75,
          "currency": "CAD"
        }
      ]
    }
  ]
}
```

Notes

- Use Yahoo Finance tickers (e.g., `XEQT.TO` for TSX and `SPY` for NYSE).
- Supported account types include TFSA, RRSP, Roth IRA, and non‑registered.
- CAD is the portfolio’s home currency for totals; each holding keeps its native currency for accuracy.
- `portfolio.json` and `historical.csv` are git‑ignored for privacy and reliable local caching.

***

## Usage

- Run `streamlit run app.py` and use the sidebar to filter by account, holder, and account type.
- Click Refresh to fetch prices; the Last Updated time and Source label will update to Live, Cache, or Mixed accordingly.
- Snapshots append to `historical.csv`, powering charts and enabling automatic fallback when live prices are unavailable.

***

## Demo mode

Try the app instantly with realistic sample data while your real files are safely backed up.

```bash
python scripts/demo_mode.py --status
python scripts/demo_mode.py   # toggle demo on/off
streamlit run app.py
```

How it works

- Swaps `portfolio.json` and `historical.csv` with sample versions, creates a `.demo_mode` marker, and restores your originals when toggled back.

Updating demo data

If you modify `portfolio.json.sample` (e.g., change share quantities), regenerate `historical.csv.sample`:

```bash
python scripts/update_demo_shares.py
```

This updates all historical snapshots with new share quantities and recalculates portfolio values without re-downloading price data.

***

## Data freshness

The header shows both Last Updated and a provenance label, so you always know what’s live and what came from cache.

- Live: all prices were fetched from yfinance during the last refresh.
- Cache: data came from the latest local snapshot within the configured TTL.
- Mixed: some tickers refreshed, others fell back to cache due to transient issues.
If the price source is unavailable, the app displays data from `historical.csv` to maintain continuity. The holdings summary now includes an FX exposure card, highlighting how much of the portfolio rides on non-CAD currencies at a glance.

***

## Scheduler

Capture a daily snapshot without opening the UI.

```bash
# Activate your environment first
python scripts/run_scheduler.py
```

Defaults

- Timezone: `America/Toronto`.
- Schedule: weekdays at 16:30 local time.
- Logging: `logs/scheduler_YYYYMMDD.log`; status in `logs/scheduler_status.json` (`last_run`, `next_run`, `job_running`, `last_error`).

Tip

- Install `psutil` to let the dashboard detect the scheduler process for better operator visibility.

***

## macOS startup

Run the scheduler at login with a minimal LaunchAgent plist (adjust paths and interpreter).

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
    <string>/Users/yourname/Projects/portodash/logs/scheduler_stdout.log</string>
    <key>StandardErrorPath</key>
    <string>/Users/yourname/Projects/portodash/logs/scheduler_stderr.log</string>
  </dict>
</plist>
```

Load and unload

```bash
launchctl load ~/Library/LaunchAgents/com.yourname.portodash.scheduler.plist
launchctl unload ~/Library/LaunchAgents/com.yourname.portodash.scheduler.plist
```

***

## Design

PortoDash features a clean, modern interface inspired by Wealthsimple's design aesthetic:

- **High contrast** black-on-white with mint green (#00D46A) accents for CTAs
- **Clear hierarchy** with generous spacing and section dividers
- **Enhanced charts** with purposeful color schemes that aid interpretation
- **Responsive layout** optimized for desktop and tablet viewing
- **Trust indicators** with prominent data source badges and timestamps

See [UX_DESIGN.md](UX_DESIGN.md) for complete design system documentation.

## Roadmap

- Hardened scheduler with APScheduler, retries, and configurable calendars.
- Expanded date ranges beyond 30 days (YTD, 1Y, 3Y) and additional charts.
- Contribution analysis to separate flows, market, and FX effects across time.
- Import/export tooling to support broker CSVs and speed up onboarding.
- Dark mode support with theme detection.

***

## Contributing

Contributions are welcome—especially around UX polish, caching strategies, data modeling, and richer multi‑currency analytics that maintain the project’s clarity‑first philosophy.
Open an issue for discussion or submit a PR with notes on UX and edge‑case considerations to keep review focused.

***

## Credits

Built with Streamlit, yfinance, pandas, and Plotly for a fast, modern Python stack tailored to interactive finance dashboards.
Most of the code for this app is developed with GitHub Copilot (Claude Sonnet 4.5). Commits to this repository are made through a bot account (@regisca-bot) to properly track automated changes.
