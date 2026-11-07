"""SQL-backed analytics queries used by the dashboard.

All filtering happens in SQLite through parameterized queries.  SQL strings
contain no user input; only allow-listed filter values are passed as bound
parameters.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path

import pandas as pd

from .config import DB_PATH
from .database import read_dataframe


@dataclass(frozen=True)
class PortfolioFilters:
    """Immutable filter state shared by every dashboard query."""

    start_date: date | None = None
    end_date: date | None = None
    loan_types: tuple[str, ...] = ()
    statuses: tuple[str, ...] = ()
    segments: tuple[str, ...] = ()


def _where_clause(filters: PortfolioFilters) -> tuple[str, list[str]]:
    conditions: list[str] = ["1 = 1"]
    params: list[str] = []

    if filters.start_date:
        conditions.append("d.disbursement_date >= ?")
        params.append(filters.start_date.isoformat())
    if filters.end_date:
        conditions.append("d.disbursement_date <= ?")
        params.append(filters.end_date.isoformat())
    if filters.loan_types:
        placeholders = ", ".join("?" for _ in filters.loan_types)
        conditions.append(f"d.loan_type IN ({placeholders})")
        params.extend(filters.loan_types)
    if filters.statuses:
        placeholders = ", ".join("?" for _ in filters.statuses)
        conditions.append(f"d.status IN ({placeholders})")
        params.extend(filters.statuses)
    if filters.segments:
        placeholders = ", ".join("?" for _ in filters.segments)
        conditions.append(f"d.segment IN ({placeholders})")
        params.extend(filters.segments)

    return " AND ".join(conditions), params


def get_filter_options(db_path: Path | str = DB_PATH) -> dict:
    """Return filter domains and record counts for the sidebar."""
    from contextlib import closing

    from .database import get_connection

    with closing(get_connection(db_path)) as connection:
        date_bounds = connection.execute(
            "SELECT MIN(disbursement_date), MAX(disbursement_date) FROM loans"
        ).fetchone()
        type_rows = connection.execute(
            "SELECT loan_type, COUNT(*) FROM loans GROUP BY loan_type ORDER BY loan_type"
        ).fetchall()
        status_rows = connection.execute(
            "SELECT status, COUNT(*) FROM loans GROUP BY status ORDER BY status"
        ).fetchall()
        segment_rows = connection.execute(
            "SELECT segment, COUNT(*) FROM customers GROUP BY segment ORDER BY segment"
        ).fetchall()

    return {
        "min_date": date.fromisoformat(date_bounds[0]) if date_bounds and date_bounds[0] else date.today(),
        "max_date": date.fromisoformat(date_bounds[1]) if date_bounds and date_bounds[1] else date.today(),
        "loan_types": [(row[0], row[1]) for row in type_rows],
        "statuses": [(row[0], row[1]) for row in status_rows],
        "segments": [(row[0], row[1]) for row in segment_rows],
    }


def get_kpis(filters: PortfolioFilters, db_path: Path | str = DB_PATH) -> dict:
    where_sql, params = _where_clause(filters)
    query = f"""
        SELECT
            COUNT(*) AS total_loans,
            COUNT(DISTINCT d.customer_id) AS customers,
            COALESCE(SUM(d.principal_amount), 0) AS total_principal,
            COALESCE(SUM(CASE WHEN d.status != 'Closed' THEN d.outstanding_balance ELSE 0 END), 0)
                AS outstanding_balance,
            COALESCE(SUM(CASE WHEN d.status = 'Active' THEN 1 ELSE 0 END), 0) AS active_loans,
            COALESCE(SUM(CASE WHEN d.status = 'Closed' THEN 1 ELSE 0 END), 0) AS closed_loans,
            COALESCE(SUM(CASE WHEN d.status = 'Defaulted' THEN 1 ELSE 0 END), 0) AS defaulted_loans,
            COALESCE(SUM(CASE WHEN d.status != 'Closed' AND d.days_past_due > 0 THEN 1 ELSE 0 END), 0)
                AS overdue_loans,
            COALESCE(SUM(CASE WHEN d.status != 'Closed' AND d.days_past_due > 0
                              THEN d.outstanding_balance ELSE 0 END), 0) AS overdue_balance,
            COALESCE(SUM(CASE WHEN d.status != 'Closed' AND d.days_past_due >= 30
                              THEN d.outstanding_balance ELSE 0 END), 0) AS par30_balance,
            COALESCE(SUM(CASE WHEN d.status != 'Closed' AND d.days_past_due >= 60
                              THEN d.outstanding_balance ELSE 0 END), 0) AS par60_balance,
            COALESCE(SUM(CASE WHEN d.status != 'Closed' AND d.days_past_due >= 90
                              THEN d.outstanding_balance ELSE 0 END), 0) AS par90_balance,
            COALESCE(SUM(CASE WHEN d.status = 'Defaulted' THEN d.principal_amount ELSE 0 END), 0)
                AS defaulted_principal,
            COALESCE(SUM(CASE WHEN d.status = 'Defaulted' THEN d.outstanding_balance ELSE 0 END), 0)
                AS defaulted_balance,
            CASE WHEN SUM(CASE WHEN d.status != 'Closed' THEN d.outstanding_balance ELSE 0 END) > 0
                 THEN SUM(CASE WHEN d.status != 'Closed'
                               THEN d.outstanding_balance * d.interest_rate ELSE 0 END)
                      / SUM(CASE WHEN d.status != 'Closed' THEN d.outstanding_balance ELSE 0 END)
                 ELSE 0 END AS weighted_avg_rate,
            COALESCE(AVG(CASE WHEN d.status != 'Closed' THEN d.days_past_due END), 0) AS avg_dpd
        FROM loan_details AS d
        WHERE {where_sql}
    """
    frame = read_dataframe(query, params, db_path)
    if frame.empty:
        return {}
    row = {key: (0 if value is None else value) for key, value in frame.iloc[0].to_dict().items()}

    total_loans = float(row["total_loans"] or 0)
    total_principal = float(row["total_principal"] or 0)
    outstanding = float(row["outstanding_balance"] or 0)
    overdue_balance = float(row["overdue_balance"] or 0)

    row["default_rate"] = 100 * float(row["defaulted_loans"]) / total_loans if total_loans else 0.0
    row["default_rate_balance"] = (
        100 * float(row["defaulted_principal"]) / total_principal if total_principal else 0.0
    )
    row["overdue_rate"] = 100 * overdue_balance / outstanding if outstanding else 0.0
    row["par30_rate"] = 100 * float(row["par30_balance"]) / outstanding if outstanding else 0.0
    row["par60_rate"] = 100 * float(row["par60_balance"]) / outstanding if outstanding else 0.0
    row["par90_rate"] = 100 * float(row["par90_balance"]) / outstanding if outstanding else 0.0
    row["active_share"] = 100 * float(row["active_loans"]) / total_loans if total_loans else 0.0
    row["outstanding_ratio"] = 100 * outstanding / total_principal if total_principal else 0.0
    return row


def get_monthly_originations(
    filters: PortfolioFilters, db_path: Path | str = DB_PATH
) -> pd.DataFrame:
    where_sql, params = _where_clause(filters)
    query = f"""
        SELECT
            strftime('%Y-%m-01', d.disbursement_date) AS month,
            COUNT(*) AS loan_count,
            SUM(d.principal_amount) AS disbursed_amount,
            SUM(CASE WHEN d.status != 'Closed' THEN d.outstanding_balance ELSE 0 END)
                AS outstanding_balance,
            SUM(CASE WHEN d.status = 'Defaulted' THEN 1 ELSE 0 END) AS defaulted_loans
        FROM loan_details AS d
        WHERE {where_sql}
        GROUP BY strftime('%Y-%m-01', d.disbursement_date)
        ORDER BY month
    """
    return read_dataframe(query, params, db_path)


def get_portfolio_mix(
    filters: PortfolioFilters, db_path: Path | str = DB_PATH
) -> pd.DataFrame:
    where_sql, params = _where_clause(filters)
    query = f"""
        SELECT
            d.loan_type,
            COUNT(*) AS loan_count,
            SUM(d.principal_amount) AS principal,
            SUM(CASE WHEN d.status != 'Closed' THEN d.outstanding_balance ELSE 0 END)
                AS outstanding_balance,
            SUM(CASE WHEN d.status = 'Defaulted' THEN 1 ELSE 0 END) AS defaulted_loans,
            AVG(d.interest_rate) AS avg_rate
        FROM loan_details AS d
        WHERE {where_sql}
        GROUP BY d.loan_type
        ORDER BY outstanding_balance DESC
    """
    frame = read_dataframe(query, params, db_path)
    if not frame.empty:
        total = frame["outstanding_balance"].sum()
        frame["share"] = (100 * frame["outstanding_balance"] / total).round(2) if total else 0.0
    return frame


def get_status_mix(
    filters: PortfolioFilters, db_path: Path | str = DB_PATH
) -> pd.DataFrame:
    where_sql, params = _where_clause(filters)
    query = f"""
        SELECT
            d.status,
            COUNT(*) AS loan_count,
            SUM(d.principal_amount) AS principal,
            SUM(CASE WHEN d.status != 'Closed' THEN d.outstanding_balance ELSE 0 END)
                AS outstanding_balance
        FROM loan_details AS d
        WHERE {where_sql}
        GROUP BY d.status
        ORDER BY CASE d.status WHEN 'Active' THEN 1 WHEN 'Defaulted' THEN 2 ELSE 3 END
    """
    return read_dataframe(query, params, db_path)


def get_overdue_trend(
    filters: PortfolioFilters, db_path: Path | str = DB_PATH
) -> pd.DataFrame:
    where_sql, params = _where_clause(filters)
    query = f"""
        SELECT
            s.snapshot_date,
            SUM(s.outstanding_balance) AS total_balance,
            SUM(CASE WHEN s.days_past_due > 0 THEN s.outstanding_balance ELSE 0 END)
                AS overdue_balance,
            SUM(CASE WHEN s.days_past_due >= 30 THEN s.outstanding_balance ELSE 0 END)
                AS par30_balance,
            SUM(CASE WHEN s.days_past_due > 0 THEN 1 ELSE 0 END) AS overdue_loans,
            COUNT(*) AS loan_count
        FROM portfolio_snapshots AS s
        JOIN loan_details AS d ON d.loan_id = s.loan_id
        WHERE {where_sql}
        GROUP BY s.snapshot_date
        ORDER BY s.snapshot_date
    """
    return read_dataframe(query, params, db_path)


def get_dpd_buckets(
    filters: PortfolioFilters, db_path: Path | str = DB_PATH
) -> pd.DataFrame:
    where_sql, params = _where_clause(filters)
    query = f"""
        SELECT
            bucket,
            COUNT(*) AS loan_count,
            SUM(outstanding_balance) AS outstanding_balance,
            SUM(principal_amount) AS principal
        FROM (
            SELECT
                d.principal_amount,
                d.outstanding_balance,
                CASE
                    WHEN d.days_past_due = 0 THEN 'Current'
                    WHEN d.days_past_due <= 29 THEN '1–29 days'
                    WHEN d.days_past_due <= 59 THEN '30–59 days'
                    WHEN d.days_past_due <= 89 THEN '60–89 days'
                    ELSE '90+ days'
                END AS bucket,
                CASE
                    WHEN d.days_past_due = 0 THEN 1
                    WHEN d.days_past_due <= 29 THEN 2
                    WHEN d.days_past_due <= 59 THEN 3
                    WHEN d.days_past_due <= 89 THEN 4
                    ELSE 5
                END AS bucket_order
            FROM loan_details AS d
            WHERE {where_sql} AND d.status != 'Closed'
        )
        GROUP BY bucket, bucket_order
        ORDER BY bucket_order
    """
    return read_dataframe(query, params, db_path)


def get_segment_performance(
    filters: PortfolioFilters, db_path: Path | str = DB_PATH
) -> pd.DataFrame:
    where_sql, params = _where_clause(filters)
    query = f"""
        SELECT
            d.segment,
            COUNT(*) AS loan_count,
            COUNT(DISTINCT d.customer_id) AS customer_count,
            SUM(CASE WHEN d.status != 'Closed' THEN d.outstanding_balance ELSE 0 END)
                AS outstanding_balance,
            SUM(CASE WHEN d.status != 'Closed' AND d.days_past_due > 0
                     THEN d.outstanding_balance ELSE 0 END) AS overdue_balance,
            SUM(CASE WHEN d.status != 'Closed' AND d.days_past_due > 0 THEN 1 ELSE 0 END)
                AS overdue_loans,
            SUM(CASE WHEN d.status = 'Defaulted' THEN 1 ELSE 0 END) AS defaulted_loans,
            SUM(CASE WHEN d.status = 'Defaulted' THEN d.principal_amount ELSE 0 END)
                AS defaulted_principal,
            SUM(d.principal_amount) AS total_principal,
            SUM(CASE WHEN d.status != 'Closed' AND d.days_past_due >= 30
                     THEN d.outstanding_balance ELSE 0 END) AS par30_balance,
            AVG(CASE WHEN d.status != 'Closed' THEN d.interest_rate END) AS avg_rate,
            AVG(CASE WHEN d.status != 'Closed' THEN d.days_past_due END) AS avg_dpd
        FROM loan_details AS d
        WHERE {where_sql}
        GROUP BY d.segment
        ORDER BY outstanding_balance DESC
    """
    frame = read_dataframe(query, params, db_path)
    if not frame.empty:
        frame["default_rate"] = (
            100 * frame["defaulted_principal"] / frame["total_principal"].replace(0, pd.NA)
        ).fillna(0).round(2)
        frame["par30_rate"] = (
            100 * frame["par30_balance"] / frame["outstanding_balance"].replace(0, pd.NA)
        ).fillna(0).round(2)
        frame["overdue_rate"] = (
            100 * frame["overdue_balance"] / frame["outstanding_balance"].replace(0, pd.NA)
        ).fillna(0).round(2)
    return frame


def get_risk_grade_performance(
    filters: PortfolioFilters, db_path: Path | str = DB_PATH
) -> pd.DataFrame:
    where_sql, params = _where_clause(filters)
    query = f"""
        SELECT
            d.risk_grade,
            COUNT(*) AS loan_count,
            SUM(CASE WHEN d.status != 'Closed' THEN d.outstanding_balance ELSE 0 END)
                AS outstanding_balance,
            SUM(CASE WHEN d.status = 'Defaulted' THEN 1 ELSE 0 END) AS defaulted_loans,
            SUM(CASE WHEN d.status = 'Defaulted' THEN d.principal_amount ELSE 0 END)
                AS defaulted_principal,
            SUM(d.principal_amount) AS total_principal,
            SUM(CASE WHEN d.status != 'Closed' AND d.days_past_due >= 30
                     THEN d.outstanding_balance ELSE 0 END) AS par30_balance,
            AVG(CASE WHEN d.status != 'Closed' THEN d.days_past_due END) AS avg_dpd
        FROM loan_details AS d
        WHERE {where_sql}
        GROUP BY d.risk_grade
        ORDER BY d.risk_grade
    """
    frame = read_dataframe(query, params, db_path)
    if not frame.empty:
        frame["default_rate"] = (
            100 * frame["defaulted_principal"] / frame["total_principal"].replace(0, pd.NA)
        ).fillna(0).round(2)
        frame["par30_rate"] = (
            100 * frame["par30_balance"] / frame["outstanding_balance"].replace(0, pd.NA)
        ).fillna(0).round(2)
    return frame


def get_quarterly_vintage(
    filters: PortfolioFilters, db_path: Path | str = DB_PATH
) -> pd.DataFrame:
    where_sql, params = _where_clause(filters)
    query = f"""
        SELECT
            printf('%s-Q%d', strftime('%Y', d.disbursement_date),
                   (CAST(strftime('%m', d.disbursement_date) AS INTEGER) + 2) / 3) AS vintage,
            MIN(d.disbursement_date) AS first_disbursement,
            COUNT(*) AS loan_count,
            SUM(d.principal_amount) AS principal,
            SUM(CASE WHEN d.status = 'Defaulted' THEN 1 ELSE 0 END) AS defaulted_loans,
            SUM(CASE WHEN d.status = 'Defaulted' THEN d.principal_amount ELSE 0 END)
                AS defaulted_principal
        FROM loan_details AS d
        WHERE {where_sql}
        GROUP BY vintage
        ORDER BY vintage
    """
    frame = read_dataframe(query, params, db_path)
    if not frame.empty:
        frame["default_rate"] = (
            100 * frame["defaulted_principal"] / frame["principal"].replace(0, pd.NA)
        ).fillna(0).round(2)
    return frame


def get_top_exposures(
    filters: PortfolioFilters,
    limit: int = 8,
    db_path: Path | str = DB_PATH,
) -> pd.DataFrame:
    where_sql, params = _where_clause(filters)
    params = [*params, int(limit)]
    query = f"""
        SELECT
            d.customer_id,
            d.full_name,
            d.segment,
            d.relationship_manager,
            COUNT(*) AS loan_count,
            SUM(CASE WHEN d.status != 'Closed' THEN d.outstanding_balance ELSE 0 END)
                AS exposure,
            MAX(d.days_past_due) AS max_dpd,
            SUM(CASE WHEN d.status = 'Defaulted' THEN 1 ELSE 0 END) AS defaulted_loans
        FROM loan_details AS d
        WHERE {where_sql}
        GROUP BY d.customer_id, d.full_name, d.segment, d.relationship_manager
        HAVING exposure > 0
        ORDER BY exposure DESC
        LIMIT ?
    """
    return read_dataframe(query, params, db_path)


def get_loans_table(
    filters: PortfolioFilters, db_path: Path | str = DB_PATH
) -> pd.DataFrame:
    where_sql, params = _where_clause(filters)
    query = f"""
        SELECT
            d.loan_id,
            d.full_name AS customer,
            d.customer_id,
            d.segment,
            d.loan_type,
            d.principal_amount,
            d.outstanding_balance,
            d.interest_rate,
            d.term_months,
            d.monthly_payment,
            d.disbursement_date,
            d.maturity_date,
            d.status,
            d.days_past_due,
            d.risk_grade,
            d.purpose,
            d.branch,
            d.collateral_type,
            d.credit_score,
            d.relationship_manager
        FROM loan_details AS d
        WHERE {where_sql}
        ORDER BY d.outstanding_balance DESC, d.disbursement_date DESC
    """
    return read_dataframe(query, params, db_path)


def get_snapshot_dates(db_path: Path | str = DB_PATH) -> tuple[str | None, str | None]:
    frame = read_dataframe(
        "SELECT MIN(snapshot_date) AS first_date, MAX(snapshot_date) AS last_date "
        "FROM portfolio_snapshots",
        db_path=db_path,
    )
    if frame.empty:
        return None, None
    return frame.iloc[0]["first_date"], frame.iloc[0]["last_date"]
