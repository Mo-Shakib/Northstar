"""Northstar Credit — Loan Portfolio Analytics Dashboard.

Run locally with:
    streamlit run app.py
"""

from __future__ import annotations

from datetime import date

import pandas as pd
import streamlit as st

from loan_dashboard.charts import (
    dpd_distribution_chart,
    monthly_originations_chart,
    overdue_trend_chart,
    portfolio_mix_chart,
    risk_grade_chart,
    vintage_chart,
)
from loan_dashboard.config import (
    APP_TITLE,
    CHART_CONFIG,
    DB_PATH,
    LOAN_TYPES,
    SEGMENTS,
    STATUSES,
)
from loan_dashboard.csv_io import (
    build_import_template,
    frame_to_csv_bytes,
    read_csv_upload,
    validate_upload_against_database,
)
from loan_dashboard.database import (
    ensure_database,
    fetch_customer_ids,
    table_counts,
    upsert_loans,
)
from loan_dashboard.quality import run_quality_checks
from loan_dashboard.queries import (
    PortfolioFilters,
    get_dpd_buckets,
    get_filter_options,
    get_kpis,
    get_loans_table,
    get_monthly_originations,
    get_overdue_trend,
    get_portfolio_mix,
    get_quarterly_vintage,
    get_risk_grade_performance,
    get_segment_performance,
    get_top_exposures,
)
from loan_dashboard.ui import (
    compact_currency,
    format_date,
    inject_css,
    render_app_footer,
    render_brand,
    render_hero,
    render_kpi_cards,
    render_mini_metrics,
    render_risk_posture,
    render_sidebar_footer,
    section_header,
)

