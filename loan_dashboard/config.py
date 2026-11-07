"""Application-wide configuration and presentation constants."""

from __future__ import annotations

import os
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
SAMPLE_DIR = DATA_DIR / "sample"
DB_PATH = Path(os.environ.get("LOAN_DB_PATH", DATA_DIR / "loan_portfolio.db"))

APP_TITLE = "Northstar | Loan Portfolio Analytics"
APP_NAME = "Northstar Credit"
APP_TAGLINE = "Portfolio Intelligence"

LOAN_TYPES = (
    "Personal Loan",
    "Home Loan",
    "Auto Loan",
    "Education Loan",
    "Business Loan",
    "Equipment Loan",
    "Credit Card",
)
STATUSES = ("Active", "Closed", "Defaulted")
SEGMENTS = ("Retail", "SME", "Corporate", "Premium")
RISK_GRADES = ("A", "B", "C", "D", "E")

# Cohesive palette shared by Plotly and the custom CSS.
COLORS = {
    "ink": "#0F172A",
    "muted": "#64748B",
    "primary": "#4F46E5",
    "primary_soft": "#EEF2FF",
    "teal": "#0D9488",
    "teal_soft": "#CCFBF1",
    "amber": "#D97706",
    "amber_soft": "#FEF3C7",
    "orange": "#EA580C",
    "red": "#DC2626",
    "red_soft": "#FEE2E2",
    "green": "#059669",
    "green_soft": "#D1FAE5",
    "border": "#E2E8F0",
    "surface": "#FFFFFF",
    "canvas": "#F4F6FA",
    "slate_900": "#0B1220",
}

PRODUCT_COLORS = {
    "Personal Loan": "#4F46E5",
    "Home Loan": "#0D9488",
    "Auto Loan": "#0EA5E9",
    "Education Loan": "#8B5CF6",
    "Business Loan": "#F59E0B",
    "Equipment Loan": "#EC4899",
    "Credit Card": "#94A3B8",
}

STATUS_COLORS = {
    "Active": "#4F46E5",
    "Closed": "#94A3B8",
    "Defaulted": "#DC2626",
}

RISK_COLORS = {
    "A": "#0D9488",
    "B": "#65A30D",
    "C": "#D97706",
    "D": "#EA580C",
    "E": "#DC2626",
}

CHART_CONFIG = {
    "displayModeBar": False,
    "responsive": True,
    "scrollZoom": False,
}

CURRENCY_SYMBOL = "$"
