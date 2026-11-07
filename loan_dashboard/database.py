"""SQLite persistence, schema management and loan upserts."""

from __future__ import annotations

import calendar
import sqlite3
from contextlib import closing
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

from .config import DB_PATH
from .data_generator import generate_dataset

SCHEMA_SQL = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS customers (
    customer_id          TEXT PRIMARY KEY,
    full_name            TEXT NOT NULL,
    email                TEXT,
    phone                TEXT,
    city                 TEXT,
    state                TEXT,
    segment              TEXT NOT NULL,
    relationship_manager TEXT,
    credit_score         INTEGER NOT NULL,
    annual_income        REAL NOT NULL,
    customer_since       TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS loans (
    loan_id             TEXT PRIMARY KEY,
    customer_id         TEXT NOT NULL,
    loan_type           TEXT NOT NULL,
    principal_amount    REAL NOT NULL CHECK (principal_amount > 0),
    outstanding_balance REAL NOT NULL CHECK (outstanding_balance >= 0),
    interest_rate       REAL NOT NULL,
    term_months         INTEGER NOT NULL,
    monthly_payment     REAL NOT NULL,
    disbursement_date   TEXT NOT NULL,
    maturity_date       TEXT NOT NULL,
    status              TEXT NOT NULL,
    days_past_due       INTEGER NOT NULL DEFAULT 0,
    risk_grade          TEXT NOT NULL,
    purpose             TEXT,
    branch              TEXT,
    collateral_type     TEXT,
    last_payment_date   TEXT,
    next_due_date       TEXT,
    default_date        TEXT,
    closed_date         TEXT,
    FOREIGN KEY (customer_id) REFERENCES customers (customer_id)
);

CREATE INDEX IF NOT EXISTS idx_loans_customer ON loans (customer_id);
CREATE INDEX IF NOT EXISTS idx_loans_disbursement ON loans (disbursement_date);
CREATE INDEX IF NOT EXISTS idx_loans_type ON loans (loan_type);
CREATE INDEX IF NOT EXISTS idx_loans_status ON loans (status);
CREATE INDEX IF NOT EXISTS idx_loans_risk ON loans (risk_grade);

CREATE TABLE IF NOT EXISTS portfolio_snapshots (
    snapshot_date       TEXT NOT NULL,
    loan_id             TEXT NOT NULL,
    outstanding_balance REAL NOT NULL,
    days_past_due       INTEGER NOT NULL,
    status              TEXT NOT NULL,
    PRIMARY KEY (snapshot_date, loan_id),
    FOREIGN KEY (loan_id) REFERENCES loans (loan_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_snapshots_date ON portfolio_snapshots (snapshot_date);

DROP VIEW IF EXISTS loan_details;
CREATE VIEW loan_details AS
SELECT
    l.loan_id,
    l.customer_id,
    c.full_name,
    c.segment,
    c.city,
    c.state,
    c.credit_score,
    c.annual_income,
    c.relationship_manager,
    l.loan_type,
    l.principal_amount,
    l.outstanding_balance,
    l.interest_rate,
    l.term_months,
    l.monthly_payment,
    l.disbursement_date,
    l.maturity_date,
    l.status,
    l.days_past_due,
    l.risk_grade,
    l.purpose,
    l.branch,
    l.collateral_type,
    l.last_payment_date,
    l.next_due_date,
    l.default_date,
    l.closed_date
FROM loans AS l
JOIN customers AS c ON c.customer_id = l.customer_id;
"""

LOAN_COLUMNS = [
    "loan_id", "customer_id", "loan_type", "principal_amount",
    "outstanding_balance", "interest_rate", "term_months", "monthly_payment",
    "disbursement_date", "maturity_date", "status", "days_past_due",
    "risk_grade", "purpose", "branch", "collateral_type", "last_payment_date",
    "next_due_date", "default_date", "closed_date",
]

LOAN_UPSERT_SQL = f"""
INSERT INTO loans ({", ".join(LOAN_COLUMNS)})
VALUES ({", ".join("?" for _ in LOAN_COLUMNS)})
ON CONFLICT(loan_id) DO UPDATE SET
    customer_id = excluded.customer_id,
    loan_type = excluded.loan_type,
    principal_amount = excluded.principal_amount,
    outstanding_balance = excluded.outstanding_balance,
    interest_rate = excluded.interest_rate,
    term_months = excluded.term_months,
    monthly_payment = excluded.monthly_payment,
    disbursement_date = excluded.disbursement_date,
    maturity_date = excluded.maturity_date,
    status = excluded.status,
    days_past_due = excluded.days_past_due,
    risk_grade = excluded.risk_grade,
    purpose = excluded.purpose,
    branch = excluded.branch,
    collateral_type = excluded.collateral_type,
    last_payment_date = excluded.last_payment_date,
    next_due_date = excluded.next_due_date,
    default_date = excluded.default_date,
    closed_date = excluded.closed_date;
"""


def get_connection(db_path: Path | str = DB_PATH) -> sqlite3.Connection:
    """Open a connection with row access by column name and FK enforcement."""
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path, timeout=20)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA journal_mode = WAL")
    return connection


def create_schema(connection: sqlite3.Connection) -> None:
    connection.executescript(SCHEMA_SQL)
    connection.commit()


def table_counts(db_path: Path | str = DB_PATH) -> dict[str, int]:
    with closing(get_connection(db_path)) as connection:
        return {
            table: int(connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])
            for table in ("customers", "loans", "portfolio_snapshots")
        }


def _remove_database_files(path: Path) -> None:
    for suffix in ("", "-wal", "-shm"):
        candidate = Path(f"{path}{suffix}")
        if candidate.exists():
            candidate.unlink()


def initialize_database(
    db_path: Path | str = DB_PATH,
    *,
    n_customers: int = 900,
    n_loans: int = 1_600,
    seed: int = 42,
    reset: bool = False,
) -> dict[str, int]:
    """Create the schema and demo dataset if needed.

    Existing databases are left untouched unless ``reset=True``.  Returns a
    count of rows in each table.
    """
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    if reset:
        _remove_database_files(path)

    if path.exists():
        try:
            counts = table_counts(path)
            if counts["loans"] > 0:
                return counts
        except sqlite3.DatabaseError:
            # A corrupt or schema-less file is replaced by a fresh database.
            _remove_database_files(path)

    customers, loans, snapshots = generate_dataset(
        n_customers=n_customers,
        n_loans=n_loans,
        seed=seed,
    )

    with closing(get_connection(path)) as connection:
        create_schema(connection)
        customers.to_sql("customers", connection, if_exists="append", index=False)
        loans.to_sql("loans", connection, if_exists="append", index=False)
        snapshots.to_sql("portfolio_snapshots", connection, if_exists="append", index=False)
        connection.commit()

    return table_counts(path)


def ensure_database(db_path: Path | str = DB_PATH) -> dict[str, int]:
    """Initialize the app's database on first run."""
    return initialize_database(db_path=db_path)


def _latest_completed_month_end(as_of: date | None = None) -> date:
    as_of = as_of or date.today()
    previous = as_of.replace(day=1) - timedelta(days=1)
    return date(previous.year, previous.month, calendar.monthrange(previous.year, previous.month)[1])


def upsert_loans(
    loans: pd.DataFrame,
    db_path: Path | str = DB_PATH,
    *,
    create_snapshot: bool = True,
) -> dict[str, int]:
    """Insert or update loans and refresh their latest month-end snapshot."""
    if loans.empty:
        return {"inserted": 0, "updated": 0, "total": 0}

    with closing(get_connection(db_path)) as connection:
        existing_ids = {
            row[0]
            for row in connection.execute(
                f"SELECT loan_id FROM loans WHERE loan_id IN ({','.join('?' for _ in range(len(loans)))})",
                tuple(loans["loan_id"].tolist()),
            ).fetchall()
        }

        records = [
            tuple(None if pd.isna(value) else value for value in row)
            for row in loans[LOAN_COLUMNS].itertuples(index=False, name=None)
        ]

        with connection:
            connection.executemany(LOAN_UPSERT_SQL, records)

            if create_snapshot:
                snapshot_date = _latest_completed_month_end()
                snapshot_rows = []
                for loan in loans.itertuples(index=False):
                    disbursement = date.fromisoformat(str(loan.disbursement_date))
                    if disbursement > snapshot_date:
                        continue
                    if loan.status == "Closed" or float(loan.outstanding_balance) <= 0:
                        connection.execute(
                            "DELETE FROM portfolio_snapshots WHERE loan_id = ? AND snapshot_date = ?",
                            (loan.loan_id, snapshot_date.isoformat()),
                        )
                        continue
                    snapshot_rows.append(
                        (
                            snapshot_date.isoformat(),
                            loan.loan_id,
                            float(loan.outstanding_balance),
                            int(loan.days_past_due),
                            "Defaulted" if loan.status == "Defaulted" else "Active",
                        )
                    )
                if snapshot_rows:
                    connection.executemany(
                        """
                        INSERT INTO portfolio_snapshots
                            (snapshot_date, loan_id, outstanding_balance, days_past_due, status)
                        VALUES (?, ?, ?, ?, ?)
                        ON CONFLICT(snapshot_date, loan_id) DO UPDATE SET
                            outstanding_balance = excluded.outstanding_balance,
                            days_past_due = excluded.days_past_due,
                            status = excluded.status
                        """,
                        snapshot_rows,
                    )

    updated = len(existing_ids)
    return {"inserted": len(loans) - updated, "updated": updated, "total": len(loans)}


def fetch_customer_ids(db_path: Path | str = DB_PATH) -> dict[str, str]:
    with closing(get_connection(db_path)) as connection:
        return {
            row["customer_id"]: row["full_name"]
            for row in connection.execute(
                "SELECT customer_id, full_name FROM customers ORDER BY customer_id"
            )
        }


def fetch_existing_loan_ids(db_path: Path | str = DB_PATH) -> set[str]:
    with closing(get_connection(db_path)) as connection:
        return {row[0] for row in connection.execute("SELECT loan_id FROM loans")}


def read_dataframe(
    query: str,
    params: tuple | list | None = None,
    db_path: Path | str = DB_PATH,
) -> pd.DataFrame:
    """Run a SELECT and return a DataFrame (small helper used by pages/tests)."""
    with closing(get_connection(db_path)) as connection:
        return pd.read_sql_query(query, connection, params=params or ())


def export_sample_files(db_path: Path | str = DB_PATH, sample_dir: Path | str | None = None) -> dict[str, Path]:
    """Write CSV snapshots of the demo database for offline exploration."""
    from .config import SAMPLE_DIR

    target = Path(sample_dir) if sample_dir else SAMPLE_DIR
    target.mkdir(parents=True, exist_ok=True)
    outputs = {
        "customers": target / "customers_sample.csv",
        "loans": target / "loans_sample.csv",
        "snapshots": target / "portfolio_snapshots_sample.csv",
    }

    with closing(get_connection(db_path)) as connection:
        pd.read_sql_query("SELECT * FROM customers ORDER BY customer_id", connection).to_csv(
            outputs["customers"], index=False
        )
        pd.read_sql_query(
            "SELECT * FROM loan_details ORDER BY disbursement_date DESC, loan_id",
            connection,
        ).to_csv(outputs["loans"], index=False)
        pd.read_sql_query(
            "SELECT * FROM portfolio_snapshots ORDER BY snapshot_date, loan_id",
            connection,
        ).to_csv(outputs["snapshots"], index=False)

    return outputs
