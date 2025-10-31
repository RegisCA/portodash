"""PortoDash theme utilities for modern fintech styling."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional, Union

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

Number = Union[int, float]


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
        width: 20rem !important;
        min-width: 20rem !important;
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
        padding: 0.5rem;
    }}

    .stDataFrame thead th {{
        background: var(--pd-card-bg) !important;
        font-weight: 600;
        color: var(--pd-primary);
        padding: 0.75rem 1rem !important;
    }}

    .stDataFrame tbody tr:nth-child(odd) {{
        background: rgba(17, 24, 39, 0.02) !important;
    }}

    .stDataFrame tbody tr:hover {{
        background: rgba(99, 102, 241, 0.08) !important;
    }}

    [data-testid="stDataFrame"] {{
        padding: 0.5rem;
    }}

    .stDataFrame thead th {{
        padding: 0.75rem 1rem !important;
    }}

    table.data-table {{
        width: 100%;
        border-collapse: separate;
        border-spacing: 0;
        background: var(--pd-background);
        border-radius: 12px;
        overflow: hidden;
    }}

    table.data-table thead th {{
        background: var(--pd-card-bg);
        border-bottom: 1px solid var(--pd-border);
        padding: 0.75rem 1rem;
        font-size: 0.9rem;
        text-align: left;
    }}

    table.data-table tbody td {{
        padding: 0.75rem 1rem;
        border-bottom: 1px solid var(--pd-border);
        font-size: 0.9rem;
        color: var(--pd-primary);
    }}

    table.data-table tbody tr:last-child td {{
        border-bottom: none;
    }}

    table.data-table tbody tr:hover {{
        background: rgba(99, 102, 241, 0.08);
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

    /* Metric cards */
    .metric-grid {{
        display: grid;
        gap: 1rem;
        grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    }}

    .metric-card {{
        background: var(--pd-card-bg);
        border: 1px solid var(--pd-border);
        border-radius: 12px;
        padding: 1.25rem;
        display: flex;
        flex-direction: column;
        gap: 0.5rem;
        box-shadow: 0 1px 3px rgba(15, 23, 42, 0.04);
    }}

    .metric-label {{
        font-size: 0.875rem;
        font-weight: 600;
        color: var(--pd-neutral);
        text-transform: uppercase;
        letter-spacing: 0.06em;
    }}

    .metric-value {{
        font-size: 2rem;
        font-weight: 600;
        color: var(--pd-primary);
        letter-spacing: -0.01em;
    }}

    .metric-delta {{
        font-size: 0.9rem;
        font-weight: 600;
        display: inline-flex;
        align-items: center;
        gap: 0.25rem;
    }}

    .metric-delta-label {{
        font-size: 0.8rem;
        font-weight: 500;
        color: var(--pd-neutral);
        margin-left: 0.35rem;
        text-transform: none;
    }}

    .metric-delta.positive {{
        color: var(--pd-success);
    }}

    .metric-delta.negative {{
        color: var(--pd-error);
    }}

    .metric-delta.neutral {{
        color: var(--pd-neutral);
    }}

    .metric-help {{
        font-size: 0.8rem;
        color: var(--pd-neutral);
    }}

    /* Plotly containers */
    .js-plotly-plot {{
        border-radius: 12px;
        border: 1px solid var(--pd-border);
        background: var(--pd-background);
    }}

    /* Sidebar expanders for filter groups */
    [data-testid="stSidebar"] .streamlit-expanderHeader {{
        background: transparent;
        border: 1px solid var(--pd-border);
        border-radius: 8px;
        padding: 0.75rem 1rem;
        font-weight: 600;
        color: var(--pd-primary);
        transition: background 0.2s ease;
    }}

    [data-testid="stSidebar"] .streamlit-expanderHeader:hover {{
        background: rgba(99, 102, 241, 0.06);
        border-color: var(--pd-secondary);
    }}

    [data-testid="stSidebar"] .streamlit-expanderHeader[aria-expanded="true"] {{
        border-bottom-left-radius: 0;
        border-bottom-right-radius: 0;
    }}

    [data-testid="stSidebar"] .streamlit-expanderContent {{
        border: 1px solid var(--pd-border);
        border-top: none;
        border-bottom-left-radius: 8px;
        border-bottom-right-radius: 8px;
        padding: 0.75rem;
        background: var(--pd-background);
    }}

    /* Filter count badges */
    .filter-badge {{
        display: inline-block;
        background: rgba(99, 102, 241, 0.12);
        color: var(--pd-secondary);
        padding: 0.15rem 0.5rem;
        border-radius: 12px;
        font-size: 0.85rem;
        font-weight: 600;
        margin-left: 0.5rem;
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

    .data-table {
        font-size: 0.875rem;
        color: var(--pd-primary);
    }

    .sidebar-title, .sidebar-subtitle {
        font-family: 'Inter', 'SF Pro Display', 'Segoe UI', system-ui, -apple-system, sans-serif;
    }
    </style>
    """


