"""Application-wide configuration and presentation constants."""

from __future__ import annotations

import os
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
SAMPLE_DIR = DATA_DIR / "sample"
ASSETS_DIR = ROOT_DIR / "assets"
DB_PATH = Path(os.environ.get("LOAN_DB_PATH", DATA_DIR / "loan_portfolio.db"))

APP_TITLE = "Northstar | Loan Portfolio Analytics"
APP_NAME = "Northstar"
APP_TAGLINE = "Credit Analytics"

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

# Quiet, editorial palette shared by Plotly and the custom CSS.
COLORS = {
    "ink": "#171B18",
    "muted": "#6C726D",
    "subtle": "#91968F",
    "primary": "#225C4B",
    "primary_hover": "#194939",
    "primary_soft": "#EAF1ED",
    "accent": "#B08A5A",
    "amber": "#A46B2A",
    "amber_soft": "#F6EDE0",
    "orange": "#B26A42",
    "red": "#A9443C",
    "red_soft": "#F4E8E5",
    "green": "#2F7259",
    "green_soft": "#EAF1ED",
    "info": "#3D5F78",
    "border": "#E4E1D9",
    "border_strong": "#D5D1C7",
    "surface": "#FFFFFF",
    "surface_soft": "#FAF9F5",
    "canvas": "#F3F1EB",
    "sidebar": "#F8F6F1",
    "ink_soft": "#333934",
}

PRODUCT_COLORS = {
    "Home Loan": "#2E5D4B",
    "Business Loan": "#496275",
    "Auto Loan": "#A17C56",
    "Personal Loan": "#7A6889",
    "Education Loan": "#B39A60",
    "Equipment Loan": "#747E67",
    "Credit Card": "#A6A299",
}

STATUS_COLORS = {
    "Active": "#2E5D4B",
    "Closed": "#A6A299",
    "Defaulted": "#A9443C",
}

RISK_COLORS = {
    "A": "#2F7259",
    "B": "#748354",
    "C": "#A98243",
    "D": "#B56A45",
    "E": "#A9443C",
}

CHART_CONFIG = {
    "displayModeBar": False,
    "responsive": True,
    "scrollZoom": False,
}

CURRENCY_SYMBOL = "$"
