#!/usr/bin/env python3
"""Create or reset the demo SQLite database and export sample CSVs.

Usage:
    python init_db.py                 # create the database if it is missing
    python init_db.py --reset         # rebuild the demo portfolio from scratch
    python init_db.py --loans 2500    # choose a different portfolio size
"""

from __future__ import annotations

import argparse
from pathlib import Path

from loan_dashboard.config import DB_PATH, SAMPLE_DIR
from loan_dashboard.csv_io import build_import_template
from loan_dashboard.database import (
    export_sample_files,
    fetch_customer_ids,
    initialize_database,
    read_dataframe,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reset", action="store_true", help="delete and rebuild the database")
    parser.add_argument("--loans", type=int, default=1_600, help="number of loans to generate")
    parser.add_argument("--customers", type=int, default=900, help="number of customers to generate")
    parser.add_argument("--seed", type=int, default=42, help="random seed for reproducible data")
    parser.add_argument("--no-sample", action="store_true", help="skip writing CSV sample files")
    parser.add_argument("--db", type=Path, default=DB_PATH, help="alternate SQLite database path")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    counts = initialize_database(
        db_path=args.db,
        n_customers=args.customers,
        n_loans=args.loans,
        seed=args.seed,
        reset=args.reset,
    )

    print(f"Database: {args.db.resolve()}")
    print(
        f"Rows: {counts['customers']:,} customers · "
        f"{counts['loans']:,} loans · {counts['portfolio_snapshots']:,} monthly snapshots"
    )

    distribution = read_dataframe(
        "SELECT status, COUNT(*) AS loans, ROUND(SUM(principal_amount), 2) AS principal "
        "FROM loans GROUP BY status ORDER BY loans DESC",
        db_path=args.db,
    )
    if not distribution.empty:
        print("\nLoan status mix:")
        for row in distribution.itertuples(index=False):
            print(f"  {row.status:<10} {row.loans:>5,} loans   ${row.principal:>15,.0f}")

    if not args.no_sample:
        customer_ids = fetch_customer_ids(args.db)
        first_customer = next(iter(customer_ids), "CUST-000001")
        template = build_import_template(first_customer)
        template.to_csv(SAMPLE_DIR / "import_template.csv", index=False)
        outputs = export_sample_files(args.db, SAMPLE_DIR)
        print("\nSample files:")
        for label, path in outputs.items():
            print(f"  {label:<12} {path.resolve()}")
        print(f"  {'template':<12} {(SAMPLE_DIR / 'import_template.csv').resolve()}")


if __name__ == "__main__":
    main()
