"""Smoke test that the Streamlit application renders every tab without errors."""

from __future__ import annotations

import unittest
from pathlib import Path

from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parent.parent


class DashboardAppSmokeTest(unittest.TestCase):
    def test_app_renders_all_tabs(self) -> None:
        app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=90)
        app.run()

        self.assertEqual(len(app.exception), 0, [exc.value for exc in app.exception])
        self.assertEqual(len(app.error), 0)
        self.assertEqual(
            [tab.label for tab in app.tabs],
            ["Overview", "Risk & delinquency", "Loan explorer", "Data quality", "Import & export"],
        )
        self.assertEqual(
            [widget.label for widget in app.sidebar.multiselect],
            ["Loan type", "Loan status", "Customer segment"],
        )
        self.assertGreater(len(app.dataframe), 5)
        self.assertGreater(len(app.get("plotly_chart")), 5)

    def test_sidebar_filter_reruns_cleanly(self) -> None:
        app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=90)
        app.run()
        app.sidebar.multiselect[0].set_value(["Home Loan"])
        app.run()
        self.assertEqual(len(app.exception), 0, [exc.value for exc in app.exception])
        self.assertEqual(app.sidebar.multiselect[0].value, ["Home Loan"])


if __name__ == "__main__":
    unittest.main()