def _accessibility_css() -> str:
    """Return CSS for WCAG 2.1 Level AA accessibility compliance."""

    return """
    <style>
    /* Keyboard Focus Styles - WCAG 2.1 Success Criterion 2.4.7 */
    *:focus-visible {
        outline: 3px solid var(--pd-secondary);
        outline-offset: 2px;
        border-radius: 4px;
    }

    /* Enhanced focus for interactive elements */
    .stButton > button:focus-visible,
    .stSelectbox select:focus-visible,
    .stMultiSelect:focus-visible,
    .stNumberInput input:focus-visible,
    .stSlider:focus-visible,
    a:focus-visible {
        outline: 3px solid var(--pd-secondary);
        outline-offset: 2px;
        box-shadow: 0 0 0 4px rgba(99, 102, 241, 0.1);
    }

    /* Skip to main content link - for screen readers */
    .skip-to-main {
        position: absolute;
        left: -9999px;
        z-index: 999;
        padding: 1rem 1.5rem;
        background: var(--pd-secondary);
        color: white;
        text-decoration: none;
        border-radius: 0 0 8px 0;
        font-weight: 600;
    }

    .skip-to-main:focus {
        left: 0;
        top: 0;
    }

    /* Ensure sufficient color contrast for links */
    a {
        color: #4F46E5; /* Darker indigo for better contrast (5.74:1) */
        text-decoration: underline;
        text-underline-offset: 2px;
    }

    a:hover {
        color: #4338CA; /* Even darker on hover */
        text-decoration-thickness: 2px;
    }

    /* High contrast mode support */
    @media (prefers-contrast: high) {
        :root {
            --pd-primary: #000000;
            --pd-neutral: #4B5563;
            --pd-border: #9CA3AF;
        }

        .stButton > button,
        .metric-card,
        [data-testid="stDataFrame"] {
            border-width: 2px;
        }
    }

    /* Reduced motion support */
    @media (prefers-reduced-motion: reduce) {
        *,
        *::before,
        *::after {
            animation-duration: 0.01ms !important;
            animation-iteration-count: 1 !important;
            transition-duration: 0.01ms !important;
        }

        .stButton > button {
            transition: none;
            transform: none !important;
        }
    }

    /* Print Stylesheet - WCAG Success Criterion 1.4.13 */
    @media print {
        /* Hide interactive elements */
        [data-testid="stSidebar"],
        .stButton,
        .stButton > button,
        button,
        .stSelectbox,
        .stMultiSelect,
        .stSlider,
        .stNumberInput,
        .stTextInput,
        .stDateInput,
        .stTimeInput,
        .stCheckbox,
        .stRadio,
        header,
        footer,
        [data-testid="stToolbar"],
        [data-testid="stDecoration"],
        [data-testid="stStatusWidget"] {
            display: none !important;
            visibility: hidden !important;
        }

        /* Optimize layout for print */
        .block-container {
            max-width: 100% !important;
            padding: 0 !important;
        }

        /* Ensure proper page breaks */
        .section-header {
            page-break-after: avoid;
            page-break-inside: avoid;
        }

        .metric-card,
        [data-testid="stDataFrame"],
        .stPlotlyChart {
            page-break-inside: avoid;
            margin-bottom: 1rem;
        }

        /* Improve chart readability */
        .stPlotlyChart {
            max-width: 100%;
            height: auto !important;
        }

        /* Print-friendly colors */
        body {
            background: white !important;
            color: black !important;
        }

        .metric-card {
            border: 1px solid #000 !important;
            background: white !important;
        }

        /* Add page header/footer info */
        @page {
            margin: 2cm;
            @top-right {
                content: "PortoDash Portfolio Report";
            }
            @bottom-right {
                content: counter(page);
            }
        }

        /* Ensure tables print properly */
        table {
            border-collapse: collapse;
            width: 100%;
        }

        table thead {
            display: table-header-group;
        }

        table tbody {
            display: table-row-group;
        }
    }

    /* Screen reader only content */
    .sr-only {
        position: absolute;
        width: 1px;
        height: 1px;
        padding: 0;
        margin: -1px;
        overflow: hidden;
        clip: rect(0, 0, 0, 0);
        white-space: nowrap;
        border-width: 0;
    }
    </style>
    """


