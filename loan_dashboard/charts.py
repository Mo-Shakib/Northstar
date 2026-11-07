"""Streamlined Plotly charts for the portfolio workspace."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

from .config import COLORS, RISK_COLORS

FONT_FAMILY = (
    '-apple-system, BlinkMacSystemFont, "Segoe UI", "Helvetica Neue", Arial, sans-serif'
)
GRID_COLOR = "#EFEEE9"
TICK_COLOR = "#8A908A"

BUCKET_ORDER = ["Current", "1–29 days", "30–59 days", "60–89 days", "90+ days"]
BUCKET_COLORS = {
    "Current": "#DCE7E1",
    "1–29 days": "#C9B576",
    "30–59 days": "#BE8254",
    "60–89 days": "#A85B47",
    "90+ days": "#963A32",
}


def _empty_figure(message: str, height: int = 300) -> go.Figure:
    figure = go.Figure()
    figure.add_annotation(
        text=message,
        x=0.5,
        y=0.5,
        xref="paper",
        yref="paper",
        showarrow=False,
        font={"family": FONT_FAMILY, "size": 12, "color": COLORS["subtle"]},
    )
    figure.update_xaxes(visible=False)
    figure.update_yaxes(visible=False)
    figure.update_layout(
        height=height,
        margin={"l": 8, "r": 8, "t": 8, "b": 8},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    return figure


def _style(figure: go.Figure, height: int = 300) -> go.Figure:
    figure.update_layout(
        height=height,
        margin={"l": 6, "r": 6, "t": 10, "b": 4},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"family": FONT_FAMILY, "size": 11, "color": COLORS["ink_soft"]},
        hoverlabel={
            "bgcolor": "#FFFFFF",
            "bordercolor": COLORS["border_strong"],
            "font": {"family": FONT_FAMILY, "size": 11, "color": COLORS["ink"]},
        },
        showlegend=False,
        hovermode="x unified",
    )
    figure.update_xaxes(
        showgrid=False,
        zeroline=False,
        linecolor=COLORS["border"],
        ticks="",
        tickfont={"size": 10, "color": TICK_COLOR},
    )
    figure.update_yaxes(
        showgrid=True,
        gridcolor=GRID_COLOR,
        gridwidth=1,
        zeroline=False,
        linecolor=COLORS["border"],
        ticks="",
        tickfont={"size": 10, "color": TICK_COLOR},
    )
    return figure


def monthly_originations_chart(frame: pd.DataFrame) -> go.Figure:
    if frame.empty:
        return _empty_figure("No disbursements in this selection.")

    chart = frame.copy()
    chart["month"] = pd.to_datetime(chart["month"])
    chart = chart.set_index("month").sort_index()
    chart = chart.reindex(
        pd.date_range(chart.index.min(), chart.index.max(), freq="MS"),
        fill_value=0,
    )
    chart.index.name = "month"

    figure = go.Figure(
        go.Bar(
            x=chart.index,
            y=chart["disbursed_amount"],
            customdata=chart["loan_count"],
            marker={"color": COLORS["primary"], "line": {"width": 0}},
            opacity=0.86,
            hovertemplate=(
                "<b>%{x|%b %Y}</b><br>"
                "Disbursed $%{y:,.0f}<br>"
                "%{customdata:,.0f} loans originated<extra></extra>"
            ),
        )
    )
    _style(figure, height=298)
    figure.update_layout(bargap=0.46, hovermode="x unified")
    figure.update_xaxes(tickformat="%b %y", dtick="M3")
    figure.update_yaxes(tickprefix="$", tickformat="~s", rangemode="tozero")
    return figure


def overdue_trend_chart(frame: pd.DataFrame) -> go.Figure:
    if frame.empty:
        return _empty_figure("No month-end snapshots in this selection.")

    chart = frame.copy()
    chart["snapshot_date"] = pd.to_datetime(chart["snapshot_date"])
    chart = chart.sort_values("snapshot_date")

    figure = go.Figure(
        go.Scatter(
            x=chart["snapshot_date"],
            y=chart["overdue_balance"],
            mode="lines",
            line={"color": COLORS["red"], "width": 2, "shape": "spline", "smoothing": 0.55},
            fill="tozeroy",
            fillcolor="rgba(169, 68, 60, 0.06)",
            customdata=chart["overdue_loans"],
            hovertemplate=(
                "<b>%{x|%b %Y}</b><br>"
                "Overdue balance $%{y:,.0f}<br>"
                "%{customdata:,.0f} overdue loans<extra></extra>"
            ),
        )
    )
    _style(figure, height=305)
    figure.update_layout(hovermode="x unified")
    figure.update_xaxes(tickformat="%b %y", dtick="M2")
    figure.update_yaxes(tickprefix="$", tickformat="~s", rangemode="tozero")
    return figure


def dpd_distribution_chart(frame: pd.DataFrame) -> go.Figure:
    if frame.empty:
        return _empty_figure("No open loans in this selection.")

    present = set(frame["bucket"])
    order = [bucket for bucket in BUCKET_ORDER if bucket in present]
    chart = frame.set_index("bucket").reindex(order).reset_index()
    positions = [
        "inside" if bucket == "Current" and value >= 140 else "outside"
        for bucket, value in zip(chart["bucket"], chart["loan_count"])
    ]
    figure = go.Figure(
        go.Bar(
            x=chart["loan_count"],
            y=chart["bucket"],
            orientation="h",
            marker={
                "color": [BUCKET_COLORS.get(bucket, COLORS["primary"]) for bucket in chart["bucket"]],
                "line": {"width": 0},
            },
            text=chart["loan_count"].map(lambda value: f"{int(value):,}"),
            textposition=positions,
            textfont={"size": 10, "color": COLORS["ink"]},
            insidetextfont={"size": 10, "color": COLORS["ink"]},
            outsidetextfont={"size": 10, "color": COLORS["ink"]},
            customdata=chart["outstanding_balance"],
            hovertemplate=(
                "<b>%{y}</b><br>"
                "%{x:,.0f} loans<br>"
                "Outstanding $%{customdata:,.0f}<extra></extra>"
            ),
        )
    )
    _style(figure, height=305)
    figure.update_layout(
        hovermode="closest",
        margin={"l": 4, "r": 52, "t": 8, "b": 4},
        showlegend=False,
    )
    figure.update_xaxes(showgrid=True, gridcolor=GRID_COLOR, rangemode="tozero")
    figure.update_yaxes(showgrid=False, autorange="reversed")
    return figure


def risk_grade_chart(frame: pd.DataFrame) -> go.Figure:
    if frame.empty:
        return _empty_figure("No risk-grade data in this selection.")

    chart = frame.sort_values("risk_grade")
    figure = go.Figure(
        go.Bar(
            x=chart["risk_grade"],
            y=chart["default_rate"],
            marker={
                "color": [RISK_COLORS.get(grade, COLORS["primary"]) for grade in chart["risk_grade"]],
                "line": {"width": 0},
            },
            text=chart["default_rate"].map(lambda value: f"{value:.1f}%"),
            textposition="outside",
            textfont={"size": 10, "color": COLORS["ink_soft"]},
            customdata=chart[["loan_count", "outstanding_balance"]],
            hovertemplate=(
                "<b>Grade %{x}</b><br>"
                "Default rate %{y:.2f}%<br>"
                "%{customdata[0]:,.0f} loans<br>"
                "Outstanding $%{customdata[1]:,.0f}<extra></extra>"
            ),
        )
    )
    _style(figure, height=305)
    figure.update_layout(
        hovermode="closest",
        xaxis={"type": "category"},
        yaxis={"ticksuffix": "%", "rangemode": "tozero"},
    )
    return figure


def vintage_chart(frame: pd.DataFrame) -> go.Figure:
    if frame.empty:
        return _empty_figure("No vintage data in this selection.")

    chart = frame.sort_values("vintage")
    figure = go.Figure(
        go.Scatter(
            x=chart["vintage"],
            y=chart["default_rate"],
            mode="lines+markers",
            line={"color": COLORS["primary"], "width": 2, "shape": "spline", "smoothing": 0.35},
            marker={
                "size": 5,
                "color": COLORS["surface"],
                "line": {"color": COLORS["primary"], "width": 1.5},
            },
            fill="tozeroy",
            fillcolor="rgba(34, 92, 75, 0.05)",
            customdata=chart[["loan_count", "principal"]],
            hovertemplate=(
                "<b>%{x}</b><br>"
                "Default rate %{y:.2f}%<br>"
                "%{customdata[0]:,.0f} loans<br>"
                "Originated $%{customdata[1]:,.0f}<extra></extra>"
            ),
        )
    )
    _style(figure, height=288)
    figure.update_layout(hovermode="x unified")
    figure.update_xaxes(tickangle=-30, dtick=2)
    figure.update_yaxes(ticksuffix="%", rangemode="tozero")
    return figure
