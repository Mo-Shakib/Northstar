"""Visual system and reusable presentation components for the dashboard."""

from __future__ import annotations

from datetime import date
from html import escape

import pandas as pd
import streamlit as st

from .config import APP_NAME, COLORS, PRODUCT_COLORS

# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------


def compact_currency(value: float | int | None, decimals: int = 1) -> str:
    value = float(value or 0)
    sign = "-" if value < 0 else ""
    value = abs(value)
    if value >= 1_000_000_000:
        return f"{sign}${value / 1_000_000_000:,.{decimals}f}B"
    if value >= 1_000_000:
        return f"{sign}${value / 1_000_000:,.{decimals}f}M"
    if value >= 1_000:
        return f"{sign}${value / 1_000:,.{decimals}f}K"
    return f"{sign}${value:,.0f}"


def compact_number(value: float | int | None) -> str:
    value = float(value or 0)
    if value >= 1_000_000:
        return f"{value / 1_000_000:,.1f}M"
    if value >= 1_000:
        return f"{value / 1_000:,.1f}K"
    return f"{value:,.0f}"


def _pct(value: float | int | None, decimals: int = 1) -> str:
    return f"{float(value or 0):.{decimals}f}%"


def format_date(value: date | str | None) -> str:
    if value is None:
        return "—"
    if isinstance(value, str):
        value = date.fromisoformat(value[:10])
    return value.strftime("%d %b %Y")


# ---------------------------------------------------------------------------
# Application shell
# ---------------------------------------------------------------------------


