"""Reusable presentation helpers and the dashboard's visual theme."""

from __future__ import annotations

from datetime import date
from html import escape

import streamlit as st

from .config import APP_NAME, APP_TAGLINE


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


def full_currency(value: float | int | None) -> str:
    return f"${float(value or 0):,.0f}"


def compact_number(value: float | int | None) -> str:
    value = float(value or 0)
    if value >= 1_000_000:
        return f"{value / 1_000_000:,.1f}M"
    if value >= 1_000:
        return f"{value / 1_000:,.1f}K"
    return f"{value:,.0f}"


def format_date(value: date | str | None) -> str:
    if value is None:
        return "—"
    if isinstance(value, str):
        value = date.fromisoformat(value[:10])
    return value.strftime("%d %b %Y")


def inject_css() -> None:
    st.markdown(
        """
        <style>
        :root {
            --ink: #0F172A;
            --muted: #64748B;
            --primary: #4F46E5;
            --teal: #0D9488;
            --amber: #D97706;
            --red: #DC2626;
            --border: #E7ECF3;
            --canvas: #F4F6FA;
            --white: #FFFFFF;
        }

        html, body, [class*="css"] {
            font-family: "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        }
        [data-testid="stAppViewContainer"] {
            background:
                radial-gradient(circle at 8% 0%, rgba(224, 231, 255, 0.75) 0, rgba(244, 246, 250, 0) 30%),
                radial-gradient(circle at 96% 12%, rgba(204, 251, 241, 0.55) 0, rgba(244, 246, 250, 0) 28%),
                #F4F6FA;
        }
        [data-testid="stMain"] .block-container {
            max-width: 1460px;
            padding: 1.25rem 2.1rem 3rem;
        }
        [data-testid="stHeader"] {
            background: transparent;
            height: 0;
        }
        [data-testid="stToolbar"], [data-testid="stDecoration"], #MainMenu, footer {
            visibility: hidden;
            display: none;
        }
        [data-testid="stSidebar"] {
            background: #0B1220;
            border-right: 1px solid #1E293B;
        }
        [data-testid="stSidebar"] > div:first-child {
            padding-top: 1.25rem;
        }
        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
            color: #CBD5E1;
        }
        [data-testid="stSidebar"] label,
        [data-testid="stSidebar"] .stSelectbox label,
        [data-testid="stSidebar"] .stMultiSelect label,
        [data-testid="stSidebar"] .stDateInput label {
            color: #CBD5E1 !important;
            font-size: 0.78rem !important;
            font-weight: 600 !important;
        }
        [data-testid="stSidebar"] [data-baseweb="select"] > div,
        [data-testid="stSidebar"] [data-testid="stMultiSelect"] [role="group"],
        [data-testid="stSidebar"] [data-testid="stMultiSelectTagsContainer"],
        [data-testid="stSidebar"] [data-testid="stDateInputField"],
        [data-testid="stSidebar"] [data-testid="stDateInput"] input {
            background: #111C30 !important;
            border-color: #243247 !important;
            color: #F1F5F9 !important;
        }
        [data-testid="stSidebar"] [data-testid="stMultiSelect"] [role="group"] {
            border-radius: 9px;
        }
        [data-testid="stSidebar"] [data-testid="stMultiSelect"] input,
        [data-testid="stSidebar"] [data-testid="stDateInput"] input {
            color: #F1F5F9 !important;
            background: transparent !important;
        }
        [data-testid="stSidebar"] [data-testid="stMultiSelect"] input::placeholder {
            color: #94A3B8 !important;
            opacity: 1 !important;
        }
        [data-testid="stSidebar"] [data-testid="stMultiSelect"] svg,
        [data-testid="stSidebar"] [data-testid="stDateInput"] svg {
            color: #94A3B8 !important;
        }
        [data-testid="stSidebar"] [data-testid="stDateInputField"] span {
            color: #F1F5F9 !important;
        }
        [data-testid="stSidebar"] [data-testid="stDateInputField"] [data-type="literal"],
        [data-testid="stSidebar"] [data-testid="stDateInputField"] > div > span {
            color: #94A3B8 !important;
        }
        [data-testid="stSidebar"] [data-testid="stDateInput"] [aria-hidden="true"] {
            color: #94A3B8 !important;
        }
        [data-testid="stSidebar"] [data-testid="stMultiSelect"] [data-tag] {
            background: #1E293B !important;
            color: #C7D2FE !important;
            border: 1px solid #334155 !important;
            border-radius: 6px !important;
        }
        [data-testid="stSidebar"] [data-testid="stMultiSelect"] [data-tag] span {
            color: #C7D2FE !important;
        }
        [data-testid="stSidebar"] [data-testid="stDateInputField"] {
            border: 1px solid #243247 !important;
            border-radius: 9px !important;
        }
        [data-testid="stSidebar"] [data-testid="stDateInput"] > div {
            background: transparent;
        }
        [data-testid="stSidebar"] hr {
            border-color: #1E293B;
        }
        [data-testid="stSidebar"] .stButton button {
            background: #111C30;
            color: #CBD5E1;
            border: 1px solid #243247;
            border-radius: 9px;
            font-size: 0.78rem;
            font-weight: 600;
            width: 100%;
        }
        [data-testid="stSidebar"] .stButton button:hover {
            border-color: #4F46E5;
            color: #E0E7FF;
        }

        .block-container > div {
            gap: 0.75rem;
        }
        [data-testid="stTabs"] [role="tablist"] {
            gap: 0.32rem;
            background: #FFFFFF;
            padding: 0.38rem;
            border-radius: 12px;
            border: 1px solid var(--border);
            width: fit-content;
            box-shadow: 0 1px 2px rgba(15, 23, 42, 0.03);
            margin-bottom: 0.55rem;
        }
        [data-testid="stTab"] {
            display: flex;
            align-items: center;
            min-height: 36px;
            border-radius: 8px;
            padding: 0.35rem 0.95rem;
            color: var(--muted) !important;
            background: transparent !important;
            cursor: pointer;
            transition: background 120ms ease, color 120ms ease;
        }
        [data-testid="stTab"] [data-testid="stMarkdownContainer"] p {
            color: inherit !important;
            font-size: 0.82rem;
            font-weight: 600;
            margin: 0;
        }
        [data-testid="stTab"]:hover {
            background: #F1F5F9 !important;
        }
        [data-testid="stTab"][aria-selected="true"] {
            background: #0F172A !important;
            color: #FFFFFF !important;
        }
        [data-testid="stTab"][aria-selected="true"] [data-testid="stMarkdownContainer"] p {
            color: #FFFFFF !important;
        }
        [data-testid="stTab"] .react-aria-SelectionIndicator {
            display: none;
        }
        [data-testid="stTabs"] [role="tablist"] > div:first-child {
            border-radius: 8px;
        }

        [data-testid="stVerticalBlockBorderWrapper"] {
            border: 1px solid var(--border) !important;
            border-radius: 16px !important;
            background: #FFFFFF;
            box-shadow: 0 8px 24px rgba(15, 23, 42, 0.035);
        }
        [data-testid="stVerticalBlockBorderWrapper"] > div {
            padding: 0.25rem 0.35rem;
        }
        .stButton button[kind="primary"] {
            background: #4F46E5;
            border-radius: 9px;
            border: none;
            font-weight: 600;
        }
        .stButton button[kind="primary"]:hover {
            background: #4338CA;
        }
        .stDownloadButton button {
            border-radius: 9px;
            border-color: #D8DFEA;
            font-weight: 600;
            color: #334155;
        }
        .stDownloadButton button:hover {
            border-color: #4F46E5;
            color: #4F46E5;
        }
        [data-testid="stDataFrame"] {
            border: 1px solid var(--border);
            border-radius: 12px;
            overflow: hidden;
        }
        [data-testid="stFileUploader"] {
            border-radius: 12px;
        }
        [data-testid="stFileUploaderDropzone"] {
            background: #F8FAFC;
            border-color: #CBD5E1;
            border-radius: 12px;
        }
        .stAlert {
            border-radius: 12px;
        }
        [data-testid="stMarkdownContainer"] h4 {
            font-size: 1.05rem;
            font-weight: 700;
            letter-spacing: -0.02em;
            color: var(--ink);
            margin: 0.15rem 0 0.55rem;
        }

        .brand {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            padding: 0.1rem 0.1rem 1.1rem;
        }
        .brand-logo {
            width: 38px;
            height: 38px;
            border-radius: 11px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #FFFFFF;
            font-weight: 800;
            font-size: 1.05rem;
            background: linear-gradient(145deg, #6366F1 0%, #4F46E5 55%, #0D9488 130%);
            box-shadow: 0 5px 18px rgba(79, 70, 229, 0.4);
        }
        .brand-name {
            color: #F8FAFC;
            font-weight: 700;
            font-size: 0.98rem;
            letter-spacing: -0.01em;
            line-height: 1.2;
        }
        .brand-sub {
            color: #64748B;
            font-size: 0.64rem;
            text-transform: uppercase;
            letter-spacing: 0.15em;
            margin-top: 0.22rem;
        }
        .sidebar-eyebrow {
            color: #64748B;
            font-size: 0.63rem;
            font-weight: 700;
            letter-spacing: 0.16em;
            text-transform: uppercase;
            margin: 0.15rem 0 0.6rem;
        }
        .sidebar-rule {
            height: 1px;
            background: #1E293B;
            margin: 1.2rem 0 1.1rem;
        }
        .sidebar-foot {
            padding: 0.9rem 0.95rem;
            border: 1px solid #1E293B;
            border-radius: 12px;
            background: #0F172A;
            margin-top: 1.3rem;
        }
        .sidebar-foot .dot {
            width: 7px;
            height: 7px;
            border-radius: 50%;
            background: #34D399;
            display: inline-block;
            box-shadow: 0 0 0 3px rgba(52, 211, 153, 0.13);
            margin-right: 0.45rem;
        }
        .sidebar-foot strong {
            color: #E2E8F0;
            font-size: 0.72rem;
            font-weight: 600;
        }
        .sidebar-foot small {
            display: block;
            color: #64748B;
            font-size: 0.66rem;
            line-height: 1.55;
            margin-top: 0.42rem;
        }
        .filter-count {
            display: inline-flex;
            align-items: center;
            border-radius: 999px;
            background: #1E293B;
            color: #A5B4FC;
            font-size: 0.66rem;
            font-weight: 700;
            padding: 0.22rem 0.55rem;
            margin-bottom: 0.55rem;
        }

        .hero {
            position: relative;
            overflow: hidden;
            border-radius: 20px;
            padding: 1.6rem 2rem 1.4rem;
            background:
                radial-gradient(circle at 86% 8%, rgba(99, 102, 241, 0.38) 0, transparent 34%),
                radial-gradient(circle at 100% 110%, rgba(13, 148, 136, 0.30) 0, transparent 35%),
                linear-gradient(118deg, #0B1220 0%, #111C35 55%, #172554 100%);
            border: 1px solid rgba(148, 163, 184, 0.14);
            box-shadow: 0 18px 38px rgba(15, 23, 42, 0.16);
            margin: 0.2rem 0 0.8rem;
        }
        .hero:after {
            content: "";
            position: absolute;
            width: 360px;
            height: 360px;
            right: -120px;
            top: -210px;
            border-radius: 50%;
            border: 1px solid rgba(165, 180, 252, 0.22);
            box-shadow: 0 0 0 36px rgba(165, 180, 252, 0.035), 0 0 0 80px rgba(165, 180, 252, 0.025);
        }
        .hero-eyebrow {
            color: #A5B4FC;
            font-size: 0.64rem;
            letter-spacing: 0.19em;
            font-weight: 700;
            text-transform: uppercase;
            margin-bottom: 0.55rem;
        }
        .hero-title {
            color: #F8FAFC;
            font-size: clamp(1.65rem, 2.6vw, 2.35rem);
            line-height: 1.1;
            letter-spacing: -0.035em;
            font-weight: 750;
            margin: 0;
        }
        .hero-title span {
            color: #A5B4FC;
        }
        .hero-copy {
            color: #94A3B8;
            font-size: 0.85rem;
            margin-top: 0.58rem;
            max-width: 610px;
            line-height: 1.55;
        }
        .hero-meta {
            display: flex;
            flex-wrap: wrap;
            gap: 0.45rem;
            margin-top: 1.05rem;
        }
        .hero-pill {
            display: inline-flex;
            align-items: center;
            gap: 0.35rem;
            border: 1px solid rgba(148, 163, 184, 0.2);
            background: rgba(15, 23, 42, 0.35);
            color: #CBD5E1;
            font-size: 0.68rem;
            font-weight: 600;
            border-radius: 999px;
            padding: 0.32rem 0.68rem;
            backdrop-filter: blur(5px);
        }
        .hero-pill .pulse {
            width: 6px;
            height: 6px;
            background: #34D399;
            border-radius: 50%;
            box-shadow: 0 0 0 3px rgba(52, 211, 153, 0.12);
        }

        .kpi-card {
            background: #FFFFFF;
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 1.05rem 1.15rem 1rem;
            min-height: 132px;
            box-shadow: 0 8px 24px rgba(15, 23, 42, 0.035);
            position: relative;
            overflow: hidden;
        }
        .kpi-card:before {
            content: "";
            position: absolute;
            left: 0;
            top: 0;
            bottom: 0;
            width: 3px;
            background: var(--accent, #4F46E5);
            opacity: 0.85;
        }
        .kpi-top {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 0.75rem;
            margin-bottom: 0.65rem;
        }
        .kpi-label {
            color: var(--muted);
            font-size: 0.68rem;
            font-weight: 700;
            letter-spacing: 0.09em;
            text-transform: uppercase;
        }
        .kpi-icon {
            width: 34px;
            height: 34px;
            min-width: 34px;
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            background: var(--icon-bg, #EEF2FF);
            color: var(--accent, #4F46E5);
        }
        .kpi-value {
            color: var(--ink);
            font-size: 1.78rem;
            font-weight: 750;
            letter-spacing: -0.035em;
            line-height: 1.1;
            font-variant-numeric: tabular-nums;
        }
        .kpi-detail {
            color: var(--muted);
            font-size: 0.69rem;
            margin-top: 0.52rem;
            line-height: 1.5;
        }
        .kpi-detail strong {
            color: #334155;
            font-weight: 650;
        }

        .section-head {
            display: flex;
            justify-content: space-between;
            align-items: flex-end;
            gap: 1rem;
            margin: 1.05rem 0 0.35rem;
        }
        .section-kicker {
            color: #94A3B8;
            font-size: 0.58rem;
            font-weight: 700;
            letter-spacing: 0.16em;
            text-transform: uppercase;
            margin-bottom: 0.22rem;
        }
        .section-title {
            color: var(--ink);
            font-size: 1.04rem;
            font-weight: 700;
            letter-spacing: -0.02em;
            margin: 0;
        }
        .section-note {
            color: var(--muted);
            font-size: 0.68rem;
            text-align: right;
            line-height: 1.4;
            max-width: 360px;
        }

        .risk-panel {
            background: #FFFFFF;
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 1.15rem 1.2rem 1.05rem;
            min-height: 330px;
            box-shadow: 0 8px 24px rgba(15, 23, 42, 0.035);
        }
        .risk-panel-head {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 1rem;
        }
        .risk-panel-title {
            color: var(--ink);
            font-size: 0.93rem;
            font-weight: 700;
            letter-spacing: -0.015em;
        }
        .risk-panel-badge {
            border-radius: 999px;
            background: #FFF7ED;
            border: 1px solid #FED7AA;
            color: #C2410C;
            font-size: 0.6rem;
            font-weight: 700;
            letter-spacing: 0.06em;
            padding: 0.2rem 0.5rem;
            text-transform: uppercase;
        }
        .risk-row {
            margin-bottom: 0.9rem;
        }
        .risk-row-top {
            display: flex;
            align-items: baseline;
            justify-content: space-between;
            gap: 1rem;
            margin-bottom: 0.34rem;
        }
        .risk-label {
            color: var(--muted);
            font-size: 0.7rem;
            font-weight: 600;
        }
        .risk-value {
            color: var(--ink);
            font-size: 0.9rem;
            font-weight: 750;
            font-variant-numeric: tabular-nums;
        }
        .meter {
            height: 6px;
            border-radius: 999px;
            background: #F1F5F9;
            overflow: hidden;
        }
        .meter span {
            display: block;
            height: 100%;
            border-radius: 999px;
            background: var(--meter, #4F46E5);
        }
        .risk-foot {
            display: flex;
            align-items: center;
            justify-content: space-between;
            border-top: 1px solid #F1F5F9;
            margin-top: 0.4rem;
            padding-top: 0.7rem;
            color: var(--muted);
            font-size: 0.65rem;
        }
        .risk-foot strong {
            color: #334155;
        }

        .mini-grid {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 0.8rem;
            margin: 0.2rem 0 0.5rem;
        }
        .mini-card {
            background: #FFFFFF;
            border: 1px solid var(--border);
            border-radius: 14px;
            padding: 0.85rem 1rem;
        }
        .mini-label {
            color: var(--muted);
            font-size: 0.64rem;
            font-weight: 700;
            letter-spacing: 0.08em;
            text-transform: uppercase;
        }
        .mini-value {
            color: var(--ink);
            font-size: 1.25rem;
            font-weight: 750;
            margin-top: 0.28rem;
            letter-spacing: -0.025em;
        }
        .mini-hint {
            color: #94A3B8;
            font-size: 0.63rem;
            margin-top: 0.2rem;
        }

        .eyebrow-note {
            color: #94A3B8;
            font-size: 0.68rem;
            line-height: 1.5;
        }
        .hero + div, .section-head + div {
            margin-top: 0.2rem;
        }
        .app-footer {
            color: #94A3B8;
            font-size: 0.64rem;
            line-height: 1.6;
            text-align: center;
            margin-top: 2rem;
            border-top: 1px solid #E7ECF3;
            padding-top: 1rem;
        }
        .import-step {
            color: #64748B;
            font-size: 0.72rem;
            line-height: 1.7;
        }
        .import-step strong {
            color: #334155;
        }
        .metric-inline {
            display: inline-flex;
            align-items: center;
            gap: 0.35rem;
            color: #64748B;
            font-size: 0.7rem;
        }
        .status-dot {
            width: 7px;
            height: 7px;
            border-radius: 50%;
            background: #10B981;
            display: inline-block;
        }

        @media (max-width: 900px) {
            [data-testid="stMain"] .block-container { padding: 1rem 1rem 2rem; }
            .hero { padding: 1.3rem 1.25rem; }
            .kpi-card { min-height: 120px; }
            .kpi-value { font-size: 1.5rem; }
            .section-note { display: none; }
            .mini-grid { grid-template-columns: 1fr; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_brand() -> None:
    st.markdown(
        f"""
        <div class="brand">
            <div class="brand-logo">N</div>
            <div>
                <div class="brand-name">{escape(APP_NAME)}</div>
                <div class="brand-sub">{escape(APP_TAGLINE)}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_hero(as_of: str, loan_count: int, customer_count: int) -> None:
    st.markdown(
        f"""
        <div class="hero">
            <div class="hero-eyebrow">Credit portfolio / command center</div>
            <h1 class="hero-title">Loan Portfolio <span>Analytics</span></h1>
            <div class="hero-copy">
                A single view of origination momentum, outstanding exposure, delinquency
                and credit quality across the lending book.
            </div>
            <div class="hero-meta">
                <span class="hero-pill"><span class="pulse"></span> Live portfolio view</span>
                <span class="hero-pill">As of {escape(as_of)}</span>
                <span class="hero-pill">{loan_count:,} loans · {customer_count:,} borrowers</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _kpi_icon(kind: str) -> str:
    icons = {
        "loans": (
            '<svg width="17" height="17" viewBox="0 0 24 24" fill="none" '
            'xmlns="http://www.w3.org/2000/svg"><path d="M4 7.5h16M6.5 4h11A2.5 2.5 0 0 1 20 6.5v11'
            'a2.5 2.5 0 0 1-2.5 2.5h-11A2.5 2.5 0 0 1 4 17.5v-11A2.5 2.5 0 0 1 6.5 4Z" '
            'stroke="currentColor" stroke-width="1.7"/><path d="M8 12h8M8 16h5" '
            'stroke="currentColor" stroke-width="1.7" stroke-linecap="round"/></svg>'
        ),
        "balance": (
            '<svg width="17" height="17" viewBox="0 0 24 24" fill="none" '
            'xmlns="http://www.w3.org/2000/svg"><path d="M4 8.5h16v9a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2v-9Z" '
            'stroke="currentColor" stroke-width="1.7"/><path d="M4 8.5V7a2 2 0 0 1 2-2h10.5" '
            'stroke="currentColor" stroke-width="1.7" stroke-linecap="round"/><path d="M15.5 14.2h1" '
            'stroke="currentColor" stroke-width="2.4" stroke-linecap="round"/></svg>'
        ),
        "overdue": (
            '<svg width="17" height="17" viewBox="0 0 24 24" fill="none" '
            'xmlns="http://www.w3.org/2000/svg"><path d="M12 4 3.8 18.2A1.1 1.1 0 0 0 4.8 20h14.4'
            'a1.1 1.1 0 0 0 1-1.8L12 4Z" stroke="currentColor" stroke-width="1.7" '
            'stroke-linejoin="round"/><path d="M12 9v4.5" stroke="currentColor" stroke-width="1.8" '
            'stroke-linecap="round"/><circle cx="12" cy="16.8" r="0.9" fill="currentColor"/></svg>'
        ),
        "default": (
            '<svg width="17" height="17" viewBox="0 0 24 24" fill="none" '
            'xmlns="http://www.w3.org/2000/svg"><path d="M12 3.5 19 6v5.2c0 4.4-2.9 7.8-7 9.3-4.1-1.5-7-4.9-7-9.3V6l7-2.5Z" '
            'stroke="currentColor" stroke-width="1.7" stroke-linejoin="round"/><path d="m9.2 11.8 1.9 1.9 3.8-4" '
            'stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>'
        ),
    }
    return icons[kind]


def _kpi_card(
    label: str,
    value: str,
    detail: str,
    icon: str,
    accent: str,
    icon_bg: str,
) -> str:
    return f"""
        <div class="kpi-card" style="--accent:{accent}; --icon-bg:{icon_bg};">
            <div class="kpi-top">
                <span class="kpi-label">{label}</span>
                <span class="kpi-icon">{_kpi_icon(icon)}</span>
            </div>
            <div class="kpi-value">{value}</div>
            <div class="kpi-detail">{detail}</div>
        </div>
    """


def render_kpi_cards(kpis: dict) -> None:
    columns = st.columns(4, gap="medium")
    cards = [
        _kpi_card(
            "Total loans",
            f"{int(kpis.get('total_loans', 0)):,}",
            (
                f"<strong>{int(kpis.get('customers', 0)):,}</strong> borrowers"
                f" · <strong>{kpis.get('active_share', 0):.0f}%</strong> active"
            ),
            "loans",
            "#4F46E5",
            "#EEF2FF",
        ),
        _kpi_card(
            "Outstanding balance",
            compact_currency(kpis.get("outstanding_balance", 0)),
            (
                f"<strong>{kpis.get('outstanding_ratio', 0):.1f}%</strong> of originated capital"
            ),
            "balance",
            "#0D9488",
            "#CCFBF1",
        ),
        _kpi_card(
            "Overdue loans",
            f"{int(kpis.get('overdue_loans', 0)):,}",
            (
                f"<strong>{compact_currency(kpis.get('overdue_balance', 0))}</strong> overdue"
                f" · {kpis.get('overdue_rate', 0):.1f}% of book"
            ),
            "overdue",
            "#D97706",
            "#FEF3C7",
        ),
        _kpi_card(
            "Default rate",
            f"{kpis.get('default_rate', 0):.1f}%",
            (
                f"<strong>{int(kpis.get('defaulted_loans', 0)):,}</strong> defaults"
                f" · {kpis.get('default_rate_balance', 0):.1f}% by balance"
            ),
            "default",
            "#DC2626",
            "#FEE2E2",
        ),
    ]
    for column, card in zip(columns, cards):
        with column:
            st.markdown(card, unsafe_allow_html=True)


def section_header(kicker: str, title: str, note: str = "") -> None:
    note_html = f'<div class="section-note">{escape(note)}</div>' if note else ""
    st.markdown(
        f"""
        <div class="section-head">
            <div>
                <div class="section-kicker">{escape(kicker)}</div>
                <div class="section-title">{escape(title)}</div>
            </div>
            {note_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_risk_posture(kpis: dict, concentration: float, top_product: str) -> None:
    par30 = float(kpis.get("par30_rate", 0))
    avg_rate = float(kpis.get("weighted_avg_rate", 0))
    avg_dpd = float(kpis.get("avg_dpd", 0))
    overdue_rate = float(kpis.get("overdue_rate", 0))

    def meter(value: float, maximum: float, color: str) -> str:
        width = max(2.0, min(100.0, (value / maximum) * 100 if maximum else 0))
        return f'<div class="meter"><span style="width:{width:.1f}%; --meter:{color};"></span></div>'

    st.markdown(
        f"""
        <div class="risk-panel">
            <div class="risk-panel-head">
                <div class="risk-panel-title">Portfolio risk posture</div>
                <span class="risk-panel-badge">Monitor</span>
            </div>
            <div class="risk-row">
                <div class="risk-row-top">
                    <span class="risk-label">Portfolio at risk · 30+ DPD</span>
                    <span class="risk-value">{par30:.1f}%</span>
                </div>
                {meter(par30, 20, "#DC2626")}
            </div>
            <div class="risk-row">
                <div class="risk-row-top">
                    <span class="risk-label">Overdue balance share</span>
                    <span class="risk-value">{overdue_rate:.1f}%</span>
                </div>
                {meter(overdue_rate, 20, "#D97706")}
            </div>
            <div class="risk-row">
                <div class="risk-row-top">
                    <span class="risk-label">Top product concentration</span>
                    <span class="risk-value">{concentration:.0f}%</span>
                </div>
                {meter(concentration, 60, "#4F46E5")}
            </div>
            <div class="risk-row">
                <div class="risk-row-top">
                    <span class="risk-label">Average days past due</span>
                    <span class="risk-value">{avg_dpd:.0f} days</span>
                </div>
                {meter(avg_dpd, 60, "#0D9488")}
            </div>
            <div class="risk-foot">
                <span>Weighted average rate <strong>{avg_rate:.2f}%</strong></span>
                <span>Largest: <strong>{escape(top_product or "—")}</strong></span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_mini_metrics(items: list[tuple[str, str, str]]) -> None:
    cards = "".join(
        f'<div class="mini-card">'
        f'<div class="mini-label">{escape(label)}</div>'
        f'<div class="mini-value">{escape(value)}</div>'
        f'<div class="mini-hint">{escape(hint)}</div>'
        f'</div>'
        for label, value, hint in items
    )
    st.markdown(f'<div class="mini-grid">{cards}</div>', unsafe_allow_html=True)


def render_sidebar_footer(loans: int, customers: int, db_size: str = "") -> None:
    size_note = f" · {db_size}" if db_size else ""
    st.markdown(
        f"""
        <div class="sidebar-foot">
            <strong><span class="dot"></span>Database connected</strong>
            <small>{loans:,} loans · {customers:,} customers{size_note}<br>
            Seeded demo portfolio for local analytics.</small>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_app_footer() -> None:
    st.markdown(
        """
        <div class="app-footer">
            Northstar Credit · Loan Portfolio Analytics · Synthetic demonstration data.
            Built with Streamlit, Pandas, Plotly and SQLite.
        </div>
        """,
        unsafe_allow_html=True,
    )