def inject_modern_fintech_css() -> None:
    """Inject the modern fintech base CSS into Streamlit."""

    st.markdown(_base_css(), unsafe_allow_html=True)


def inject_typography_css() -> None:
    """Inject typography-specific CSS into Streamlit."""

    st.markdown(_typography_css(), unsafe_allow_html=True)


def inject_accessibility_css() -> None:
    """Inject WCAG 2.1 Level AA accessibility CSS into Streamlit."""

    st.markdown(_accessibility_css(), unsafe_allow_html=True)


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


def render_skip_link() -> str:
    """Render a skip-to-main-content link for screen readers."""
    return '<a href="#main-content" class="skip-to-main">Skip to main content</a>'


def format_metric(value: Number) -> str:
    """Format a number as a currency string for portfolio metrics."""

    return f"${value:,.0f}"


def format_percentage(value: Number, precision: int = 1, include_sign: bool = True) -> str:
    """Format a float as a percentage string."""

    fmt = f"{{:+.{precision}f}}%" if include_sign else f"{{:.{precision}f}}%"
    return fmt.format(value)


def render_metric_card(
    label: str,
    value: Union[str, Number],
    *,
    delta: Optional[Number] = None,
    delta_is_percent: bool = True,
    delta_precision: int = 1,
    help_text: Optional[str] = None,
    delta_label: Optional[str] = None,
    value_is_currency: bool = True,
    value_precision: int = 0,
) -> str:
    """Return HTML for a stylized metric card."""

    if isinstance(value, (int, float)):
        if value_is_currency:
            value_str = f"${value:,.{value_precision}f}"
        else:
            value_str = f"{value:,.{value_precision}f}"
    else:
        value_str = str(value)

    delta_html = ""
    if delta is not None:
        delta_value = (
            format_percentage(delta, precision=delta_precision)
            if delta_is_percent
            else format_metric(delta)
        )
        tone = "positive" if delta > 0 else "negative" if delta < 0 else "neutral"
        label_html = f"<span class='metric-delta-label'>{delta_label}</span>" if delta_label else ""
        delta_html = f"<div class='metric-delta {tone}'>{delta_value}{label_html}</div>"

    help_html = f"<div class='metric-help'>{help_text}</div>" if help_text else ""

    return (
        "<div class='metric-card'>"
        f"<div class='metric-label'>{label}</div>"
        f"<div class='metric-value'>{value_str}</div>"
        f"{delta_html}"
        f"{help_html}"
        "</div>"
    )


def render_metric_grid(*cards: str) -> str:
    """Wrap metric cards in a responsive grid container."""

    return f"<div class='metric-grid'>{''.join(cards)}</div>"