def inject_css() -> None:
    st.markdown(
        """
        <style>
        :root {
            --ink: #171B18;
            --ink-soft: #333934;
            --muted: #6C726D;
            --subtle: #91968F;
            --primary: #225C4B;
            --primary-hover: #194939;
            --primary-soft: #EAF1ED;
            --accent: #B08A5A;
            --danger: #A9443C;
            --amber: #A46B2A;
            --border: #E4E1D9;
            --border-strong: #D5D1C7;
            --surface: #FFFFFF;
            --surface-soft: #FAF9F5;
            --canvas: #F3F1EB;
            --font-sans: -apple-system, BlinkMacSystemFont, "Segoe UI", "Helvetica Neue", Arial, sans-serif;
            --font-serif: "Iowan Old Style", "Palatino Linotype", Palatino, Georgia, serif;
            --font-mono: "SFMono-Regular", "SF Mono", Menlo, Consolas, monospace;
        }

        html, body, [class*="css"] {
            font-family: var(--font-sans);
        }
        html, body {
            background: var(--canvas);
        }
        [data-testid="stAppViewContainer"] {
            background: var(--canvas);
        }
        [data-testid="stMain"] .block-container {
            max-width: 1380px;
            padding: 2.2rem 2.6rem 2.6rem;
        }
        [data-testid="stHeader"] {
            background: transparent;
            height: 0;
            overflow: visible;
        }
        [data-testid="stToolbar"] {
            display: flex !important;
            visibility: visible !important;
            position: fixed;
            top: 0;
            left: 0;
            z-index: 100001;
            width: auto;
            height: auto !important;
            padding: 0;
            background: transparent;
            pointer-events: none;
        }
        [data-testid="stToolbarActions"],
        [data-testid="stBaseButton-header"],
        [data-testid="stMainMenu"],
        [data-testid="stDecoration"],
        #MainMenu,
        footer {
            visibility: hidden;
            display: none;
        }
        [data-testid="stExpandSidebarButton"] {
            display: flex !important;
            position: fixed !important;
            top: 14px !important;
            left: 14px !important;
            z-index: 100002 !important;
            align-items: center;
            justify-content: center;
            visibility: visible !important;
            width: 34px !important;
            height: 34px !important;
            padding: 0 !important;
            border: 1px solid var(--border-strong) !important;
            border-radius: 7px !important;
            background: #FFFFFF !important;
            color: var(--ink-soft) !important;
            box-shadow: 0 1px 2px rgba(23, 27, 24, 0.04);
            pointer-events: auto;
        }
        [data-testid="stExpandSidebarButton"]:hover {
            border-color: #AABCB2 !important;
            color: var(--primary) !important;
        }
        [data-testid="stExpandSidebarButton"] span {
            font-size: 17px !important;
        }
        [data-testid="stMarkdownContainer"] p {
            line-height: 1.55;
        }

        /* Sidebar */
        [data-testid="stSidebar"] {
            background: #F8F6F1;
            border-right: 1px solid var(--border);
        }
        [data-testid="stSidebar"] > div:first-child {
            padding: 1.55rem 1.15rem 1.5rem;
        }
        [data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
            gap: 0.7rem;
        }
        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
            color: var(--muted);
        }
        [data-testid="stSidebar"] [data-testid="stWidgetLabel"] p {
            color: #505650 !important;
            font-size: 0.72rem !important;
            font-weight: 600 !important;
            letter-spacing: 0.005em;
        }
        [data-testid="stSidebar"] [data-testid="stTooltipIcon"] {
            display: none;
        }
        [data-testid="stSidebar"] [data-testid="stDateInputField"],
        [data-testid="stSidebar"] [data-testid="stMultiSelect"] [role="group"] {
            background: #FFFFFF !important;
            border: 1px solid #DDD9CF !important;
            border-radius: 7px !important;
            min-height: 38px;
            box-shadow: none !important;
        }
        [data-testid="stSidebar"] [data-testid="stDateInputField"]:focus-within,
        [data-testid="stSidebar"] [data-testid="stMultiSelect"] [role="group"]:focus-within {
            border-color: #93B4A7 !important;
            box-shadow: 0 0 0 2px rgba(34, 92, 75, 0.08) !important;
        }
        [data-testid="stSidebar"] [data-testid="stDateInputField"] span,
        [data-testid="stSidebar"] [data-testid="stMultiSelect"] input {
            color: var(--ink) !important;
            font-size: 0.76rem !important;
        }
        [data-testid="stSidebar"] [data-testid="stDateInputField"] [data-type="literal"],
        [data-testid="stSidebar"] [data-testid="stDateInputField"] > div > span {
            color: #989D96 !important;
        }
        [data-testid="stSidebar"] [data-testid="stMultiSelect"] input::placeholder {
            color: #979C95 !important;
            opacity: 1 !important;
        }
        [data-testid="stSidebar"] [data-testid="stMultiSelect"] svg,
        [data-testid="stSidebar"] [data-testid="stDateInput"] svg {
            color: #8B918A !important;
        }
        [data-testid="stSidebar"] [data-testid="stMultiSelect"] [data-tag] {
            background: #EDF2EF !important;
            border: 1px solid #DCE6E0 !important;
            color: #295845 !important;
            border-radius: 4px !important;
            font-size: 0.69rem !important;
            font-weight: 550 !important;
        }
        [data-testid="stSidebar"] [data-testid="stMultiSelect"] [data-tag] span {
            color: #295845 !important;
        }
        [data-testid="stSidebar"] .stButton button {
            width: auto;
            min-height: 0;
            padding: 0;
            border: 0;
            background: transparent;
            color: #747A74;
            font-size: 0.7rem;
            font-weight: 550;
            line-height: 1.4;
            justify-content: flex-start;
        }
        [data-testid="stSidebar"] .stButton button:hover {
            color: var(--primary);
            background: transparent;
            border: 0;
        }
        [class*="st-key-sidebar_reset"] {
            display: flex;
            justify-content: flex-end;
        }
        [class*="st-key-sidebar_reset"] button {
            margin-left: auto;
        }

        .brand {
            display: flex;
            align-items: center;
            gap: 0.62rem;
            padding: 0.05rem 0.1rem 0.6rem;
        }
        .brand-mark {
            width: 26px;
            height: 26px;
            display: flex;
            align-items: center;
            justify-content: center;
            border: 1px solid #CFDBD5;
            border-radius: 7px;
            background: #F2F7F4;
        }
        .brand-name {
            color: var(--ink);
            font-size: 0.98rem;
            font-weight: 700;
            letter-spacing: -0.035em;
            line-height: 1.1;
        }
        .brand-sub {
            color: #858B84;
            font-size: 0.62rem;
            letter-spacing: 0.02em;
            margin-top: 0.17rem;
        }
        .side-rule {
            height: 1px;
            background: #E7E3DA;
            margin: 0.55rem 0 0.4rem;
        }
        .side-heading {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0.35rem 0.05rem 0.1rem;
        }
        .side-heading span:first-child {
            color: #777D77;
            font-size: 0.62rem;
            font-weight: 700;
            letter-spacing: 0.11em;
            text-transform: uppercase;
        }
        .side-heading span:last-child {
            color: #989D96;
            font-size: 0.62rem;
        }
        .side-meta {
            border-top: 1px solid #E7E3DA;
            margin-top: 0.7rem;
            padding: 0.95rem 0.08rem 0.1rem;
        }
        .side-meta-title {
            color: #777D77;
            font-size: 0.61rem;
            font-weight: 700;
            letter-spacing: 0.11em;
            text-transform: uppercase;
            margin-bottom: 0.5rem;
        }
        .side-meta-date {
            color: var(--ink-soft);
            font-size: 0.71rem;
            font-weight: 600;
            line-height: 1.5;
        }
        .side-meta-grid {
            display: flex;
            gap: 0.8rem;
            margin-top: 0.55rem;
            color: #6C726C;
            font-size: 0.68rem;
        }
        .side-meta-grid strong {
            color: var(--ink);
            font-weight: 650;
            font-variant-numeric: tabular-nums;
        }
        .side-meta-foot {
            display: flex;
            align-items: center;
            gap: 0.42rem;
            color: #8A8F89;
            font-size: 0.63rem;
            line-height: 1.5;
            margin-top: 0.75rem;
        }
        .db-dot {
            width: 5px;
            height: 5px;
            border-radius: 50%;
            background: #4E8B70;
            display: inline-block;
            flex: none;
        }

        /* Page header */
        .page-kicker {
            color: #7D837D;
            font-size: 0.61rem;
            letter-spacing: 0.13em;
            font-weight: 700;
            text-transform: uppercase;
            margin-bottom: 0.55rem;
        }
        .page-title {
            font-family: var(--font-serif) !important;
            color: var(--ink) !important;
            font-size: clamp(1.75rem, 2.4vw, 2.28rem) !important;
            font-weight: 500 !important;
            line-height: 1.1 !important;
            letter-spacing: -0.035em !important;
            margin: 0 !important;
            padding: 0 !important;
        }
        .page-subtitle {
            color: #6A706B;
            font-size: 0.79rem;
            line-height: 1.55;
            margin: 0.55rem 0 0;
            max-width: 560px;
        }
        .page-meta {
            display: flex;
            align-items: center;
            flex-wrap: wrap;
            gap: 0.52rem;
            margin-top: 0.8rem;
            color: #878D87;
            font-size: 0.68rem;
        }
        .page-meta .live-dot {
            width: 5px;
            height: 5px;
            border-radius: 50%;
            background: #4E8B70;
            display: inline-block;
            margin-right: 0.12rem;
        }
        .page-meta strong {
            color: #5C625C;
            font-weight: 600;
        }
        .page-meta .sep {
            color: #C2C5BF;
        }
        .filter-chip {
            display: inline-flex;
            align-items: center;
            height: 20px;
            padding: 0 0.48rem;
            border-radius: 4px;
            background: var(--primary-soft);
            color: #38614F;
            font-size: 0.61rem;
            font-weight: 600;
        }
        [class*="st-key-header_action_box"] {
            display: flex;
            justify-content: flex-end;
            align-items: flex-end !important;
        }
        [class*="st-key-header_action_box"] [data-testid="stElementContainer"] {
            margin-left: auto !important;
            width: fit-content;
        }
        [class*="st-key-header_action_box"] [data-testid="stDownloadButton"] button {
            min-height: 35px;
            border: 1px solid var(--border-strong);
            border-radius: 7px;
            background: #FFFFFF;
            color: var(--ink-soft);
            font-size: 0.71rem;
            font-weight: 600;
            box-shadow: none;
        }
        [class*="st-key-header_action_box"] [data-testid="stDownloadButton"] button:hover {
            border-color: #AABDB3;
            color: var(--primary);
            background: #FCFDFC;
        }

        /* Tabs */
        [data-testid="stTabs"] {
            margin-top: 1.5rem;
        }
        [data-testid="stTabs"] [role="tablist"] {
            gap: 1.55rem;
            width: 100%;
            padding: 0;
            border: none;
            border-bottom: 1px solid var(--border);
            border-radius: 0;
            background: transparent;
            box-shadow: none;
            margin-bottom: 1.2rem;
        }
        [data-testid="stTab"] {
            min-height: 0;
            padding: 0 0 0.72rem;
            border-radius: 0;
            background: transparent !important;
            color: #7C827C !important;
            cursor: pointer;
        }
        [data-testid="stTab"] [data-testid="stMarkdownContainer"] p {
            color: inherit !important;
            font-size: 0.72rem;
            font-weight: 600;
            letter-spacing: 0.005em;
            margin: 0;
        }
        [data-testid="stTab"]:hover {
            background: transparent !important;
            color: var(--ink) !important;
        }
        [data-testid="stTab"][aria-selected="true"] {
            color: var(--ink) !important;
            box-shadow: inset 0 -1.5px 0 var(--ink);
        }
        [data-testid="stTab"][aria-selected="true"] [data-testid="stMarkdownContainer"] p {
            color: var(--ink) !important;
        }
        [data-testid="stTab"] .react-aria-SelectionIndicator {
            display: none;
        }

        /* Metric strip */
        .metric-strip {
            display: grid;
            grid-template-columns: repeat(var(--metric-cols, 4), minmax(0, 1fr));
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 10px;
            overflow: hidden;
            margin-bottom: 1rem;
        }
        .metric-cell {
            padding: 1.05rem 1.15rem 1rem;
            min-width: 0;
            border-right: 1px solid var(--border);
        }
        .metric-cell:last-child {
            border-right: 0;
        }
        .metric-label {
            display: flex;
            align-items: center;
            gap: 0.38rem;
            color: #777D77;
            font-size: 0.66rem;
            font-weight: 600;
        }
        .metric-label .dot {
            width: 5px;
            height: 5px;
            border-radius: 50%;
            flex: none;
        }
        .metric-value {
            color: var(--ink);
            font-size: 1.72rem;
            font-weight: 620;
            letter-spacing: -0.045em;
            line-height: 1.05;
            margin-top: 0.45rem;
            font-variant-numeric: tabular-nums;
            white-space: nowrap;
        }
        .metric-detail {
            color: #858B85;
            font-size: 0.64rem;
            line-height: 1.45;
            margin-top: 0.42rem;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        .metric-detail strong {
            color: #5E645E;
            font-weight: 600;
        }

        /* Panels and cards */
        [class*="st-key-card_"] {
            border: 1px solid var(--border) !important;
            border-radius: 10px !important;
            background: var(--surface) !important;
            box-shadow: none !important;
            padding: 1rem 1.15rem 0.6rem !important;
            min-height: 385px;
        }
        [class*="st-key-ops_"] {
            border: 1px solid var(--border) !important;
            border-radius: 10px !important;
            background: var(--surface) !important;
            box-shadow: none !important;
            padding: 1rem 1.15rem 0.9rem !important;
        }
        .panel {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 10px;
            padding: 1rem 1.15rem 1.05rem;
            height: 100%;
            min-height: 385px;
        }
        .panel .grow {
            flex: 1;
        }
        .card-head {
            display: flex;
            align-items: flex-start;
            justify-content: space-between;
            gap: 1rem;
            margin-bottom: 0.7rem;
        }
        .card-title {
            color: var(--ink);
            font-size: 0.8rem;
            font-weight: 650;
            letter-spacing: -0.015em;
            line-height: 1.3;
            margin: 0;
        }
        .card-sub {
            color: #858B85;
            font-size: 0.66rem;
            line-height: 1.4;
            margin-top: 0.2rem;
        }
        .card-aside {
            color: var(--ink-soft);
            font-size: 0.72rem;
            font-weight: 600;
            text-align: right;
            white-space: nowrap;
            font-variant-numeric: tabular-nums;
            line-height: 1.35;
        }
        .card-aside small {
            display: block;
            color: #989D96;
            font-size: 0.55rem;
            font-weight: 650;
            letter-spacing: 0.07em;
            text-transform: uppercase;
            margin-top: 0.16rem;
        }
        .panel-foot {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 0.75rem;
            border-top: 1px solid #EFEDE7;
            margin-top: auto;
            padding-top: 0.65rem;
            color: #888E88;
            font-size: 0.62rem;
            line-height: 1.45;
        }
        .panel-foot strong {
            color: #5D635D;
            font-weight: 600;
        }
        .panel-note {
            color: #7E847E;
            font-size: 0.63rem;
            line-height: 1.5;
            border-top: 1px solid #EFEDE7;
            padding-top: 0.62rem;
            margin-top: 0.7rem;
        }
        .empty-block {
            display: flex;
            align-items: center;
            justify-content: center;
            min-height: 140px;
            color: var(--subtle);
            font-size: 0.72rem;
        }

        /* Allocation */
        .allocation-panel {
            display: flex;
            flex-direction: column;
        }
        .allocation-list {
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            flex: 1;
            margin-top: 0.25rem;
        }
        .alloc-row {
            padding: 0.52rem 0 0.48rem;
            border-bottom: 1px solid #F1EFEA;
        }
        .alloc-row:last-child {
            border-bottom: 0;
        }
        .alloc-line {
            display: flex;
            align-items: baseline;
            justify-content: space-between;
            gap: 0.8rem;
            font-size: 0.68rem;
            line-height: 1.35;
        }
        .alloc-name {
            display: flex;
            align-items: center;
            gap: 0.42rem;
            color: #555B56;
            min-width: 0;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        .alloc-dot {
            width: 5px;
            height: 5px;
            border-radius: 50%;
            display: inline-block;
            flex: none;
        }
        .alloc-value {
            color: var(--ink);
            font-weight: 600;
            font-size: 0.67rem;
            white-space: nowrap;
            font-variant-numeric: tabular-nums;
        }
        .alloc-share {
            color: #91968F;
            font-weight: 450;
            margin-left: 0.22rem;
        }
        .alloc-track {
            height: 3px;
            background: #F1EFEA;
            border-radius: 2px;
            margin-top: 0.43rem;
            overflow: hidden;
        }
        .alloc-track span {
            display: block;
            height: 100%;
            border-radius: 2px;
        }

        /* Risk panel */
        .risk-panel {
            display: flex;
            flex-direction: column;
        }
        .risk-top {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 0.8rem;
            border-bottom: 1px solid #EFEDE7;
            padding-bottom: 0.8rem;
        }
        .risk-stat span {
            display: block;
            color: #838983;
            font-size: 0.62rem;
            line-height: 1.45;
        }
        .risk-stat strong {
            display: block;
            color: var(--ink);
            font-size: 1.25rem;
            font-weight: 620;
            letter-spacing: -0.035em;
            margin-top: 0.22rem;
            font-variant-numeric: tabular-nums;
        }
        .risk-bar-label {
            display: flex;
            justify-content: space-between;
            color: #8A908A;
            font-size: 0.59rem;
            margin: 0.8rem 0 0.38rem;
        }
        .risk-bar {
            display: flex;
            height: 9px;
            border-radius: 3px;
            overflow: hidden;
            background: #F1EFEA;
        }
        .risk-bar span {
            display: block;
            height: 100%;
        }
        .risk-legend {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 0.38rem 0.85rem;
            margin-top: 0.65rem;
        }
        .risk-legend-item {
            display: flex;
            align-items: center;
            gap: 0.38rem;
            color: #7E847E;
            font-size: 0.6rem;
            line-height: 1.45;
            min-width: 0;
        }
        .risk-legend-item i {
            width: 5px;
            height: 5px;
            border-radius: 50%;
            flex: none;
        }
        .risk-legend-item span {
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        .risk-legend-item strong {
            color: #545A55;
            font-weight: 600;
            margin-left: auto;
            font-variant-numeric: tabular-nums;
        }
        .risk-insight {
            color: #6E746E;
            background: #FAF9F5;
            border: 1px solid #EFECE5;
            border-radius: 6px;
            font-size: 0.62rem;
            line-height: 1.5;
            padding: 0.55rem 0.65rem;
            margin-top: 0.65rem;
        }
        .risk-insight strong {
            color: #565C57;
        }

        /* Standard data table */
        .table-panel {
            display: flex;
            flex-direction: column;
        }
        .data-table {
            width: 100%;
            border-collapse: collapse;
            table-layout: fixed;
            margin-top: 0.25rem;
        }
        .data-table th {
            color: #92978F;
            font-size: 0.58rem;
            font-weight: 650;
            letter-spacing: 0.035em;
            line-height: 1.35;
            text-align: left;
            padding: 0 0.38rem 0.45rem;
            border-bottom: 1px solid #EAE7E0;
            white-space: nowrap;
        }
        .data-table th.num,
        .data-table td.num {
            text-align: right;
        }
        .data-table td {
            color: #5D635D;
            font-size: 0.68rem;
            line-height: 1.4;
            padding: 0.58rem 0.38rem;
            border-bottom: 1px solid #F2F0EB;
            vertical-align: middle;
            white-space: nowrap;
            font-variant-numeric: tabular-nums;
        }
        .data-table tr:last-child td {
            border-bottom: 0;
        }
        .row-title {
            display: block;
            color: var(--ink-soft);
            font-weight: 600;
        }
        .row-sub {
            display: block;
            color: #92978F;
            font-size: 0.61rem;
            margin-top: 0.12rem;
        }
        .data-table .risk-text {
            color: var(--danger);
        }
        .data-table .warn-text {
            color: var(--amber);
        }
        .table-footer {
            color: #808680;
            font-size: 0.62rem;
            line-height: 1.5;
            border-top: 1px solid #EFEDE7;
            padding-top: 0.62rem;
            margin-top: auto;
        }
        .table-footer strong {
            color: #585E59;
            font-weight: 600;
        }

        /* Exposure list */
        .exposure-list {
            margin-top: 0.1rem;
        }
        .exposure-row {
            display: grid;
            grid-template-columns: 1.5rem minmax(0, 1fr) auto;
            gap: 0.55rem;
            align-items: center;
            padding: 0.48rem 0;
            border-bottom: 1px solid #F2F0EB;
        }
        .exposure-row:last-child {
            border-bottom: 0;
        }
        .exposure-rank {
            color: #A4A8A2;
            font-family: var(--font-mono);
            font-size: 0.59rem;
            letter-spacing: -0.04em;
        }
        .exposure-person {
            color: var(--ink-soft);
            font-size: 0.68rem;
            font-weight: 600;
            line-height: 1.35;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        .exposure-meta {
            color: #92978F;
            font-size: 0.6rem;
            line-height: 1.4;
            margin-top: 0.1rem;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        .exposure-value {
            color: var(--ink);
            font-size: 0.68rem;
            font-weight: 600;
            text-align: right;
            white-space: nowrap;
            font-variant-numeric: tabular-nums;
        }
        .risk-tag {
            display: block;
            color: #A76A2D;
            font-size: 0.56rem;
            font-weight: 550;
            margin-top: 0.12rem;
        }

        /* Quality */
        .quality-panel {
            min-height: 0;
            margin-bottom: 0.9rem;
        }
        .status-pill {
            display: inline-flex;
            align-items: center;
            gap: 0.3rem;
            color: #39745B;
            background: #EFF6F2;
            border: 1px solid #DDE9E2;
            border-radius: 4px;
            font-size: 0.57rem;
            font-weight: 600;
            line-height: 1;
            padding: 0.24rem 0.38rem;
            white-space: nowrap;
        }
        .status-pill:before {
            content: "";
            width: 4px;
            height: 4px;
            border-radius: 50%;
            background: #4B8A6D;
        }
        .status-pill.review {
            color: #9D632C;
            background: #FBF4E9;
            border-color: #F0E0C9;
        }
        .status-pill.review:before {
            background: #B47736;
        }
        .quality-columns {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 0 2.4rem;
        }
        .quality-col-head {
            display: grid;
            grid-template-columns: minmax(0, 1fr) 62px 32px;
            gap: 0.7rem;
            color: #969A94;
            font-size: 0.55rem;
            font-weight: 650;
            letter-spacing: 0.06em;
            text-transform: uppercase;
            padding: 0.1rem 0.1rem 0.45rem;
            border-bottom: 1px solid #EAE7E0;
        }
        .quality-col-head span:nth-child(2),
        .quality-col-head span:nth-child(3) {
            text-align: right;
        }
        .quality-entry {
            border-bottom: 1px solid #F2F0EB;
        }
        .quality-entry:last-child {
            border-bottom: 0;
        }
        .quality-item {
            display: grid;
            grid-template-columns: minmax(0, 1fr) 62px 32px;
            gap: 0.7rem;
            align-items: center;
            padding: 0.56rem 0.1rem;
        }
        .quality-name {
            color: #4C524D;
            font-size: 0.67rem;
            font-weight: 550;
            line-height: 1.35;
        }
        .quality-scope {
            color: #989D96;
            font-size: 0.57rem;
            line-height: 1.35;
            margin-top: 0.1rem;
        }
        .quality-finding {
            color: #A9443C;
            background: #FCF3F1;
            border-radius: 4px;
            font-size: 0.59rem;
            line-height: 1.45;
            padding: 0.35rem 0.45rem;
            margin: 0 0.1rem 0.45rem;
        }
        .quality-count {
            text-align: right;
            color: #858B85;
            font-size: 0.64rem;
            font-variant-numeric: tabular-nums;
        }
        .quality-summary {
            display: flex;
            align-items: center;
            gap: 0.45rem;
            color: #5F655F;
            font-size: 0.68rem;
            line-height: 1.5;
            margin: 0.1rem 0 0.2rem;
        }
        .quality-summary .check-dot {
            width: 6px;
            height: 6px;
            border-radius: 50%;
            background: #4B8A6D;
        }

        /* Completeness */
        .completeness-panel {
            min-height: 0;
            margin-bottom: 0.7rem;
        }
        .completeness-wide {
            display: grid;
            grid-template-columns: 1.05fr 1fr;
            gap: 2rem;
            padding-top: 0.15rem;
        }
        .coverage-top {
            padding: 0.1rem 0 0;
        }
        .coverage-line {
            display: flex;
            align-items: baseline;
            justify-content: space-between;
            gap: 1rem;
        }
        .coverage-label {
            color: #7D837D;
            font-size: 0.64rem;
        }
        .coverage-value {
            color: var(--ink);
            font-size: 1.23rem;
            font-weight: 620;
            letter-spacing: -0.035em;
            font-variant-numeric: tabular-nums;
        }
        .coverage-track {
            height: 5px;
            border-radius: 3px;
            background: #F0EEE8;
            margin-top: 0.5rem;
            overflow: hidden;
        }
        .coverage-track span {
            display: block;
            height: 100%;
            border-radius: 3px;
            background: #4B8A6D;
        }
        .coverage-caption {
            color: #8B918A;
            font-size: 0.6rem;
            line-height: 1.5;
            margin-top: 0.45rem;
        }
        .optional-list {
            border-left: 1px solid #EFEDE7;
            padding-left: 2rem;
        }
        .optional-title {
            color: #8B918A;
            font-size: 0.55rem;
            font-weight: 650;
            letter-spacing: 0.07em;
            text-transform: uppercase;
            margin-bottom: 0.2rem;
        }
        .coverage-row {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 1rem;
            padding: 0.48rem 0;
            border-bottom: 1px solid #F2F0EB;
            font-size: 0.64rem;
        }
        .coverage-row:last-child {
            border-bottom: 0;
        }
        .coverage-field {
            color: #646A64;
            font-family: var(--font-mono);
            font-size: 0.6rem;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        .coverage-missing {
            color: #8F958F;
            white-space: nowrap;
            font-variant-numeric: tabular-nums;
        }
        .coverage-note {
            color: #8C918B;
            font-size: 0.6rem;
            line-height: 1.5;
            border-top: 1px solid #EFEDE7;
            padding-top: 0.62rem;
            margin-top: 0.8rem;
        }

        /* General controls */
        .stButton button[kind="primary"] {
            background: var(--primary);
            border: 1px solid var(--primary);
            border-radius: 7px;
            color: #FFFFFF;
            font-size: 0.72rem;
            font-weight: 600;
            min-height: 36px;
            box-shadow: none;
        }
        .stButton button[kind="primary"]:hover {
            background: var(--primary-hover);
            border-color: var(--primary-hover);
        }
        .stButton button[kind="secondary"] {
            border-radius: 7px;
            border: 1px solid var(--border-strong);
            color: var(--ink-soft);
            font-size: 0.7rem;
            font-weight: 550;
            min-height: 35px;
            background: #FFFFFF;
        }
        [data-testid="stDownloadButton"] button {
            border-radius: 7px;
            border: 1px solid var(--border);
            color: #535953;
            background: #FFFFFF;
            font-size: 0.68rem;
            font-weight: 550;
            min-height: 34px;
            box-shadow: none;
        }
        [data-testid="stDownloadButton"] button:hover {
            border-color: #AABCB2;
            color: var(--primary);
            background: #FCFDFC;
        }
        [data-testid="stTextInput"] input {
            background: #FFFFFF;
            border: 1px solid #DDD9CF;
            border-radius: 7px;
            color: var(--ink);
            font-size: 0.76rem;
            min-height: 38px;
        }
        [data-testid="stTextInput"] > div > div {
            border-color: #DDD9CF !important;
            border-radius: 7px !important;
        }
        [data-testid="stTextInput"] input::placeholder {
            color: #9A9F98 !important;
        }
        [data-testid="stFileUploader"] label {
            color: #505650 !important;
            font-size: 0.72rem !important;
            font-weight: 600 !important;
        }
        [data-testid="stFileUploader"] {
            background: #FBFAF7;
            border: 1px dashed #D8D4CA;
            border-radius: 8px;
            padding: 0.35rem;
        }
        [data-testid="stFileUploaderDropzone"] {
            background: transparent;
            border: 0;
            border-radius: 7px;
            padding: 0.45rem;
        }
        [data-testid="stFileUploaderDropzone"] button {
            border-radius: 6px;
            border-color: #D3CFC5;
            font-size: 0.68rem;
            min-height: 32px;
        }
        [data-testid="stFileUploaderDropzone"] small {
            color: #979C95;
        }
        [data-testid="stDataFrame"] {
            border: 1px solid var(--border);
            border-radius: 8px;
            overflow: hidden;
            background: #FFFFFF;
        }
        [data-testid="stExpander"] {
            border: 1px solid var(--border);
            border-radius: 8px;
            background: #FFFFFF;
        }
        [data-testid="stExpander"] summary {
            color: #5F655F;
            font-size: 0.7rem;
        }
        .stAlert {
            border-radius: 7px;
            border-width: 1px;
            font-size: 0.72rem;
        }
        .stAlert p {
            font-size: 0.72rem;
            line-height: 1.5;
        }
        div[data-testid="stSpinner"] {
            color: var(--primary);
        }

        /* Data operations */
        .ops-intro {
            color: #6D736D;
            font-size: 0.71rem;
            line-height: 1.6;
            margin: 0 0 0.75rem;
        }
        .ops-intro strong {
            color: #4F5550;
            font-weight: 600;
        }
        .required-fields {
            color: #8B918A;
            font-family: var(--font-mono);
            font-size: 0.58rem;
            line-height: 1.7;
            margin-top: -0.3rem;
            margin-bottom: 0.6rem;
            word-break: break-word;
        }
        .data-note {
            color: #989D96;
            font-size: 0.6rem;
            line-height: 1.5;
            margin-top: 0.5rem;
        }
        .workspace-strip {
            display: grid;
            grid-template-columns: 1.45fr 1fr 1fr 1fr;
            gap: 1rem;
            align-items: center;
            background: #F8F6F1;
            border: 1px solid var(--border);
            border-radius: 9px;
            padding: 0.85rem 1rem;
            margin-top: 1rem;
        }
        .workspace-strip .ws-label {
            color: #888E88;
            font-size: 0.6rem;
            line-height: 1.45;
        }
        .workspace-strip .ws-value {
            color: var(--ink-soft);
            font-size: 0.75rem;
            font-weight: 600;
            font-variant-numeric: tabular-nums;
            margin-top: 0.16rem;
        }
        .workspace-strip .ws-path {
            color: #8B918A;
            font-family: var(--font-mono);
            font-size: 0.56rem;
            line-height: 1.45;
            margin-top: 0.15rem;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        .section-note {
            color: #858B85;
            font-size: 0.66rem;
            line-height: 1.5;
        }
        .app-footer {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 1rem;
            color: #969B95;
            font-size: 0.6rem;
            line-height: 1.5;
            border-top: 1px solid var(--border);
            margin-top: 1.8rem;
            padding-top: 0.9rem;
        }
        .app-footer span:last-child {
            text-align: right;
        }

        @media (max-width: 1200px) {
            .metric-detail {
                white-space: normal;
            }
            .metric-value {
                font-size: 1.55rem;
            }
        }

        @media (max-width: 1100px) {
            [role="tabpanel"] [data-testid="stHorizontalBlock"] {
                flex-wrap: wrap !important;
                row-gap: 0.9rem;
            }
            [role="tabpanel"] [data-testid="stColumn"] {
                flex: 1 1 100% !important;
                width: 100% !important;
                min-width: 100% !important;
            }
        }

        @media (max-width: 900px) {
            [data-testid="stMain"] .block-container {
                padding: 3.6rem 1rem 2rem;
            }
            .page-title {
                font-size: 1.9rem !important;
            }
            .metric-strip {
                grid-template-columns: repeat(2, minmax(0, 1fr));
            }
            .metric-cell {
                border-bottom: 1px solid var(--border);
            }
            .metric-cell:nth-child(2n) {
                border-right: 0;
            }
            .metric-cell:nth-last-child(-n+2) {
                border-bottom: 0;
            }
            [data-testid="stTabs"] [role="tablist"] {
                gap: 1.1rem;
                overflow-x: auto;
            }
            .data-table th:nth-child(6),
            .data-table td:nth-child(6) {
                display: none;
            }
            .workspace-strip {
                grid-template-columns: 1fr 1fr;
            }
            .completeness-wide {
                grid-template-columns: 1fr;
                gap: 0.8rem;
            }
            .optional-list {
                border-left: 0;
                border-top: 1px solid #EFEDE7;
                padding-left: 0;
                padding-top: 0.6rem;
            }
            .app-footer {
                flex-direction: column;
                align-items: flex-start;
            }
            .app-footer span:last-child {
                text-align: left;
            }
        }

        @media (max-width: 620px) {
            [data-testid="stSidebar"] > div:first-child {
                padding: 1.1rem 0.9rem 1.2rem;
            }
            .page-title {
                font-size: 1.65rem !important;
            }
            .page-subtitle {
                font-size: 0.76rem;
            }
            .page-meta {
                font-size: 0.62rem;
            }
            [data-testid="stTabs"] [role="tablist"] {
                gap: 0.9rem;
            }
            [data-testid="stTab"] [data-testid="stMarkdownContainer"] p {
                font-size: 0.67rem;
            }
            .quality-columns {
                grid-template-columns: 1fr;
                gap: 0;
            }
            .quality-columns > div + div {
                margin-top: 0.7rem;
            }
            .metric-cell {
                padding: 0.9rem;
            }
            .metric-value {
                font-size: 1.35rem;
            }
            .workspace-strip {
                grid-template-columns: 1fr;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_brand() -> None:
    st.markdown(
        '<div class="brand">'
        '<div class="brand-mark">'
        '<svg width="15" height="15" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">'
        '<path d="M10 1.6 11.95 8.05 18.4 10 11.95 11.95 10 18.4 8.05 11.95 1.6 10 8.05 8.05 10 1.6Z" fill="#225C4B"/>'
        '</svg>'
        '</div>'
        f'<div><div class="brand-name">{escape(APP_NAME.lower())}</div>'
        '<div class="brand-sub">Credit analytics</div></div>'
        '</div>'
        '<div class="side-rule"></div>',
        unsafe_allow_html=True,
    )


def render_sidebar_footer(
    loans: int,
    customers: int,
    db_size: str,
    min_date: date | str,
    max_date: date | str,
) -> None:
    st.markdown(
        '<div class="side-meta">'
        '<div class="side-meta-title">Data coverage</div>'
        f'<div class="side-meta-date">{format_date(min_date)} – {format_date(max_date)}</div>'
        '<div class="side-meta-grid">'
        f'<span><strong>{loans:,}</strong> loans</span>'
        f'<span><strong>{customers:,}</strong> customers</span>'
        '</div>'
        f'<div class="side-meta-foot"><span class="db-dot"></span>Local SQLite · {escape(db_size)}</div>'
        '<div class="side-meta-foot">Synthetic demonstration portfolio</div>'
        '</div>',
        unsafe_allow_html=True,
    )


def render_page_header(
    as_of: str,
    loans: int,
    customers: int,
    active_filters: int,
) -> None:
    filter_chip = (
        f'<span class="filter-chip">{active_filters} filter'
        f'{"s" if active_filters != 1 else ""} applied</span>'
        if active_filters
        else ""
    )
    st.markdown(
        '<div class="page-heading">'
        '<div class="page-kicker">Portfolio analytics</div>'
        '<h1 class="page-title">Loan portfolio</h1>'
        '<p class="page-subtitle">Exposure, origination and credit quality across the '
        'lending book.</p>'
        '<div class="page-meta">'
        f'<span><span class="live-dot"></span>As of {escape(as_of)}</span>'
        '<span class="sep">/</span>'
        f'<span><strong>{loans:,}</strong> loans</span>'
        '<span class="sep">/</span>'
        f'<span><strong>{customers:,}</strong> customers</span>'
        '<span class="sep">/</span>'
        '<span>USD</span>'
        f'{filter_chip}'
        '</div>'
        '</div>',
        unsafe_allow_html=True,
    )


def render_app_footer() -> None:
    st.markdown(
        '<div class="app-footer">'
        '<span>Northstar Credit Analytics</span>'
        '<span>Synthetic portfolio · Local SQLite workspace · Streamlit / Pandas / Plotly</span>'
        '</div>',
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Content components
# ---------------------------------------------------------------------------


def card_header(
    title: str,
    subtitle: str = "",
    meta: str = "",
    meta_label: str = "",
) -> None:
    aside = ""
    if meta:
        label = f"<small>{escape(meta_label)}</small>" if meta_label else ""
        aside = f'<div class="card-aside">{escape(meta)}{label}</div>'
    subtitle_html = f'<div class="card-sub">{escape(subtitle)}</div>' if subtitle else ""
    st.markdown(
        '<div class="card-head">'
        f'<div><div class="card-title">{escape(title)}</div>{subtitle_html}</div>'
        f'{aside}'
        '</div>',
        unsafe_allow_html=True,
    )


def render_metric_strip(items: list[dict], columns: int | None = None) -> None:
    cols = columns or len(items)
    cells = []
    for item in items:
        color = item.get("color", COLORS["primary"])
        detail = item.get("detail", "")
        cells.append(
            '<div class="metric-cell">'
            '<div class="metric-label">'
            f'<span class="dot" style="background:{escape(color)}"></span>'
            f'{escape(item["label"])}</div>'
            f'<div class="metric-value">{escape(item["value"])}</div>'
            f'<div class="metric-detail">{escape(detail)}</div>'
            '</div>'
        )
    st.markdown(
        f'<div class="metric-strip" style="--metric-cols:{int(cols)}">{"".join(cells)}</div>',
        unsafe_allow_html=True,
    )


def _card_head_html(
    title: str,
    subtitle: str = "",
    meta: str = "",
    meta_label: str = "",
) -> str:
    aside = ""
    if meta:
        label = f"<small>{escape(meta_label)}</small>" if meta_label else ""
        aside = f'<div class="card-aside">{escape(meta)}{label}</div>'
    subtitle_html = f'<div class="card-sub">{escape(subtitle)}</div>' if subtitle else ""
    return (
        '<div class="card-head">'
        f'<div><div class="card-title">{escape(title)}</div>{subtitle_html}</div>'
        f'{aside}'
        '</div>'
    )


def render_product_allocation(mix: pd.DataFrame) -> None:
    total = float(mix["outstanding_balance"].sum()) if not mix.empty else 0.0
    header = _card_head_html(
        "Outstanding by product",
        "Share of open balance",
        compact_currency(total),
        "open",
    )
    if mix.empty or total <= 0:
        body = '<div class="empty-block">No outstanding balance in this selection.</div>'
    else:
        rows = []
        for row in mix.sort_values("outstanding_balance", ascending=False).itertuples(index=False):
            share = float(row.outstanding_balance) / total * 100 if total else 0
            color = PRODUCT_COLORS.get(row.loan_type, COLORS["primary"])
            rows.append(
                '<div class="alloc-row">'
                '<div class="alloc-line">'
                '<span class="alloc-name">'
                f'<span class="alloc-dot" style="background:{escape(color)}"></span>'
                f'{escape(row.loan_type)}</span>'
                '<span class="alloc-value">'
                f'{compact_currency(row.outstanding_balance)}'
                f'<span class="alloc-share">{share:.1f}%</span>'
                '</span>'
                '</div>'
                f'<div class="alloc-track"><span style="width:{max(share, 1.2):.2f}%;background:{escape(color)}"></span></div>'
                '</div>'
            )
        body = f'<div class="allocation-list">{"".join(rows)}</div>'
    st.markdown(
        f'<div class="panel allocation-panel">{header}{body}</div>',
        unsafe_allow_html=True,
    )


def render_risk_panel(kpis: dict, dpd: pd.DataFrame) -> None:
    overdue = dpd[dpd["bucket"] != "Current"].copy() if not dpd.empty else dpd
    total_overdue = float(overdue["outstanding_balance"].sum()) if not overdue.empty else 0.0
    total_open = float(dpd["outstanding_balance"].sum()) if not dpd.empty else 0.0
    current_share = (
        float(dpd.loc[dpd["bucket"] == "Current", "outstanding_balance"].sum()) / total_open * 100
        if total_open
        else 0
    )
    bucket_colors = {
        "1–29 days": "#C9B576",
        "30–59 days": "#BE8254",
        "60–89 days": "#A85B47",
        "90+ days": "#963A32",
    }
    header = _card_head_html(
        "Credit quality",
        "Past-due balance by ageing bucket",
        f'{int(kpis.get("overdue_loans", 0)):,}',
        "overdue loans",
    )
    stat_html = (
        '<div class="risk-top">'
        '<div class="risk-stat"><span>PAR 30+</span>'
        f'<strong>{_pct(kpis.get("par30_rate", 0))}</strong></div>'
        '<div class="risk-stat"><span>90+ DPD exposure</span>'
        f'<strong>{compact_currency(kpis.get("par90_balance", 0))}</strong></div>'
        '</div>'
    )
    if overdue.empty or total_overdue <= 0:
        bar_html = '<div class="empty-block" style="min-height:90px">No overdue exposure.</div>'
        insight = "No past-due balances in the current selection."
    else:
        bar_parts = []
        legend_parts = []
        for row in overdue.itertuples(index=False):
            share = float(row.outstanding_balance) / total_overdue * 100 if total_overdue else 0
            color = bucket_colors.get(row.bucket, COLORS["primary"])
            bar_parts.append(
                f'<span style="width:{share:.2f}%;background:{color}" title="{escape(row.bucket)}"></span>'
            )
            legend_parts.append(
                '<span class="risk-legend-item">'
                f'<i style="background:{color}"></i>'
                f'<span>{escape(row.bucket)}</span><strong>{share:.0f}%</strong></span>'
            )
        bar_html = (
            '<div class="risk-bar-label"><span>Composition of past-due balance</span>'
            f'<span>{compact_currency(total_overdue)}</span></div>'
            f'<div class="risk-bar">{"".join(bar_parts)}</div>'
            f'<div class="risk-legend">{"".join(legend_parts)}</div>'
        )
        highest = overdue.sort_values("outstanding_balance", ascending=False).iloc[0]
        highest_share = float(highest["outstanding_balance"]) / total_overdue * 100
        insight = (
            f'Accounts <strong>{escape(highest["bucket"])}</strong> past due carry '
            f'{highest_share:.0f}% of past-due balance.'
        )
    insight_html = f'<div class="risk-insight">{insight}</div>'
    footer = (
        '<div class="panel-foot">'
        f'<span>Current book <strong>{current_share:.1f}%</strong></span>'
        f'<span>Weighted rate <strong>{_pct(kpis.get("weighted_avg_rate", 0), 2)}</strong></span>'
        '</div>'
    )
    st.markdown(
        f'<div class="panel risk-panel">{header}{stat_html}{bar_html}{insight_html}{footer}</div>',
        unsafe_allow_html=True,
    )


def render_segment_table(segment: pd.DataFrame) -> None:
    header = _card_head_html(
        "Segment performance",
        "Exposure and credit quality by customer type",
        f"{len(segment):,}",
        "segments",
    )
    if segment.empty:
        body = '<div class="empty-block">No segment data in this selection.</div>'
        footer = ""
    else:
        rows = []
        for row in segment.itertuples(index=False):
            default_class = "risk-text" if row.default_rate >= 5 else ("warn-text" if row.default_rate >= 3 else "")
            par_class = "risk-text" if row.par30_rate >= 5 else ("warn-text" if row.par30_rate >= 2 else "")
            rows.append(
                '<tr>'
                f'<td><span class="row-title">{escape(row.segment)}</span>'
                f'<span class="row-sub">{int(row.customer_count):,} customers</span></td>'
                f'<td class="num">{int(row.loan_count):,}</td>'
                f'<td class="num">{compact_currency(row.outstanding_balance)}</td>'
                f'<td class="num {default_class}">{_pct(row.default_rate)}</td>'
                f'<td class="num {par_class}">{_pct(row.par30_rate)}</td>'
                f'<td class="num">{_pct(row.avg_rate, 2)}</td>'
                '</tr>'
            )
        body = (
            '<table class="data-table">'
            '<thead><tr>'
            '<th>Segment</th><th class="num">Loans</th><th class="num">Outstanding</th>'
            '<th class="num">Default</th><th class="num">PAR 30+</th><th class="num">Avg rate</th>'
            '</tr></thead>'
            f'<tbody>{"".join(rows)}</tbody></table>'
        )
        riskiest = segment.sort_values("par30_rate", ascending=False).iloc[0]
        footer = (
            '<div class="table-footer">'
            f'<strong>{escape(riskiest["segment"])}</strong> has the highest PAR 30+ at '
            f'{riskiest["par30_rate"]:.1f}%. Default rate is calculated on originated principal.'
            '</div>'
        )
    st.markdown(
        f'<div class="panel table-panel">{header}{body}{footer}</div>',
        unsafe_allow_html=True,
    )


def render_exposure_list(top_exposures: pd.DataFrame, total_outstanding: float) -> None:
    header = _card_head_html(
        "Largest exposures",
        "Borrowers ranked by open balance",
        f"Top {len(top_exposures):,}" if not top_exposures.empty else "Top exposures",
    )
    if top_exposures.empty:
        body = '<div class="empty-block">No open exposures in this selection.</div>'
        footer = ""
    else:
        rows = []
        for index, row in enumerate(top_exposures.itertuples(index=False), start=1):
            risk_tag = ""
            if int(row.defaulted_loans) > 0:
                risk_tag = '<span class="risk-tag">Defaulted</span>'
            elif int(row.max_dpd) > 0:
                risk_tag = f'<span class="risk-tag">{int(row.max_dpd)} DPD</span>'
            rows.append(
                '<div class="exposure-row">'
                f'<div class="exposure-rank">{index:02d}</div>'
                '<div>'
                f'<div class="exposure-person">{escape(row.full_name)}</div>'
                f'<div class="exposure-meta">{escape(row.segment)} · {int(row.loan_count):,} loans</div>'
                '</div>'
                '<div>'
                f'<div class="exposure-value">{compact_currency(row.exposure)}</div>'
                f'{risk_tag}'
                '</div>'
                '</div>'
            )
        exposure_sum = float(top_exposures["exposure"].sum())
        share = exposure_sum / total_outstanding * 100 if total_outstanding else 0
        footer = (
            '<div class="panel-foot">'
            f'<span>Top {len(top_exposures):,} share <strong>{share:.1f}%</strong> of open balance</span>'
            '</div>'
        )
        body = f'<div class="exposure-list">{"".join(rows)}</div>'
    st.markdown(
        f'<div class="panel table-panel">{header}{body}{footer}</div>',
        unsafe_allow_html=True,
    )


def render_segment_risk_table(segment: pd.DataFrame) -> None:
    header = _card_head_html(
        "Segment risk",
        "Default and delinquency by customer type",
        "Watchlist",
    )
    if segment.empty:
        body = '<div class="empty-block">No segment data in this selection.</div>'
        footer = ""
    else:
        rows = []
        for row in segment.sort_values("par30_rate", ascending=False).itertuples(index=False):
            default_class = "risk-text" if row.default_rate >= 5 else ("warn-text" if row.default_rate >= 3 else "")
            par_class = "risk-text" if row.par30_rate >= 5 else ("warn-text" if row.par30_rate >= 2 else "")
            rows.append(
                '<tr>'
                f'<td><span class="row-title">{escape(row.segment)}</span>'
                f'<span class="row-sub">{int(row.customer_count):,} customers</span></td>'
                f'<td class="num {par_class}">{_pct(row.par30_rate)}</td>'
                f'<td class="num {default_class}">{_pct(row.default_rate)}</td>'
                f'<td class="num">{int(row.avg_dpd)} days</td>'
                '</tr>'
            )
        body = (
            '<table class="data-table">'
            '<thead><tr><th>Segment</th><th class="num">PAR 30+</th>'
            '<th class="num">Default</th><th class="num">Avg DPD</th></tr></thead>'
            f'<tbody>{"".join(rows)}</tbody></table>'
        )
        footer = (
            '<div class="table-footer">'
            'PAR and default rates are balance-weighted as of the latest refresh.'
            '</div>'
        )
    st.markdown(
        f'<div class="panel table-panel">{header}{body}{footer}</div>',
        unsafe_allow_html=True,
    )


def render_quality_checks(checks: pd.DataFrame) -> None:
    passed = int((checks["status"] == "Passed").sum()) if not checks.empty else 0
    header = _card_head_html(
        "Validation controls",
        "Run against the complete database, independent of filters",
        f"{passed}/{len(checks):,}",
        "passed",
    )
    if checks.empty:
        body = '<div class="empty-block">No validation controls available.</div>'
    else:
        split_at = (len(checks) + 1) // 2
        check_columns = [checks.iloc[:split_at], checks.iloc[split_at:]]
        columns_html = []
        for column in check_columns:
            entries = []
            for row in column.itertuples(index=False):
                pill_class = "status-pill" if row.status == "Passed" else "status-pill review"
                finding = (
                    f'<div class="quality-finding">{escape(row.finding)}</div>'
                    if row.status != "Passed"
                    else ""
                )
                entries.append(
                    '<div class="quality-entry">'
                    '<div class="quality-item">'
                    '<div>'
                    f'<div class="quality-name">{escape(row.check)}</div>'
                    f'<div class="quality-scope">{escape(row.scope)} · {escape(row.severity)}</div>'
                    '</div>'
                    f'<div><span class="{pill_class}">{escape(row.status)}</span></div>'
                    f'<div class="quality-count">{int(row.issues):,}</div>'
                    '</div>'
                    f'{finding}'
                    '</div>'
                )
            columns_html.append(
                '<div>'
                '<div class="quality-col-head"><span>Control</span><span>Result</span><span>Issues</span></div>'
                f'{"".join(entries)}'
                '</div>'
            )
        body = f'<div class="quality-columns">{"".join(columns_html)}</div>'
    st.markdown(
        f'<div class="panel quality-panel">{header}{body}</div>',
        unsafe_allow_html=True,
    )


def render_completeness(missing: pd.DataFrame) -> None:
    header = _card_head_html(
        "Field completeness",
        "Missing-value profile across the database",
        "",
    )
    if missing.empty:
        body = '<div class="empty-block">No field-level data available.</div>'
    else:
        critical = missing[missing["critical"]]
        critical_complete = int((critical["missing"] == 0).sum())
        critical_total = len(critical)
        coverage = 100 * critical_complete / critical_total if critical_total else 100.0
        optional = missing[(~missing["critical"]) & (missing["missing"] > 0)].sort_values(
            "missing", ascending=False
        )
        optional_rows = []
        for row in optional.head(8).itertuples(index=False):
            optional_rows.append(
                '<div class="coverage-row">'
                f'<span class="coverage-field">{escape(row.table)}.{escape(row.column)}</span>'
                f'<span class="coverage-missing">{int(row.missing):,} blank</span>'
                '</div>'
            )
        optional_html = (
            '<div class="optional-list">'
            '<div class="optional-title">Expected blank fields</div>'
            f'{"".join(optional_rows)}'
            '</div>'
            if optional_rows
            else ""
        )
        body = (
            '<div class="completeness-wide">'
            '<div class="coverage-top">'
            '<div class="coverage-line"><span class="coverage-label">Critical field coverage</span>'
            f'<span class="coverage-value">{coverage:.1f}%</span></div>'
            f'<div class="coverage-track"><span style="width:{coverage:.1f}%"></span></div>'
            f'<div class="coverage-caption">{critical_complete} of {critical_total} critical fields '
            'fully populated across the database.</div>'
            '<div class="coverage-note">Optional lifecycle dates are blank until a loan is closed '
            'or defaults. Critical-field completeness is scored separately.</div>'
            '</div>'
            f'{optional_html}'
            '</div>'
        )
    st.markdown(
        f'<div class="panel completeness-panel">{header}{body}</div>',
        unsafe_allow_html=True,
    )