st.set_page_config(
    page_title=APP_TITLE,
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_css()


@st.cache_resource(show_spinner=False)
def bootstrap_database(database_path: str) -> dict[str, int]:
    return ensure_database(database_path)


try:
    with st.spinner("Preparing the portfolio database…"):
        bootstrap_database(str(DB_PATH))
    DATABASE_COUNTS = table_counts(DB_PATH)
except Exception as error:  # pragma: no cover - protects the UI from a broken file
    st.error(f"Could not initialize the database: {error}")
    st.stop()

if DATABASE_COUNTS.get("loans", 0) == 0:
    st.error("The portfolio database is empty. Run `python init_db.py --reset` and reload.")
    st.stop()

# ---------------------------------------------------------------------------
# Sidebar filters
# ---------------------------------------------------------------------------
with st.sidebar:
    render_brand()
    st.markdown('<div class="sidebar-eyebrow">Portfolio filters</div>', unsafe_allow_html=True)

    options = get_filter_options(DB_PATH)
    type_counts = dict(options["loan_types"])
    status_counts = dict(options["statuses"])
    segment_counts = dict(options["segments"])
    available_types = [name for name, _ in options["loan_types"]] or list(LOAN_TYPES)
    available_statuses = [name for name, _ in options["statuses"]] or list(STATUSES)
    available_segments = [name for name, _ in options["segments"]] or list(SEGMENTS)

    def reset_filters() -> None:
        for key in (
            "filter_dates",
            "filter_loan_types",
            "filter_statuses",
            "filter_segments",
        ):
            st.session_state.pop(key, None)

    if st.button("Reset filters", on_click=reset_filters, width="stretch"):
        pass

    date_range = st.date_input(
        "Disbursement date range",
        value=(options["min_date"], options["max_date"]),
        min_value=options["min_date"],
        max_value=options["max_date"],
        key="filter_dates",
        format="DD/MM/YYYY",
        help="Filter loans by when they were disbursed. Applies to every tab.",
    )
    if isinstance(date_range, (tuple, list)):
        if len(date_range) >= 2:
            start_date, end_date = date_range[0], date_range[1]
        elif len(date_range) == 1:
            start_date = end_date = date_range[0]
        else:
            start_date, end_date = options["min_date"], options["max_date"]
    else:
        start_date = end_date = date_range

    selected_types = st.multiselect(
        "Loan type",
        options=available_types,
        default=[],
        key="filter_loan_types",
        format_func=lambda value: f"{value}  ·  {type_counts.get(value, 0):,}",
        placeholder="All loan types",
        help="Leave empty to include all products.",
    )
    selected_statuses = st.multiselect(
        "Loan status",
        options=available_statuses,
        default=[],
        key="filter_statuses",
        format_func=lambda value: f"{value}  ·  {status_counts.get(value, 0):,}",
        placeholder="All statuses",
        help="Leave empty to include all statuses.",
    )
    selected_segments = st.multiselect(
        "Customer segment",
        options=available_segments,
        default=[],
        key="filter_segments",
        format_func=lambda value: f"{value}  ·  {segment_counts.get(value, 0):,}",
        placeholder="All segments",
        help="Leave empty to include all customer segments.",
    )

    active_filters = 0
    active_filters += int(start_date != options["min_date"] or end_date != options["max_date"])
    active_filters += int(bool(selected_types))
    active_filters += int(bool(selected_statuses))
    active_filters += int(bool(selected_segments))
    st.markdown(
        f'<div class="filter-count">{active_filters} active filter'
        f'{"s" if active_filters != 1 else ""}</div>',
        unsafe_allow_html=True,
    )

    st.markdown('<div class="sidebar-rule"></div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-eyebrow">Coverage</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="import-step">Disbursements from <strong>{format_date(options["min_date"])}'
        f'</strong> to <strong>{format_date(options["max_date"])}</strong>.<br>'
        "All metrics update instantly when filters change.</div>",
        unsafe_allow_html=True,
    )
    db_size = f"{DB_PATH.stat().st_size / 1_000_000:.1f} MB" if DB_PATH.exists() else ""
    render_sidebar_footer(
        DATABASE_COUNTS.get("loans", 0),
        DATABASE_COUNTS.get("customers", 0),
        db_size,
    )

filters = PortfolioFilters(
    start_date=start_date,
    end_date=end_date,
    loan_types=tuple(selected_types),
    statuses=tuple(selected_statuses),
    segments=tuple(selected_segments),
)

# ---------------------------------------------------------------------------
# Data access (queries are intentionally uncached: local SQLite is fast and
# imported records must appear immediately on the next rerun)
# ---------------------------------------------------------------------------
kpis = get_kpis(filters, DB_PATH)
monthly = get_monthly_originations(filters, DB_PATH)
mix = get_portfolio_mix(filters, DB_PATH)
overdue_trend = get_overdue_trend(filters, DB_PATH)
dpd = get_dpd_buckets(filters, DB_PATH)
segment_performance = get_segment_performance(filters, DB_PATH)
risk_performance = get_risk_grade_performance(filters, DB_PATH)
vintage = get_quarterly_vintage(filters, DB_PATH)
top_exposures = get_top_exposures(filters, limit=8, db_path=DB_PATH)
loans_table = get_loans_table(filters, DB_PATH)

top_product = str(mix.iloc[0]["loan_type"]) if not mix.empty else "—"
top_product_share = float(mix.iloc[0]["share"]) if not mix.empty else 0.0
as_of_label = format_date(date.today())

render_hero(
    as_of_label,
    int(kpis.get("total_loans", 0)),
    int(kpis.get("customers", 0)),
)
render_kpi_cards(kpis)

if kpis.get("total_loans", 0) == 0:
    st.warning(
        "No loans match the current filter selection. Use **Reset filters** in the sidebar "
        "or widen the disbursement date range."
    )

tabs = st.tabs(["Overview", "Risk & delinquency", "Loan explorer", "Data quality", "Import & export"])

# ---------------------------------------------------------------------------
# Overview
# ---------------------------------------------------------------------------
with tabs[0]:
    section_header(
        "Originations",
        "Monthly disbursements",
        f"{compact_currency(monthly['disbursed_amount'].sum() if not monthly.empty else 0)} "
        f"originated across {len(monthly):,} months",
    )
    origination_col, mix_col = st.columns([1.62, 1], gap="medium")
    with origination_col:
        with st.container(border=True):
            st.plotly_chart(
                monthly_originations_chart(monthly),
                width="stretch",
                config=CHART_CONFIG,
            )
    with mix_col:
        with st.container(border=True):
            st.plotly_chart(portfolio_mix_chart(mix), width="stretch", config=CHART_CONFIG)

    section_header(
        "Delinquency",
        "Overdue trend",
        "Month-end overdue balances and the number of loans past due",
    )
    trend_col, posture_col = st.columns([1.62, 1], gap="medium")
    with trend_col:
        with st.container(border=True):
            st.plotly_chart(
                overdue_trend_chart(overdue_trend),
                width="stretch",
                config=CHART_CONFIG,
            )
    with posture_col:
        render_risk_posture(kpis, top_product_share, top_product)

    section_header(
        "Book composition",
        "Segment scorecard",
        "Outstanding exposure, delinquency and default rate by customer segment",
    )
    scorecard_col, exposure_col = st.columns([1.25, 0.75], gap="medium")
    with scorecard_col:
        with st.container(border=True):
            if segment_performance.empty:
                st.info("No segment data for the selected filters.")
            else:
                segment_display = segment_performance[
                    ["segment", "loan_count", "outstanding_balance", "overdue_rate",
                     "default_rate", "par30_rate", "avg_rate"]
                ].copy()
                segment_display.columns = [
                    "Segment", "Loans", "Outstanding", "Overdue %", "Default %",
                    "PAR 30+", "Avg rate",
                ]
                st.dataframe(
                    segment_display,
                    hide_index=True,
                    width="stretch",
                    height="auto",
                    column_config={
                        "Loans": st.column_config.NumberColumn(format="%,d"),
                        "Outstanding": st.column_config.NumberColumn(format="$%,.0f"),
                        "Overdue %": st.column_config.NumberColumn(format="%.1f%%"),
                        "Default %": st.column_config.NumberColumn(format="%.1f%%"),
                        "PAR 30+": st.column_config.NumberColumn(format="%.1f%%"),
                        "Avg rate": st.column_config.NumberColumn(format="%.2f%%"),
                    },
                )
                riskiest = segment_performance.sort_values("par30_rate", ascending=False).iloc[0]
                highest_default = segment_performance.sort_values("default_rate", ascending=False).iloc[0]
                if riskiest["segment"] == highest_default["segment"]:
                    st.caption(
                        f"{riskiest['segment']} carries the highest PAR 30+ "
                        f"({riskiest['par30_rate']:.1f}%) and default rate "
                        f"({riskiest['default_rate']:.1f}%)."
                    )
                else:
                    st.caption(
                        f"{riskiest['segment']} carries the highest PAR 30+ at "
                        f"{riskiest['par30_rate']:.1f}%; {highest_default['segment']} has the "
                        f"highest default rate at {highest_default['default_rate']:.1f}%."
                    )
    with exposure_col:
        with st.container(border=True):
            if top_exposures.empty:
                st.info("No open exposures for the selected filters.")
            else:
                exposure_display = top_exposures[
                    ["full_name", "segment", "loan_count", "exposure"]
                ].copy()
                exposure_display.columns = ["Borrower", "Segment", "Loans", "Exposure"]
                st.dataframe(
                    exposure_display,
                    hide_index=True,
                    width="stretch",
                    height="auto",
                    column_config={
                        "Segment": st.column_config.TextColumn(width="small"),
                        "Loans": st.column_config.NumberColumn(format="%d", width="small"),
                        "Exposure": st.column_config.NumberColumn(format="$%,.0f"),
                    },
                )

# ---------------------------------------------------------------------------
# Risk & delinquency
# ---------------------------------------------------------------------------
with tabs[1]:
    section_header(
        "Credit risk",
        "Portfolio at risk",
        "Risk metrics are calculated from open loans in the current filter selection",
    )
    render_mini_metrics(
        [
            (
                "PAR 30+",
                f"{kpis.get('par30_rate', 0):.1f}%",
                f"{compact_currency(kpis.get('par30_balance', 0))} past due 30+ days",
            ),
            (
                "90+ DPD exposure",
                compact_currency(kpis.get("par90_balance", 0)),
                f"{kpis.get('par90_rate', 0):.1f}% of the open book",
            ),
            (
                "Weighted average rate",
                f"{kpis.get('weighted_avg_rate', 0):.2f}%",
                "Weighted by outstanding balance",
            ),
        ]
    )

    section_header(
        "Delinquency & credit quality",
        "Risk distribution",
        "Open-loan arrears buckets and balance-weighted default rates by risk grade",
    )
    dpd_col, grade_col = st.columns([1.35, 1], gap="medium")
    with dpd_col:
        with st.container(border=True):
            st.plotly_chart(dpd_distribution_chart(dpd), width="stretch", config=CHART_CONFIG)
    with grade_col:
        with st.container(border=True):
            st.plotly_chart(risk_grade_chart(risk_performance), width="stretch", config=CHART_CONFIG)

    section_header(
        "Vintages",
        "Quarterly origination quality",
        "Default rate by disbursement quarter — a proxy for underwriting quality over time",
    )
    vintage_col, grade_table_col = st.columns([1.35, 1], gap="medium")
    with vintage_col:
        with st.container(border=True):
            st.plotly_chart(vintage_chart(vintage), width="stretch", config=CHART_CONFIG)
    with grade_table_col:
        with st.container(border=True):
            if risk_performance.empty:
                st.info("No risk-grade data for the selected filters.")
            else:
                grade_display = risk_performance[
                    ["risk_grade", "loan_count", "outstanding_balance", "default_rate", "par30_rate"]
                ].copy()
                grade_display.columns = ["Grade", "Loans", "Outstanding", "Default %", "PAR 30+"]
                st.dataframe(
                    grade_display,
                    hide_index=True,
                    width="stretch",
                    height="auto",
                    column_config={
                        "Loans": st.column_config.NumberColumn(format="%,d"),
                        "Outstanding": st.column_config.NumberColumn(format="$%,.0f"),
                        "Default %": st.column_config.NumberColumn(format="%.1f%%"),
                        "PAR 30+": st.column_config.NumberColumn(format="%.1f%%"),
                    },
                )
                worst_grade = risk_performance.sort_values("default_rate", ascending=False).iloc[0]
                st.caption(
                    f"Grade {worst_grade['risk_grade']} has the highest observed default rate "
                    f"at {worst_grade['default_rate']:.1f}%."
                )

    section_header(
        "Segments",
        "Portfolio quality by customer segment",
        "Overdue balance, delinquency and default rate by segment",
    )
    with st.container(border=True):
        if segment_performance.empty:
            st.info("No segment data for the selected filters.")
        else:
            detail = segment_performance[
                ["segment", "customer_count", "loan_count", "outstanding_balance",
                 "overdue_balance", "overdue_loans", "defaulted_loans", "default_rate",
                 "par30_rate", "avg_dpd"]
            ].copy()
            detail.columns = [
                "Segment", "Customers", "Loans", "Outstanding", "Overdue balance",
                "Overdue loans", "Defaults", "Default %", "PAR 30+", "Avg DPD",
            ]
            st.dataframe(
                detail,
                hide_index=True,
                width="stretch",
                height="auto",
                column_config={
                    "Customers": st.column_config.NumberColumn(format="%,d"),
                    "Loans": st.column_config.NumberColumn(format="%,d"),
                    "Outstanding": st.column_config.NumberColumn(format="$%,.0f"),
                    "Overdue balance": st.column_config.NumberColumn(format="$%,.0f"),
                    "Overdue loans": st.column_config.NumberColumn(format="%,d"),
                    "Defaults": st.column_config.NumberColumn(format="%,d"),
                    "Default %": st.column_config.NumberColumn(format="%.1f%%"),
                    "PAR 30+": st.column_config.NumberColumn(format="%.1f%%"),
                    "Avg DPD": st.column_config.NumberColumn(format="%.0f days"),
                },
            )

# ---------------------------------------------------------------------------
# Loan explorer
# ---------------------------------------------------------------------------
with tabs[2]:
    section_header(
        "Loan-level data",
        "Loan explorer",
        "Search and inspect the filtered book, then export exactly what you see",
    )
    search_col, download_col = st.columns([2.2, 1], gap="medium", vertical_alignment="bottom")
    with search_col:
        search = st.text_input(
            "Search loan ID, borrower, product or purpose",
            placeholder="Try LN-00042, Personal, or a borrower name…",
            key="explorer_search",
            label_visibility="collapsed",
        )
    search_scope = loans_table.copy()
    if search.strip() and not search_scope.empty:
        query = search.strip()
        mask = (
            search_scope["loan_id"].astype(str).str.contains(query, case=False, regex=False, na=False)
            | search_scope["customer"].astype(str).str.contains(query, case=False, regex=False, na=False)
            | search_scope["customer_id"].astype(str).str.contains(query, case=False, regex=False, na=False)
            | search_scope["loan_type"].astype(str).str.contains(query, case=False, regex=False, na=False)
            | search_scope["purpose"].astype(str).str.contains(query, case=False, regex=False, na=False)
        )
        search_scope = search_scope[mask]

    displayed_outstanding = (
        search_scope.loc[search_scope["status"] != "Closed", "outstanding_balance"].sum()
        if not search_scope.empty
        else 0
    )
    download_name = f"loan_book_{date.today().isoformat()}.csv"
    with download_col:
        st.download_button(
            "Download search results",
            data=frame_to_csv_bytes(search_scope),
            file_name=download_name,
            mime="text/csv",
            width="stretch",
            key="explorer_download",
        )

    st.markdown(
        f'<div class="metric-inline"><span class="status-dot"></span>'
        f'{len(search_scope):,} loans · {compact_currency(displayed_outstanding)} outstanding'
        f'</div>',
        unsafe_allow_html=True,
    )

    if search_scope.empty:
        st.info("No loans match the current search and filters.")
    else:
        explorer = search_scope.copy()
        explorer["disbursement_date"] = pd.to_datetime(explorer["disbursement_date"]).dt.strftime("%d %b %Y")
        explorer["maturity_date"] = pd.to_datetime(explorer["maturity_date"]).dt.strftime("%d %b %Y")
        explorer = explorer[
            ["loan_id", "customer", "segment", "loan_type", "principal_amount",
             "outstanding_balance", "interest_rate", "term_months", "status",
             "days_past_due", "risk_grade", "disbursement_date", "maturity_date",
             "branch", "purpose"]
        ]
        explorer.columns = [
            "Loan ID", "Borrower", "Segment", "Product", "Principal", "Outstanding",
            "Rate", "Term", "Status", "DPD", "Grade", "Disbursed", "Matures",
            "Branch", "Purpose",
        ]
        st.dataframe(
            explorer,
            hide_index=True,
            width="stretch",
            height=520,
            column_config={
                "Principal": st.column_config.NumberColumn(format="$%,.0f"),
                "Outstanding": st.column_config.NumberColumn(format="$%,.0f"),
                "Rate": st.column_config.NumberColumn(format="%.2f%%"),
                "Term": st.column_config.NumberColumn(format="%d mo"),
                "DPD": st.column_config.NumberColumn(format="%d"),
            },
        )

# ---------------------------------------------------------------------------
# Data quality
# ---------------------------------------------------------------------------
with tabs[3]:
    quality = run_quality_checks(DB_PATH)
    quality_summary = quality["summary"]
    section_header(
        "Governance",
        "Data quality center",
        "Checks run against the complete database, independent of sidebar filters",
    )
    render_mini_metrics(
        [
            (
                "Checks passed",
                f"{quality_summary['passed']}/{quality_summary['checks_run']}",
                f"{quality_summary['score']:.1f}% quality score",
            ),
            (
                "Findings to review",
                f"{quality_summary['review']}",
                f"{quality_summary['critical_issues']:,} critical issues",
            ),
            (
                "Rows scanned",
                f"{quality_summary['rows_scanned']:,}",
                "Customers, loans and monthly snapshots",
            ),
        ]
    )
    if quality_summary["review"] == 0:
        st.success("All integrity, completeness and domain checks passed.")
    else:
        st.warning("Some checks need review. See the findings below for details.")

    section_header(
        "Checks",
        "Validation results",
        "Duplicate keys, missing values, referential integrity and business-rule checks",
    )
    with st.container(border=True):
        checks_display = quality["checks"].copy()
        checks_display = checks_display[["check", "scope", "status", "severity", "issues", "finding"]]
        checks_display.columns = ["Check", "Scope", "Status", "Severity", "Issues", "Finding"]
        st.dataframe(
            checks_display,
            hide_index=True,
            width="stretch",
            height=620,
            column_config={
                "Issues": st.column_config.NumberColumn(format="%,d"),
            },
        )

    section_header(
        "Completeness",
        "Missing-value scan",
        "Critical fields are flagged; optional lifecycle dates can be empty",
    )
    with st.container(border=True):
        missing_display = quality["missing"].copy()
        missing_display = missing_display[
            ["table", "column", "missing", "total", "completeness", "critical"]
        ]
        missing_display.columns = ["Table", "Field", "Missing", "Rows", "Completeness", "Critical"]
        st.dataframe(
            missing_display,
            hide_index=True,
            width="stretch",
            height=340,
            column_config={
                "Missing": st.column_config.NumberColumn(format="%,d"),
                "Rows": st.column_config.NumberColumn(format="%,d"),
                "Completeness": st.column_config.ProgressColumn(
                    format="%.1f%%", min_value=0, max_value=100
                ),
                "Critical": st.column_config.CheckboxColumn(),
            },
        )

# ---------------------------------------------------------------------------
# Import & export
# ---------------------------------------------------------------------------
with tabs[4]:
    section_header(
        "Data operations",
        "Import & export",
        "Bring in new loan records or take the current view away as CSV",
    )

    import_col, export_col = st.columns([1.12, 0.88], gap="large")

    with import_col:
        with st.container(border=True):
            st.markdown("#### Import loans from CSV")
            st.markdown(
                '<div class="import-step">Upload loan-level records to add new loans or update '
                "existing loan IDs. Required fields are <strong>loan_id</strong>, "
                "<strong>customer_id</strong>, <strong>loan_type</strong>, "
                "<strong>principal_amount</strong>, <strong>interest_rate</strong>, "
                "<strong>term_months</strong>, <strong>disbursement_date</strong> and "
                "<strong>status</strong>. Missing optional values receive safe defaults.</div>",
                unsafe_allow_html=True,
            )

            if st.session_state.get("import_summary"):
                result = st.session_state["import_summary"]
                loan_word = "loan record" if result["total"] == 1 else "loan records"
                st.success(
                    f"Imported {result['total']:,} {loan_word} — "
                    f"{result['inserted']:,} new and {result['updated']:,} updated."
                )
                st.caption("The dashboard now reflects the new records in the portfolio.")
                if st.button("Import another file", type="secondary", width="stretch"):
                    st.session_state.pop("import_summary", None)
                    st.rerun()
            else:
                customer_ids = fetch_customer_ids(DB_PATH)
                template_customer = next(iter(customer_ids), "CUST-000001")
                template = build_import_template(template_customer)
                st.download_button(
                    "Download CSV template",
                    data=frame_to_csv_bytes(template),
                    file_name="loan_import_template.csv",
                    mime="text/csv",
                    key="template_download",
                    width="stretch",
                )

                uploaded = st.file_uploader(
                    "Upload loan CSV",
                    type=["csv"],
                    key="loan_csv_upload",
                    help="UTF-8 CSV, maximum 20 MB.",
                    max_upload_size=20,
                )

                if uploaded is not None:
                    try:
                        raw_frame = read_csv_upload(uploaded)
                    except ValueError as error:
                        st.error(str(error))
                    else:
                        validation = validate_upload_against_database(raw_frame, DB_PATH)
                        summary = validation.summary
                        st.markdown(
                            f"**{summary['valid']:,} valid** of {summary['total']:,} rows · "
                            f"{summary['new']:,} new · {summary['updates']:,} updates · "
                            f"{summary['invalid']:,} invalid"
                        )

                        if not validation.issues.empty:
                            st.error(
                                f"{len(validation.issues):,} validation issue(s) found. "
                                "Invalid rows will be skipped."
                            )
                            with st.expander("View validation issues", expanded=False):
                                st.dataframe(
                                    validation.issues,
                                    hide_index=True,
                                    width="stretch",
                                    height=220,
                                )
                        if validation.warnings:
                            with st.expander("Import notes", expanded=False):
                                for warning in validation.warnings[:25]:
                                    st.caption(f"• {warning}")
                                if len(validation.warnings) > 25:
                                    st.caption(f"…and {len(validation.warnings) - 25:,} more notes.")

                        if not validation.cleaned.empty:
                            st.caption("Preview — first five normalized rows")
                            st.dataframe(
                                validation.cleaned.head(5),
                                hide_index=True,
                                width="stretch",
                                height=220,
                            )
                            if st.button(
                                f"Import {summary['valid']:,} validated loan"
                                f"{'s' if summary['valid'] != 1 else ''}",
                                type="primary",
                                width="stretch",
                                key="execute_import",
                            ):
                                try:
                                    result = upsert_loans(validation.cleaned, DB_PATH)
                                except Exception as error:  # pragma: no cover - DB safety
                                    st.error(f"Import failed: {error}")
                                else:
                                    st.session_state["import_summary"] = result
                                    st.rerun()
                        else:
                            st.info("No valid rows are available to import.")

    with export_col:
        with st.container(border=True):
            st.markdown("#### Export current view")
            st.markdown(
                '<div class="import-step">Every export respects the filters in the sidebar. '
                "CSV files open directly in Excel, Google Sheets or a BI tool.</div>",
                unsafe_allow_html=True,
            )
            st.download_button(
                "Loan book · filtered CSV",
                data=frame_to_csv_bytes(loans_table),
                file_name=f"loan_book_{date.today().isoformat()}.csv",
                mime="text/csv",
                key="export_loan_book",
                width="stretch",
            )

            summary_export = pd.DataFrame(
                [
                    ("Total loans", int(kpis.get("total_loans", 0))),
                    ("Borrowers", int(kpis.get("customers", 0))),
                    ("Total principal", round(float(kpis.get("total_principal", 0)), 2)),
                    ("Outstanding balance", round(float(kpis.get("outstanding_balance", 0)), 2)),
                    ("Overdue loans", int(kpis.get("overdue_loans", 0))),
                    ("Overdue balance", round(float(kpis.get("overdue_balance", 0)), 2)),
                    ("Defaulted loans", int(kpis.get("defaulted_loans", 0))),
                    ("Default rate (%)", round(float(kpis.get("default_rate", 0)), 2)),
                    ("Default rate by balance (%)", round(float(kpis.get("default_rate_balance", 0)), 2)),
                    ("PAR 30+ (%)", round(float(kpis.get("par30_rate", 0)), 2)),
                    ("Weighted average rate (%)", round(float(kpis.get("weighted_avg_rate", 0)), 2)),
                ],
                columns=["Metric", "Value"],
            )
            st.download_button(
                "Portfolio summary · CSV",
                data=frame_to_csv_bytes(summary_export),
                file_name=f"portfolio_summary_{date.today().isoformat()}.csv",
                mime="text/csv",
                key="export_summary",
                width="stretch",
            )

            if not monthly.empty:
                monthly_export = monthly.copy()
                monthly_export.columns = [
                    "Month", "Loans originated", "Disbursed amount",
                    "Outstanding balance", "Defaulted loans",
                ]
                st.download_button(
                    "Monthly originations · CSV",
                    data=frame_to_csv_bytes(monthly_export),
                    file_name=f"monthly_originations_{date.today().isoformat()}.csv",
                    mime="text/csv",
                    key="export_monthly",
                    width="stretch",
                )

            if not segment_performance.empty:
                segment_export = segment_performance.copy()
                st.download_button(
                    "Segment scorecard · CSV",
                    data=frame_to_csv_bytes(segment_export),
                    file_name=f"segment_scorecard_{date.today().isoformat()}.csv",
                    mime="text/csv",
                    key="export_segments",
                    width="stretch",
                )

        with st.container(border=True):
            st.markdown("#### Database snapshot")
            st.markdown(
                f'<div class="import-step"><strong>{DATABASE_COUNTS["customers"]:,}</strong> customers<br>'
                f'<strong>{DATABASE_COUNTS["loans"]:,}</strong> loans<br>'
                f'<strong>{DATABASE_COUNTS["portfolio_snapshots"]:,}</strong> month-end snapshots<br>'
                f'<strong>{db_size}</strong> SQLite database</div>',
                unsafe_allow_html=True,
            )
            st.caption(f"Database file: `{DB_PATH}`")
            st.caption("Rebuild the demo data any time with `python init_db.py --reset`.")

render_app_footer()
