"""Data-quality checks for the SQLite portfolio database."""

from __future__ import annotations

from contextlib import closing
from datetime import date
from pathlib import Path

import pandas as pd

from .config import DB_PATH
from .database import get_connection

CRITICAL_COLUMNS = {
    "customers": [
        "customer_id", "full_name", "segment", "credit_score",
        "annual_income", "customer_since",
    ],
    "loans": [
        "loan_id", "customer_id", "loan_type", "principal_amount",
        "outstanding_balance", "interest_rate", "term_months",
        "disbursement_date", "maturity_date", "status", "days_past_due",
        "risk_grade",
    ],
    "portfolio_snapshots": [
        "snapshot_date", "loan_id", "outstanding_balance", "days_past_due", "status",
    ],
}


def _scalar(connection, sql: str, params: tuple = ()) -> int:
    value = connection.execute(sql, params).fetchone()[0]
    return int(value or 0)


def run_quality_checks(db_path: Path | str = DB_PATH) -> dict:
    """Run duplicate, completeness, referential-integrity and domain checks."""
    today = date.today().isoformat()
    checks: list[dict] = []

    def add_check(
        name: str,
        scope: str,
        count: int,
        severity: str,
        description: str,
        finding: str,
    ) -> None:
        checks.append(
            {
                "check": name,
                "scope": scope,
                "status": "Passed" if count == 0 else "Review",
                "issues": count,
                "severity": severity,
                "description": description,
                "finding": finding if count else "No issues found.",
            }
        )

    with closing(get_connection(db_path)) as connection:
        add_check(
            "Duplicate loan IDs",
            "loans",
            _scalar(
                connection,
                "SELECT COUNT(*) FROM (SELECT loan_id FROM loans GROUP BY loan_id HAVING COUNT(*) > 1)",
            ),
            "Critical",
            "Each loan_id must identify exactly one loan.",
            "Loan IDs appear on more than one row.",
        )
        add_check(
            "Duplicate customer IDs",
            "customers",
            _scalar(
                connection,
                "SELECT COUNT(*) FROM (SELECT customer_id FROM customers "
                "GROUP BY customer_id HAVING COUNT(*) > 1)",
            ),
            "Critical",
            "Each customer_id must identify exactly one customer.",
            "Customer IDs appear on more than one row.",
        )
        add_check(
            "Duplicate snapshot keys",
            "portfolio_snapshots",
            _scalar(
                connection,
                "SELECT COUNT(*) FROM (SELECT snapshot_date, loan_id "
                "FROM portfolio_snapshots GROUP BY snapshot_date, loan_id "
                "HAVING COUNT(*) > 1)",
            ),
            "Critical",
            "A loan can have at most one snapshot per month-end.",
            "Duplicate month-end snapshot keys were found.",
        )
        add_check(
            "Missing loan fields",
            "loans",
            _scalar(
                connection,
                """
                SELECT COUNT(*) FROM loans
                WHERE loan_id IS NULL OR TRIM(CAST(loan_id AS TEXT)) = ''
                   OR customer_id IS NULL OR TRIM(CAST(customer_id AS TEXT)) = ''
                   OR loan_type IS NULL OR TRIM(CAST(loan_type AS TEXT)) = ''
                   OR principal_amount IS NULL OR outstanding_balance IS NULL
                   OR interest_rate IS NULL OR term_months IS NULL
                   OR disbursement_date IS NULL OR maturity_date IS NULL
                   OR status IS NULL OR days_past_due IS NULL OR risk_grade IS NULL
                """,
            ),
            "Critical",
            "Critical loan fields must be populated.",
            "Loans contain missing values in required fields.",
        )
        add_check(
            "Missing customer fields",
            "customers",
            _scalar(
                connection,
                """
                SELECT COUNT(*) FROM customers
                WHERE customer_id IS NULL OR TRIM(CAST(customer_id AS TEXT)) = ''
                   OR full_name IS NULL OR TRIM(CAST(full_name AS TEXT)) = ''
                   OR segment IS NULL OR credit_score IS NULL
                   OR annual_income IS NULL OR customer_since IS NULL
                """,
            ),
            "Critical",
            "Customer identity and segmentation fields must be populated.",
            "Customers contain missing values in required fields.",
        )
        add_check(
            "Orphan loans",
            "loans → customers",
            _scalar(
                connection,
                """
                SELECT COUNT(*) FROM loans AS l
                LEFT JOIN customers AS c ON c.customer_id = l.customer_id
                WHERE c.customer_id IS NULL
                """,
            ),
            "Critical",
            "Every loan must reference an existing customer.",
            "Loans reference customer IDs that do not exist.",
        )
        add_check(
            "Orphan snapshots",
            "portfolio_snapshots → loans",
            _scalar(
                connection,
                """
                SELECT COUNT(*) FROM portfolio_snapshots AS s
                LEFT JOIN loans AS l ON l.loan_id = s.loan_id
                WHERE l.loan_id IS NULL
                """,
            ),
            "Critical",
            "Every snapshot must reference an existing loan.",
            "Snapshots reference loan IDs that do not exist.",
        )
        add_check(
            "Invalid financial values",
            "loans",
            _scalar(
                connection,
                """
                SELECT COUNT(*) FROM loans
                WHERE principal_amount <= 0
                   OR outstanding_balance < 0
                   OR interest_rate < 0 OR interest_rate > 50
                   OR term_months <= 0
                   OR days_past_due < 0
                """,
            ),
            "Critical",
            "Amounts, rates and terms must fall within valid business ranges.",
            "Loans contain negative, zero or out-of-range financial values.",
        )
        add_check(
            "Closed loans with balance",
            "loans",
            _scalar(
                connection,
                "SELECT COUNT(*) FROM loans WHERE status = 'Closed' AND outstanding_balance > 0.01",
            ),
            "Warning",
            "Closed loans should have no outstanding principal.",
            "Closed loans still carry an outstanding balance.",
        )
        add_check(
            "Defaulted loans below 90 DPD",
            "loans",
            _scalar(
                connection,
                "SELECT COUNT(*) FROM loans WHERE status = 'Defaulted' AND days_past_due < 90",
            ),
            "Warning",
            "Defaulted loans should be at least 90 days past due.",
            "Defaulted status is inconsistent with days past due.",
        )
        add_check(
            "Invalid categorical values",
            "loans / customers",
            _scalar(
                connection,
                """
                SELECT
                    (SELECT COUNT(*) FROM loans
                     WHERE status NOT IN ('Active', 'Closed', 'Defaulted')
                        OR risk_grade NOT IN ('A', 'B', 'C', 'D', 'E')
                        OR loan_type NOT IN ('Personal Loan', 'Home Loan', 'Auto Loan',
                                             'Education Loan', 'Business Loan',
                                             'Equipment Loan', 'Credit Card'))
                  + (SELECT COUNT(*) FROM customers
                     WHERE segment NOT IN ('Retail', 'SME', 'Corporate', 'Premium'))
                """,
            ),
            "Warning",
            "Status, risk grade, product and segment values must use supported domains.",
            "Unsupported categorical values were found.",
        )
        add_check(
            "Future-dated disbursements",
            "loans",
            _scalar(connection, "SELECT COUNT(*) FROM loans WHERE disbursement_date > ?", (today,)),
            "Warning",
            "A disbursement cannot occur after the current date.",
            "Loans have disbursement dates in the future.",
        )
        add_check(
            "Maturity before disbursement",
            "loans",
            _scalar(
                connection,
                "SELECT COUNT(*) FROM loans WHERE maturity_date < disbursement_date",
            ),
            "Critical",
            "Maturity dates must follow the disbursement date.",
            "Maturity dates precede the disbursement date.",
        )
        add_check(
            "Invalid snapshots",
            "portfolio_snapshots",
            _scalar(
                connection,
                """
                SELECT COUNT(*) FROM portfolio_snapshots
                WHERE outstanding_balance < 0 OR days_past_due < 0
                   OR status NOT IN ('Active', 'Defaulted', 'Closed')
                """,
            ),
            "Warning",
            "Historical snapshots must contain valid balances and statuses.",
            "Snapshots contain invalid balances, DPD or status values.",
        )
        integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
        add_check(
            "SQLite integrity",
            "database",
            0 if integrity == "ok" else 1,
            "Critical",
            "SQLite's built-in file and index integrity check must return 'ok'.",
            f"Integrity check returned: {integrity}",
        )

    tables = {}
    with closing(get_connection(db_path)) as connection:
        for table in ("customers", "loans", "portfolio_snapshots"):
            tables[table] = pd.read_sql_query(f"SELECT * FROM {table}", connection)

    missing_rows: list[dict] = []
    for table, frame in tables.items():
        for column in frame.columns:
            series = frame[column]
            blank = series.isna() | (
                series.map(lambda value: isinstance(value, str) and not value.strip())
            )
            missing = int(blank.sum())
            total = len(frame)
            missing_rows.append(
                {
                    "table": table,
                    "column": column,
                    "missing": missing,
                    "total": total,
                    "completeness": round(100 * (1 - missing / total), 2) if total else 100.0,
                    "critical": column in CRITICAL_COLUMNS.get(table, []),
                }
            )

    missing_frame = pd.DataFrame(missing_rows)
    if not missing_frame.empty:
        missing_frame = missing_frame.sort_values(
            ["missing", "critical", "table", "column"],
            ascending=[False, False, True, True],
        ).reset_index(drop=True)

    check_frame = pd.DataFrame(checks)
    passed = int((check_frame["status"] == "Passed").sum())
    review = int((check_frame["status"] == "Review").sum())
    critical_issues = int(
        check_frame.loc[check_frame["severity"] == "Critical", "issues"].sum()
    )
    rows_scanned = int(sum(len(frame) for frame in tables.values()))

    return {
        "checks": check_frame,
        "missing": missing_frame,
        "summary": {
            "checks_run": len(check_frame),
            "passed": passed,
            "review": review,
            "critical_issues": critical_issues,
            "rows_scanned": rows_scanned,
            "score": round(100 * passed / len(check_frame), 1) if len(check_frame) else 100.0,
        },
    }
