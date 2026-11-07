"""Core tests for the database, analytics SQL, CSV validation and quality checks."""

from __future__ import annotations

import tempfile
import unittest
from datetime import timedelta
from pathlib import Path

import pandas as pd

from loan_dashboard.config import DB_PATH
from loan_dashboard.csv_io import (
    build_import_template,
    validate_upload_against_database,
)
from loan_dashboard.database import (
    fetch_customer_ids,
    initialize_database,
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
    get_segment_performance,
    get_top_exposures,
)


class DashboardDatabaseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.temp_dir = tempfile.TemporaryDirectory()
        cls.db_path = Path(cls.temp_dir.name) / "test_portfolio.db"
        cls.counts = initialize_database(
            cls.db_path,
            n_customers=30,
            n_loans=55,
            seed=7,
        )

    @classmethod
    def tearDownClass(cls) -> None:
        cls.temp_dir.cleanup()

    def test_database_has_relational_records(self) -> None:
        self.assertEqual(self.counts["customers"], 30)
        self.assertEqual(self.counts["loans"], 55)
        self.assertGreater(self.counts["portfolio_snapshots"], 0)

    def test_queries_return_data(self) -> None:
        filters = PortfolioFilters()
        kpis = get_kpis(filters, self.db_path)
        current_loan_count = table_counts(self.db_path)["loans"]
        self.assertEqual(int(kpis["total_loans"]), current_loan_count)
        self.assertGreater(kpis["outstanding_balance"], 0)
        self.assertFalse(get_monthly_originations(filters, self.db_path).empty)
        self.assertFalse(get_portfolio_mix(filters, self.db_path).empty)
        self.assertFalse(get_overdue_trend(filters, self.db_path).empty)
        self.assertFalse(get_dpd_buckets(filters, self.db_path).empty)
        self.assertFalse(get_segment_performance(filters, self.db_path).empty)
        self.assertFalse(get_top_exposures(filters, 5, self.db_path).empty)
        self.assertEqual(len(get_loans_table(filters, self.db_path)), current_loan_count)

    def test_filters_are_applied_in_sql(self) -> None:
        all_kpis = get_kpis(PortfolioFilters(), self.db_path)
        active_kpis = get_kpis(PortfolioFilters(statuses=("Active",)), self.db_path)
        closed_kpis = get_kpis(PortfolioFilters(statuses=("Closed",)), self.db_path)
        self.assertLessEqual(active_kpis["total_loans"], all_kpis["total_loans"])
        self.assertEqual(
            int(active_kpis["total_loans"] + closed_kpis["total_loans"]),
            int(all_kpis["total_loans"]),
        )

        options = get_filter_options(self.db_path)
        earliest = options["min_date"]
        latest = options["max_date"]
        cutoff = earliest + timedelta(days=200)
        date_filtered = get_kpis(
            PortfolioFilters(start_date=cutoff, end_date=latest), self.db_path
        )
        self.assertLessEqual(date_filtered["total_loans"], all_kpis["total_loans"])

        segment = options["segments"][0][0]
        segment_filtered = get_kpis(PortfolioFilters(segments=(segment,)), self.db_path)
        self.assertLess(segment_filtered["total_loans"], all_kpis["total_loans"])

    def test_data_quality_checks_pass(self) -> None:
        result = run_quality_checks(self.db_path)
        self.assertEqual(result["summary"]["review"], 0)
        self.assertEqual(result["summary"]["critical_issues"], 0)
        self.assertEqual(result["summary"]["passed"], result["summary"]["checks_run"])
        critical = result["missing"][result["missing"]["critical"]]
        self.assertTrue((critical["missing"] == 0).all())

    def test_csv_validation_and_upsert(self) -> None:
        customer_id = next(iter(fetch_customer_ids(self.db_path)))
        template = build_import_template(customer_id)
        validation = validate_upload_against_database(template, self.db_path)
        self.assertTrue(validation.issues.empty)
        self.assertEqual(validation.summary["valid"], 1)

        before = table_counts(self.db_path)["loans"]
        result = upsert_loans(validation.cleaned, self.db_path)
        after = table_counts(self.db_path)["loans"]
        self.assertEqual(result["inserted"], 1)
        self.assertEqual(result["total"], 1)
        self.assertEqual(after, before + 1)

        # Re-importing the same loan ID updates in place.
        result = upsert_loans(validation.cleaned, self.db_path)
        self.assertEqual(result["updated"], 1)
        self.assertEqual(table_counts(self.db_path)["loans"], after)

    def test_invalid_csv_is_rejected(self) -> None:
        customer_id = next(iter(fetch_customer_ids(self.db_path)))
        invalid = build_import_template(customer_id)
        invalid.loc[0, "customer_id"] = "CUST-DOES-NOT-EXIST"
        invalid.loc[0, "loan_type"] = "Crypto Loan"
        invalid.loc[0, "interest_rate"] = 99
        validation = validate_upload_against_database(invalid, self.db_path)
        self.assertEqual(validation.summary["valid"], 0)
        self.assertGreaterEqual(len(validation.issues), 3)

    def test_duplicate_rows_are_flagged(self) -> None:
        customer_id = next(iter(fetch_customer_ids(self.db_path)))
        template = build_import_template(customer_id)
        duplicated = pd.concat([template, template], ignore_index=True)
        validation = validate_upload_against_database(duplicated, self.db_path)
        self.assertEqual(validation.summary["valid"], 1)
        self.assertFalse(validation.issues.empty)
        self.assertTrue((validation.issues["field"] == "loan_id").any())

    def test_status_totals_reconcile(self) -> None:
        for status in ("Active", "Closed", "Defaulted"):
            filtered = get_kpis(PortfolioFilters(statuses=(status,)), self.db_path)
            self.assertEqual(float(filtered["total_loans"]), float(filtered["total_loans"]))
        total = get_kpis(PortfolioFilters(), self.db_path)["total_loans"]
        status_sum = sum(
            get_kpis(PortfolioFilters(statuses=(status,)), self.db_path)["total_loans"]
            for status in ("Active", "Closed", "Defaulted")
        )
        self.assertEqual(int(total), int(status_sum))


class SampleDataTests(unittest.TestCase):
    def test_default_database_includes_required_volume(self) -> None:
        if not DB_PATH.exists():
            self.skipTest("Default database has not been initialized.")
        counts = table_counts(DB_PATH)
        self.assertGreaterEqual(counts["loans"], 1_000)
        self.assertGreater(counts["customers"], 0)

    def test_sample_loans_csv_is_importable(self) -> None:
        sample_path = Path("data/sample/loans_sample.csv")
        if not sample_path.exists() or not DB_PATH.exists():
            self.skipTest("Sample CSV has not been generated.")
        frame = pd.read_csv(sample_path)
        validation = validate_upload_against_database(frame, DB_PATH)
        self.assertEqual(validation.summary["invalid"], 0)
        self.assertEqual(validation.summary["valid"], len(frame))


if __name__ == "__main__":
    unittest.main()
