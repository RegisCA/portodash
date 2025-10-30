"""PortoDash theme utilities for modern fintech styling."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

import streamlit as st


@dataclass(frozen=True)
class ThemeTokens:
    """Design tokens for the PortoDash theme."""

    primary: str = "#1A1A1A"  # Near black
    secondary: str = "#6366F1"  # Indigo action
    success: str = "#10B981"  # Emerald gains
    warning: str = "#F59E0B"  # Amber alerts
    error: str = "#EF4444"
    neutral: str = "#6B7280"
    background: str = "#FFFFFF"
    card_bg: str = "#F9FAFB"


TOKENS = ThemeTokens()


def _base_css() -> str:
    """Return the core CSS for the modern fintech palette."""

    return f"""
    <style>
    :root {{
        --pd-primary: {TOKENS.primary};
        --pd-secondary: {TOKENS.secondary};
        --pd-success: {TOKENS.success};
        --pd-warning: {TOKENS.warning};
        --pd-error: {TOKENS.error};
        --pd-neutral: {TOKENS.neutral};
        --pd-background: {TOKENS.background};
        --pd-card-bg: {TOKENS.card_bg};
        --pd-border: #E5E7EB;
    }}

    html, body, [class*="css"] {{
        font-family: 'Inter', 'SF Pro Display', 'Segoe UI', system-ui, -apple-system, sans-serif;
        background-color: var(--pd-background);
        color: var(--pd-primary);
    }}

    /* Layout */
    .block-container {{
        padding-top: 2rem !important;
        padding-bottom: 2rem !important;
        max-width: 1200px;
    }}

    .stApp header {{
        background: var(--pd-background);
    }}

    /* Buttons */
    .stButton > button {{
        border-radius: 8px;
        font-weight: 600;
        padding: 0.5rem 1.5rem;
        border: 1px solid var(--pd-border);
        background: var(--pd-background);
        color: var(--pd-primary);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }}

    .stButton > button:hover {{
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(17, 24, 39, 0.08);
    }}

    .stButton > button[kind="primary"] {{
        background: var(--pd-secondary);
        color: #FFFFFF;
        border: 1px solid var(--pd-secondary);
    }}

    .stButton > button[kind="primary"]:hover {{
        box-shadow: 0 6px 16px rgba(99, 102, 241, 0.25);
    }}

    /* Sidebar */
    [data-testid="stSidebar"] > div:first-child {{
        background: var(--pd-card-bg);
        border-right: 1px solid var(--pd-border);
        padding: 1.5rem 1rem 1rem;
    }}

    .sidebar-title {{
        font-size: 1rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: var(--pd-neutral);
        margin-bottom: 0.75rem;
    }}

    .sidebar-subtitle {{
        font-size: 0.95rem;
        font-weight: 600;
        margin: 1rem 0 0.5rem;
        color: var(--pd-primary);
    }}

    .sidebar-divider {{
        border: none;
        height: 1px;
        margin: 1rem 0;
        background: rgba(17, 24, 39, 0.05);
    }}

    /* Tables */
    [data-testid="stDataFrame"] {{
        border-radius: 12px;
        border: 1px solid var(--pd-border);
        background: var(--pd-background);
    }}

    .stDataFrame thead th {{
        background: var(--pd-card-bg) !important;
        font-weight: 600;
        color: var(--pd-primary);
    }}

    .stDataFrame tbody tr:nth-child(odd) {{
        background: rgba(17, 24, 39, 0.02) !important;
    }}

    .stDataFrame tbody tr:hover {{
        background: rgba(99, 102, 241, 0.08) !important;
    }}

    .gain-positive {{
        background: rgba(16, 185, 129, 0.12);
        color: var(--pd-success);
    }}

    .gain-negative {{
        background: rgba(239, 68, 68, 0.12);
        color: var(--pd-error);
    }}

    /* Status badges */
    .status-badge {{
        display: inline-flex;
        align-items: center;
        padding: 0.25rem 0.75rem;
        border-radius: 999px;
        font-size: 0.85rem;
        font-weight: 600;
        letter-spacing: 0.02em;
    }}

    .status-live {{
        background: rgba(16, 185, 129, 0.15);
        color: var(--pd-success);
    }}

    .status-cache {{
        background: rgba(245, 158, 11, 0.18);
        color: var(--pd-warning);
    }}

    .status-mixed {{
        background: rgba(107, 114, 128, 0.15);
        color: var(--pd-neutral);
    }}

    /* Plotly containers */
    .js-plotly-plot {{
        border-radius: 12px;
        border: 1px solid var(--pd-border);
        background: var(--pd-background);
    }}
    </style>
    """


def _typography_css() -> str:
    """Return the CSS for typography hierarchy."""

    return """
    <style>
    .app-title {
        font-size: 2.25rem;
        font-weight: 700;
        letter-spacing: -0.02em;
        margin-bottom: 0.25rem;
        color: var(--pd-primary);
    }

    .section-header {
        font-size: 1.75rem;
        font-weight: 600;
        margin: 1.75rem 0 1rem;
        letter-spacing: -0.01em;
        color: var(--pd-primary);
    }

    .subsection-header {
        font-size: 1.25rem;
        font-weight: 600;
        margin: 1.25rem 0 0.75rem;
        color: var(--pd-primary);
    }

    .portfolio-value {
        font-size: 2.5rem;
        font-weight: 700;
        color: var(--pd-primary);
    }

    .metric-label {
        font-size: 0.875rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: var(--pd-neutral);
        margin-bottom: 0.25rem;
    }

    .data-table {
        font-size: 0.875rem;
        color: var(--pd-primary);
    }

    .sidebar-title, .sidebar-subtitle {
        font-family: 'Inter', 'SF Pro Display', 'Segoe UI', system-ui, -apple-system, sans-serif;
    }
    </style>
    """


def inject_modern_fintech_css() -> None:
    """Inject the modern fintech base CSS into Streamlit."""

    st.markdown(_base_css(), unsafe_allow_html=True)


def inject_typography_css() -> None:
    """Inject typography-specific CSS into Streamlit."""

    st.markdown(_typography_css(), unsafe_allow_html=True)


_SECTION_LABELS: Dict[str, str] = {
    "analytics": "Analytics Overview",
    "date": "Date Range",
    "filter": "Filter Controls",
    "account": "Account",
    "holder": "Holder",
    "type": "Type",
    "refresh": "Data Refresh",
}


def get_section_label(icon_type: str) -> str:
    """Return the professional label corresponding to the given section key."""

    return _SECTION_LABELS.get(icon_type, icon_type.title())


def render_page_title(text: str) -> str:
    return f"<h1 class='app-title'>{text}</h1>"


def render_section_header(text: str) -> str:
    return f"<h2 class='section-header'>{text}</h2>"


def render_subsection_header(text: str) -> str:
    return f"<h3 class='subsection-header'>{text}</h3>"


def render_sidebar_title(text: str) -> str:
    return f"<div class='sidebar-title'>{text}</div>"


def render_sidebar_subtitle(text: str) -> str:
    return f"<div class='sidebar-subtitle'>{text}</div>"


def format_metric(value: float) -> str:
    """Format a number as a currency string for portfolio metrics."""

    return f"${value:,.0f}"