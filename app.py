"""Northstar — loan portfolio analytics dashboard.

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
    risk_grade_chart,
    vintage_chart,
)
from loan_dashboard.config import (
    APP_TITLE,
    CHART_CONFIG,
    COLORS,
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
    card_header,
    compact_currency,
    format_date,
    inject_css,
    render_app_footer,
    render_brand,
    render_completeness,
    render_exposure_list,
    render_metric_strip,
    render_page_header,
    render_product_allocation,
    render_quality_checks,
    render_risk_panel,
    render_segment_risk_table,
    render_segment_table,
    render_sidebar_footer,
)

st.set_page_config(
    page_title=APP_TITLE,
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="auto",
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
    options = get_filter_options(DB_PATH)
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

    heading_col, reset_col = st.columns([1.7, 1], vertical_alignment="center")
    with heading_col:
        st.markdown(
            '<div class="side-heading"><span>Filters</span></div>',
            unsafe_allow_html=True,
        )
    with reset_col:
        st.button(
            "Reset",
            on_click=reset_filters,
            type="tertiary",
            key="sidebar_reset",
        )

    date_range = st.date_input(
        "Disbursement period",
        value=(options["min_date"], options["max_date"]),
        min_value=options["min_date"],
        max_value=options["max_date"],
        key="filter_dates",
        format="DD/MM/YYYY",
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
        placeholder="All loan types",
    )
    selected_statuses = st.multiselect(
        "Status",
        options=available_statuses,
        default=[],
        key="filter_statuses",
        placeholder="All statuses",
    )
    selected_segments = st.multiselect(
        "Customer segment",
        options=available_segments,
        default=[],
        key="filter_segments",
        placeholder="All segments",
    )

    active_filters = 0
    active_filters += int(start_date != options["min_date"] or end_date != options["max_date"])
    active_filters += int(bool(selected_types))
    active_filters += int(bool(selected_statuses))
    active_filters += int(bool(selected_segments))

    if active_filters:
        st.markdown(
            '<div class="data-note">Selections apply to every view.</div>',
            unsafe_allow_html=True,
        )

    db_size = f"{DB_PATH.stat().st_size / 1_000_000:.1f} MB" if DB_PATH.exists() else ""
    render_sidebar_footer(
        DATABASE_COUNTS.get("loans", 0),
        DATABASE_COUNTS.get("customers", 0),
        db_size,
        options["min_date"],
        options["max_date"],
    )

filters = PortfolioFilters(
    start_date=start_date,
    end_date=end_date,
    loan_types=tuple(selected_types),
    statuses=tuple(selected_statuses),
    segments=tuple(selected_segments),
)

# ---------------------------------------------------------------------------
# Data access
# ---------------------------------------------------------------------------
kpis = get_kpis(filters, DB_PATH)
monthly = get_monthly_originations(filters, DB_PATH)
mix = get_portfolio_mix(filters, DB_PATH)
overdue_trend = get_overdue_trend(filters, DB_PATH)
dpd = get_dpd_buckets(filters, DB_PATH)
segment_performance = get_segment_performance(filters, DB_PATH)
risk_performance = get_risk_grade_performance(filters, DB_PATH)
vintage = get_quarterly_vintage(filters, DB_PATH)
if not vintage.empty:
    current_quarter = f"{date.today().year}-Q{(date.today().month - 1) // 3 + 1}"
    vintage = vintage[vintage["vintage"] != current_quarter]
top_exposures = get_top_exposures(filters, limit=6, db_path=DB_PATH)
loans_table = get_loans_table(filters, DB_PATH)

as_of_label = format_date(date.today())
export_name = f"northstar_loan_book_{date.today().isoformat()}.csv"

header_col, action_col = st.columns([5.1, 1.1], gap="large", vertical_alignment="center")
with header_col:
    render_page_header(
        as_of_label,
        int(kpis.get("total_loans", 0)),
        int(kpis.get("customers", 0)),
        active_filters,
    )
with action_col:
    with st.container(key="header_action_box"):
        st.download_button(
            "Export",
            data=frame_to_csv_bytes(loans_table),
            file_name=export_name,
            mime="text/csv",
            key="header_export",
            width="content",
        )

if kpis.get("total_loans", 0) == 0:
    st.warning(
        "No loans match the current selection. Clear filters or widen the disbursement period."
    )

tabs = st.tabs(
    ["Overview", "Risk & delinquency", "Loan explorer", "Data quality", "Import & export"]
)

# ---------------------------------------------------------------------------
# Overview
# ---------------------------------------------------------------------------
with tabs[0]:
    render_metric_strip(
        [
            {
                "label": "Total loans",
                "value": f"{int(kpis.get('total_loans', 0)):,}",
                "detail": (
                    f"{int(kpis.get('customers', 0)):,} borrowers · "
                    f"{kpis.get('active_share', 0):.0f}% active"
                ),
                "color": COLORS["primary"],
            },
            {
                "label": "Outstanding balance",
                "value": compact_currency(kpis.get("outstanding_balance", 0)),
                "detail": f"{kpis.get('outstanding_ratio', 0):.1f}% of originated capital",
                "color": COLORS["info"],
            },
            {
                "label": "Overdue loans",
                "value": f"{int(kpis.get('overdue_loans', 0)):,}",
                "detail": (
                    f"{compact_currency(kpis.get('overdue_balance', 0))} overdue · "
                    f"{kpis.get('overdue_rate', 0):.1f}% of book"
                ),
                "color": COLORS["amber"],
            },
            {
                "label": "Default rate",
                "value": f"{kpis.get('default_rate', 0):.1f}%",
                "detail": (
                    f"{int(kpis.get('defaulted_loans', 0)):,} defaults · "
                    f"{kpis.get('default_rate_balance', 0):.1f}% by balance"
                ),
                "color": COLORS["red"],
            },
        ]
    )

    origination_col, allocation_col = st.columns([2.02, 1], gap="medium")
    with origination_col:
        with st.container(border=True, key="card_origination"):
            card_header(
                "Origination activity",
                "Monthly disbursed principal",
                compact_currency(monthly["disbursed_amount"].sum()) if not monthly.empty else "$0",
                "total",
            )
            st.plotly_chart(
                monthly_originations_chart(monthly),
                width="stretch",
                config=CHART_CONFIG,
            )
    with allocation_col:
        render_product_allocation(mix)

    trend_col, risk_col = st.columns([2.02, 1], gap="medium")
    with trend_col:
        with st.container(border=True, key="card_trend"):
            latest_overdue = (
                compact_currency(overdue_trend.iloc[-1]["overdue_balance"])
                if not overdue_trend.empty
                else "$0"
            )
            latest_snapshot = (
                format_date(overdue_trend.iloc[-1]["snapshot_date"])
                if not overdue_trend.empty
                else "No snapshot"
            )
            card_header(
                "Delinquency trend",
                "Overdue balance at each month-end",
                latest_overdue,
                latest_snapshot,
            )
            st.plotly_chart(
                overdue_trend_chart(overdue_trend),
                width="stretch",
                config=CHART_CONFIG,
            )
    with risk_col:
        render_risk_panel(kpis, dpd)

    segment_col, exposure_col = st.columns([1.55, 1], gap="medium")
    with segment_col:
        render_segment_table(segment_performance)
    with exposure_col:
        render_exposure_list(top_exposures, float(kpis.get("outstanding_balance", 0)))

# ---------------------------------------------------------------------------
# Risk & delinquency
# ---------------------------------------------------------------------------
with tabs[1]:
    render_metric_strip(
        [
            {
                "label": "PAR 30+",
                "value": f"{kpis.get('par30_rate', 0):.1f}%",
                "detail": f"{compact_currency(kpis.get('par30_balance', 0))} past due 30+ days",
                "color": COLORS["amber"],
            },
            {
                "label": "90+ DPD balance",
                "value": compact_currency(kpis.get("par90_balance", 0)),
                "detail": f"{kpis.get('par90_rate', 0):.1f}% of open book",
                "color": COLORS["red"],
            },
            {
                "label": "Weighted average rate",
                "value": f"{kpis.get('weighted_avg_rate', 0):.2f}%",
                "detail": "Weighted by open balance",
                "color": COLORS["primary"],
            },
            {
                "label": "Average DPD",
                "value": f"{kpis.get('avg_dpd', 0):.0f} days",
                "detail": "Across non-closed loans",
                "color": COLORS["subtle"],
            },
        ]
    )

    dpd_col, grade_col = st.columns([1.02, 0.98], gap="medium")
    with dpd_col:
        with st.container(border=True, key="card_dpd"):
            open_loans = int((dpd["loan_count"].sum()) if not dpd.empty else 0)
            card_header(
                "Delinquency distribution",
                "Open loans by days-past-due bucket",
                f"{open_loans:,}",
                "open loans",
            )
            st.plotly_chart(
                dpd_distribution_chart(dpd),
                width="stretch",
                config=CHART_CONFIG,
            )
    with grade_col:
        with st.container(border=True, key="card_grade"):
            card_header(
                "Default by risk grade",
                "Balance-weighted default rate",
                f"{kpis.get('default_rate_balance', 0):.1f}%",
                "book default",
            )
            st.plotly_chart(
                risk_grade_chart(risk_performance),
                width="stretch",
                config=CHART_CONFIG,
            )

    vintage_col, segment_risk_col = st.columns([1.35, 1], gap="medium")
    with vintage_col:
        with st.container(border=True, key="card_vintage"):
            card_header(
                "Vintage performance",
                "Default rate by completed disbursement quarter",
                f"{len(vintage):,}",
                "quarters",
            )
            st.plotly_chart(
                vintage_chart(vintage),
                width="stretch",
                config=CHART_CONFIG,
            )
    with segment_risk_col:
        render_segment_risk_table(segment_performance)

# ---------------------------------------------------------------------------
# Loan explorer
# ---------------------------------------------------------------------------
with tabs[2]:
    search_col, download_col = st.columns([2.25, 1], gap="medium", vertical_alignment="bottom")
    with search_col:
        search = st.text_input(
            "Search loans",
            placeholder="Search loan ID, borrower, product or purpose…",
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
    with download_col:
        st.download_button(
            "Export search",
            data=frame_to_csv_bytes(search_scope),
            file_name=f"northstar_search_{date.today().isoformat()}.csv",
            mime="text/csv",
            key="explorer_download",
            width="stretch",
        )

    st.markdown(
        '<div class="section-note" style="margin:0.2rem 0 0.55rem;">'
        f'<strong style="color:#4C524D;">{len(search_scope):,}</strong> loans · '
        f'<strong style="color:#4C524D;">{compact_currency(displayed_outstanding)}</strong> outstanding'
        '</div>',
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
             "outstanding_balance", "interest_rate", "status", "days_past_due",
             "risk_grade", "disbursement_date"]
        ]
        explorer.columns = [
            "Loan ID", "Borrower", "Segment", "Product", "Principal", "Outstanding",
            "Rate", "Status", "DPD", "Grade", "Disbursed",
        ]
        with st.container(border=True, key="card_loans"):
            card_header(
                "Loan book",
                "A searchable record of the selected portfolio",
                f"{len(explorer):,}",
                "results",
            )
            st.dataframe(
                explorer,
                hide_index=True,
                width="stretch",
                height=524,
                column_config={
                    "Principal": st.column_config.NumberColumn(format="$%,.0f"),
                    "Outstanding": st.column_config.NumberColumn(format="$%,.0f"),
                    "Rate": st.column_config.NumberColumn(format="%.2f%%"),
                    "DPD": st.column_config.NumberColumn(format="%d"),
                    "Loan ID": st.column_config.TextColumn(width="small"),
                    "Borrower": st.column_config.TextColumn(width="medium"),
                    "Grade": st.column_config.TextColumn(width="small"),
                },
            )

# ---------------------------------------------------------------------------
# Data quality
# ---------------------------------------------------------------------------
with tabs[3]:
    quality = run_quality_checks(DB_PATH)
    quality_summary = quality["summary"]
    render_metric_strip(
        [
            {
                "label": "Validation checks",
                "value": f"{quality_summary['passed']}/{quality_summary['checks_run']}",
                "detail": f"{quality_summary['score']:.1f}% quality score",
                "color": COLORS["primary"],
            },
            {
                "label": "Critical issues",
                "value": f"{quality_summary['critical_issues']:,}",
                "detail": "No blocking findings" if quality_summary["critical_issues"] == 0 else "Requires review",
                "color": COLORS["red"],
            },
            {
                "label": "Rows audited",
                "value": f"{quality_summary['rows_scanned']:,}",
                "detail": "Customers, loans and month-end snapshots",
                "color": COLORS["info"],
            },
        ],
        columns=3,
    )

    if quality_summary["review"] == 0:
        st.markdown(
            '<div class="quality-summary"><span class="check-dot"></span>'
            'All integrity, completeness and domain checks passed.</div>',
            unsafe_allow_html=True,
        )
    else:
        st.warning(
            f"{quality_summary['review']} control(s) require review. Findings are shown in the "
            "validation controls below."
        )

    render_quality_checks(quality["checks"])
    render_completeness(quality["missing"])

    with st.expander("View field-level completeness", expanded=False):
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
    import_col, export_col = st.columns([1.06, 0.94], gap="large")

    with import_col:
        with st.container(border=True, key="ops_import"):
            card_header(
                "Import loan records",
                "Add new loans or update existing loan IDs",
                "CSV",
                "format",
            )
            st.markdown(
                '<div class="ops-intro">Upload loan-level records to add new loans or update '
                'existing loan IDs. Each valid row is written in a single transaction.</div>',
                unsafe_allow_html=True,
            )
            st.markdown(
                '<div class="required-fields">REQUIRED · loan_id, customer_id, loan_type, '
                'principal_amount, interest_rate, term_months, disbursement_date, status</div>',
                unsafe_allow_html=True,
            )

            if st.session_state.get("import_summary"):
                result = st.session_state["import_summary"]
                record_word = "record" if result["total"] == 1 else "records"
                st.success(
                    f"Imported {result['total']:,} loan {record_word} — "
                    f"{result['inserted']:,} new and {result['updated']:,} updated."
                )
                st.caption("Portfolio totals and charts now reflect the imported records.")
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
                                    st.caption(
                                        f"…and {len(validation.warnings) - 25:,} more notes."
                                    )

                        if not validation.cleaned.empty:
                            st.caption("Preview · first five normalized rows")
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
        with st.container(border=True, key="ops_export"):
            card_header(
                "Export current view",
                "Every file respects the sidebar filters",
                "CSV",
                "format",
            )
            st.markdown(
                '<div class="ops-intro">Files are UTF-8 CSV and open directly in Excel, '
                'Google Sheets or a BI tool.</div>',
                unsafe_allow_html=True,
            )
            st.download_button(
                "Loan book · filtered CSV",
                data=frame_to_csv_bytes(loans_table),
                file_name=f"northstar_loan_book_{date.today().isoformat()}.csv",
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
                file_name=f"northstar_summary_{date.today().isoformat()}.csv",
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
                    file_name=f"northstar_originations_{date.today().isoformat()}.csv",
                    mime="text/csv",
                    key="export_monthly",
                    width="stretch",
                )

            if not segment_performance.empty:
                st.download_button(
                    "Segment performance · CSV",
                    data=frame_to_csv_bytes(segment_performance),
                    file_name=f"northstar_segments_{date.today().isoformat()}.csv",
                    mime="text/csv",
                    key="export_segments",
                    width="stretch",
                )

            st.markdown(
                '<div class="data-note">Exports capture the current filter selection, '
                'not the complete database.</div>',
                unsafe_allow_html=True,
            )

    st.markdown(
        '<div class="workspace-strip">'
        '<div><div class="ws-label">Workspace database</div>'
        f'<div class="ws-value">Local SQLite · {db_size}</div>'
        f'<div class="ws-path">{DB_PATH}</div></div>'
        f'<div><div class="ws-label">Loans</div><div class="ws-value">{DATABASE_COUNTS["loans"]:,}</div></div>'
        f'<div><div class="ws-label">Customers</div><div class="ws-value">{DATABASE_COUNTS["customers"]:,}</div></div>'
        f'<div><div class="ws-label">Month-end snapshots</div><div class="ws-value">{DATABASE_COUNTS["portfolio_snapshots"]:,}</div></div>'
        '</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="data-note">Rebuild the demonstration data with '
        '<span style="font-family:SFMono-Regular,Menlo,monospace;">python init_db.py --reset</span>.'
        '</div>',
        unsafe_allow_html=True,
    )

render_app_footer()
