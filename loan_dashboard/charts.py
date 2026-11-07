"""Plotly chart builders with a consistent, dashboard-friendly visual style."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from .config import COLORS, PRODUCT_COLORS, RISK_COLORS

FONT_FAMILY = "Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"
GRID_COLOR = "#EEF2F7"
AXIS_COLOR = "#94A3B8"


def _empty_figure(message: str, height: int = 320) -> go.Figure:
    figure = go.Figure()
    figure.add_annotation(
        text=message,
        x=0.5,
        y=0.5,
        xref="paper",
        yref="paper",
        showarrow=False,
        font={"family": FONT_FAMILY, "size": 13, "color": COLORS["muted"]},
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


def _style(figure: go.Figure, height: int = 320) -> go.Figure:
    figure.update_layout(
        height=height,
        margin={"l": 12, "r": 12, "t": 12, "b": 8},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"family": FONT_FAMILY, "size": 12, "color": COLORS["ink"]},
        hoverlabel={
            "bgcolor": "#0F172A",
            "bordercolor": "#0F172A",
            "font": {"family": FONT_FAMILY, "size": 12, "color": "#FFFFFF"},
        },
        legend={
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.02,
            "xanchor": "left",
            "x": 0,
            "font": {"size": 11, "color": COLORS["muted"]},
        },
    )
    figure.update_xaxes(
        showgrid=False,
        zeroline=False,
        linecolor=COLORS["border"],
        tickfont={"size": 11, "color": COLORS["muted"]},
    )
    figure.update_yaxes(
        showgrid=True,
        gridcolor=GRID_COLOR,
        gridwidth=1,
        zeroline=False,
        linecolor=COLORS["border"],
        tickfont={"size": 11, "color": COLORS["muted"]},
    )
    return figure


def monthly_originations_chart(frame: pd.DataFrame) -> go.Figure:
    if frame.empty:
        return _empty_figure("No disbursements match the selected filters.")

    chart = frame.copy()
    chart["month"] = pd.to_datetime(chart["month"])
    chart = chart.set_index("month").sort_index()
    full_range = pd.date_range(chart.index.min(), chart.index.max(), freq="MS")
    chart = chart.reindex(full_range, fill_value=0)
    chart.index.name = "month"

    figure = make_subplots(specs=[[{"secondary_y": True}]])
    figure.add_trace(
        go.Bar(
            x=chart.index,
            y=chart["disbursed_amount"],
            name="Disbursed amount",
            marker={"color": COLORS["primary"], "line": {"width": 0}},
            opacity=0.92,
            hovertemplate="<b>%{x|%b %Y}</b><br>Disbursed: $%{y:,.0f}<extra></extra>",
        ),
        secondary_y=False,
    )
    figure.add_trace(
        go.Scatter(
            x=chart.index,
            y=chart["loan_count"],
            name="Loans originated",
            mode="lines+markers",
            line={"color": COLORS["teal"], "width": 2.5},
            marker={"size": 5, "color": COLORS["teal"]},
            hovertemplate="<b>%{x|%b %Y}</b><br>Loans: %{y:,.0f}<extra></extra>",
        ),
        secondary_y=True,
    )
    _style(figure, height=320)
    figure.update_layout(
        bargap=0.42,
        hovermode="x unified",
        legend={"orientation": "h", "y": 1.08, "x": 0},
    )
    figure.update_xaxes(tickformat="%b %y", dtick="M3", ticks="")
    figure.update_yaxes(
        tickprefix="$",
        tickformat="~s",
        secondary_y=False,
        rangemode="tozero",
    )
    figure.update_yaxes(
        showgrid=False,
        secondary_y=True,
        rangemode="tozero",
        tickformat="d",
        dtick=10,
    )
    return figure


def portfolio_mix_chart(frame: pd.DataFrame) -> go.Figure:
    if frame.empty or frame["outstanding_balance"].sum() <= 0:
        return _empty_figure("No outstanding balance in this selection.")

    chart = frame[frame["outstanding_balance"] > 0].copy()
    chart = chart.sort_values("outstanding_balance", ascending=False)
    total = chart["outstanding_balance"].sum()
    colors = [PRODUCT_COLORS.get(product, COLORS["primary"]) for product in chart["loan_type"]]

    figure = go.Figure(
        go.Pie(
            labels=chart["loan_type"],
            values=chart["outstanding_balance"],
            hole=0.66,
            sort=False,
            domain={"x": [0, 0.63], "y": [0, 1]},
            marker={"colors": colors, "line": {"color": "#FFFFFF", "width": 2}},
            customdata=chart["share"],
            textinfo="none",
            hovertemplate=(
                "<b>%{label}</b><br>Outstanding: $%{value:,.0f}"
                "<br>Book share: %{customdata:.1f}%<extra></extra>"
            ),
        )
    )
    _style(figure, height=320)
    figure.update_layout(
        margin={"l": 4, "r": 8, "t": 8, "b": 8},
        showlegend=True,
        legend={
            "orientation": "v",
            "yanchor": "middle",
            "y": 0.5,
            "xanchor": "right",
            "x": 0.99,
            "font": {"size": 9, "color": COLORS["muted"]},
            "itemsizing": "constant",
            "tracegroupgap": 0,
        },
        annotations=[
            {
                "text": (
                    f"<span style='font-size:10px;color:{COLORS['muted']}'>OUTSTANDING</span><br>"
                    f"<span style='font-size:19px;font-weight:700;color:{COLORS['ink']}'>"
                    f"${total / 1_000_000:,.1f}M</span>"
                ),
                "x": 0.315,
                "y": 0.5,
                "showarrow": False,
                "align": "center",
            }
        ],
    )
    return figure


def overdue_trend_chart(frame: pd.DataFrame) -> go.Figure:
    if frame.empty:
        return _empty_figure("No month-end snapshots match the selected filters.")

    chart = frame.copy()
    chart["snapshot_date"] = pd.to_datetime(chart["snapshot_date"])
    chart = chart.sort_values("snapshot_date")

    figure = make_subplots(specs=[[{"secondary_y": True}]])
    figure.add_trace(
        go.Scatter(
            x=chart["snapshot_date"],
            y=chart["overdue_balance"],
            name="Overdue balance",
            mode="lines+markers",
            line={"color": COLORS["red"], "width": 2.6, "shape": "spline", "smoothing": 0.9},
            marker={"size": 5, "color": COLORS["red"]},
            fill="tozeroy",
            fillcolor="rgba(220, 38, 38, 0.09)",
            hovertemplate="<b>%{x|%b %Y}</b><br>Overdue: $%{y:,.0f}<extra></extra>",
        ),
        secondary_y=False,
    )
    figure.add_trace(
        go.Scatter(
            x=chart["snapshot_date"],
            y=chart["overdue_loans"],
            name="Overdue loans",
            mode="lines",
            line={"color": COLORS["amber"], "width": 2, "dash": "dot"},
            hovertemplate="<b>%{x|%b %Y}</b><br>Loans: %{y:,.0f}<extra></extra>",
        ),
        secondary_y=True,
    )
    _style(figure, height=330)
    figure.update_layout(
        hovermode="x unified",
        legend={"orientation": "h", "y": 1.08, "x": 0},
    )
    figure.update_xaxes(tickformat="%b %y", dtick="M2", ticks="")
    figure.update_yaxes(tickprefix="$", tickformat="~s", secondary_y=False, rangemode="tozero")
    figure.update_yaxes(
        showgrid=False,
        secondary_y=True,
        rangemode="tozero",
        tickformat="d",
        nticks=5,
    )
    return figure


def dpd_distribution_chart(frame: pd.DataFrame) -> go.Figure:
    if frame.empty:
        return _empty_figure("No open loans match the selected filters.", height=300)

    bucket_order = ["Current", "1–29 days", "30–59 days", "60–89 days", "90+ days"]
    bucket_colors = {
        "Current": COLORS["teal"],
        "1–29 days": "#F59E0B",
        "30–59 days": "#EA580C",
        "60–89 days": "#DC2626",
        "90+ days": "#991B1B",
    }
    chart = (
        frame.set_index("bucket")
        .reindex([bucket for bucket in bucket_order if bucket in set(frame["bucket"])])
        .reset_index()
    )
    chart = chart.dropna(subset=["loan_count"])

    positions = ["inside" if value >= 150 else "outside" for value in chart["loan_count"]]
    figure = go.Figure(
        go.Bar(
            x=chart["loan_count"],
            y=chart["bucket"],
            orientation="h",
            marker={
                "color": [bucket_colors.get(bucket, COLORS["primary"]) for bucket in chart["bucket"]],
                "line": {"width": 0},
            },
            text=chart["loan_count"].map(lambda value: f"{int(value):,}"),
            textposition=positions,
            insidetextfont={"size": 11, "color": "#FFFFFF"},
            outsidetextfont={"size": 11, "color": COLORS["ink"]},
            customdata=chart["outstanding_balance"],
            hovertemplate=(
                "<b>%{y}</b><br>Loans: %{x:,.0f}"
                "<br>Outstanding: $%{customdata:,.0f}<extra></extra>"
            ),
        )
    )
    _style(figure, height=300)
    figure.update_layout(
        xaxis_title=None,
        yaxis_title=None,
        margin={"l": 8, "r": 64, "t": 8, "b": 8},
        showlegend=False,
        xaxis={"showgrid": True, "gridcolor": GRID_COLOR, "rangemode": "tozero"},
    )
    figure.update_yaxes(showgrid=False, autorange="reversed")
    return figure


def risk_grade_chart(frame: pd.DataFrame) -> go.Figure:
    if frame.empty:
        return _empty_figure("No risk-grade data for this selection.", height=300)

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
            textfont={"size": 11, "color": COLORS["ink"]},
            customdata=chart[["loan_count", "outstanding_balance"]],
            hovertemplate=(
                "<b>Grade %{x}</b><br>Default rate: %{y:.2f}%"
                "<br>Loans: %{customdata[0]:,.0f}"
                "<br>Outstanding: $%{customdata[1]:,.0f}<extra></extra>"
            ),
        )
    )
    _style(figure, height=300)
    figure.update_layout(
        margin={"l": 8, "r": 8, "t": 12, "b": 8},
        showlegend=False,
        xaxis={"title": None, "type": "category"},
        yaxis={"ticksuffix": "%", "rangemode": "tozero"},
    )
    return figure


def vintage_chart(frame: pd.DataFrame) -> go.Figure:
    if frame.empty:
        return _empty_figure("No vintage data for this selection.", height=300)

    chart = frame.sort_values("vintage")
    figure = go.Figure(
        go.Scatter(
            x=chart["vintage"],
            y=chart["default_rate"],
            mode="lines+markers",
            line={"color": COLORS["primary"], "width": 2.6, "shape": "spline", "smoothing": 0.7},
            marker={"size": 7, "color": COLORS["primary"], "line": {"width": 2, "color": "#FFFFFF"}},
            fill="tozeroy",
            fillcolor="rgba(79, 70, 229, 0.07)",
            customdata=chart[["loan_count", "principal"]],
            hovertemplate=(
                "<b>%{x}</b><br>Default rate: %{y:.2f}%"
                "<br>Loans: %{customdata[0]:,.0f}"
                "<br>Originated: $%{customdata[1]:,.0f}<extra></extra>"
            ),
        )
    )
    _style(figure, height=300)
    figure.update_layout(
        showlegend=False,
        margin={"l": 8, "r": 8, "t": 12, "b": 8},
        xaxis={"title": None},
        yaxis={"ticksuffix": "%", "rangemode": "tozero"},
    )
    return figure
