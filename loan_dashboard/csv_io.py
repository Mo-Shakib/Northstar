"""CSV validation, import preparation and export helpers."""

from __future__ import annotations

import calendar
import io
import math
from dataclasses import dataclass
from datetime import date, timedelta

import pandas as pd

from .config import LOAN_TYPES, RISK_GRADES, STATUSES
from .database import LOAN_COLUMNS, fetch_customer_ids, fetch_existing_loan_ids

REQUIRED_COLUMNS = [
    "loan_id",
    "customer_id",
    "loan_type",
    "principal_amount",
    "interest_rate",
    "term_months",
    "disbursement_date",
    "status",
]

IMPORT_HELP = (
    "Required columns: loan_id, customer_id, loan_type, principal_amount, interest_rate, "
    "term_months, disbursement_date and status. Optional fields fall back to sensible defaults."
)


@dataclass
class ImportValidation:
    cleaned: pd.DataFrame
    issues: pd.DataFrame
    summary: dict
    warnings: list[str]

    @property
    def is_valid(self) -> bool:
        return not self.cleaned.empty and self.issues.empty


def _empty_issues() -> pd.DataFrame:
    return pd.DataFrame(columns=["row", "severity", "field", "message"])


def _canonical(value: str, options: tuple[str, ...]) -> str | None:
    lookup = {option.casefold(): option for option in options}
    return lookup.get(str(value).strip().casefold())


def _add_months(value: date, months: int) -> date:
    month_index = value.month - 1 + int(months)
    year = value.year + month_index // 12
    month = month_index % 12 + 1
    day = min(value.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def _monthly_payment(principal: float, annual_rate: float, term_months: int) -> float:
    monthly_rate = annual_rate / 100 / 12
    if monthly_rate <= 0:
        return round(principal / term_months, 2)
    factor = (1 + monthly_rate) ** term_months
    return round(principal * monthly_rate * factor / (factor - 1), 2)


def _parse_date(value, label: str) -> str | None:
    if value is None or pd.isna(value) or str(value).strip() == "":
        return None
    parsed = pd.to_datetime(value, errors="coerce")
    if pd.isna(parsed):
        raise ValueError(f"{label} is not a valid date.")
    return parsed.date().isoformat()


def _is_blank(value) -> bool:
    return value is None or pd.isna(value) or str(value).strip() == ""


def prepare_upload(frame: pd.DataFrame) -> pd.DataFrame:
    """Normalize column whitespace/case without mutating the uploaded frame."""
    prepared = frame.copy()
    prepared.columns = [str(column).strip().lower() for column in prepared.columns]
    return prepared


def validate_loan_csv(
    frame: pd.DataFrame,
    *,
    existing_customer_ids: set[str] | None = None,
    existing_loan_ids: set[str] | None = None,
) -> ImportValidation:
    """Validate and normalize an uploaded loan CSV.

    Invalid rows are excluded from ``cleaned`` and reported in ``issues``.
    Updating existing loan IDs is supported intentionally (upsert).
    """
    prepared = prepare_upload(frame)
    missing_columns = [column for column in REQUIRED_COLUMNS if column not in prepared.columns]
    if missing_columns:
        issues = pd.DataFrame(
            [
                {
                    "row": None,
                    "severity": "Error",
                    "field": ", ".join(missing_columns),
                    "message": "Required column(s) are missing from the CSV header.",
                }
            ]
        )
        return ImportValidation(
            cleaned=pd.DataFrame(columns=LOAN_COLUMNS),
            issues=issues,
            summary={"total": len(prepared), "valid": 0, "invalid": len(prepared), "new": 0, "updates": 0},
            warnings=[],
        )

    existing_loan_ids = existing_loan_ids or set()
    issues: list[dict] = []
    warnings: list[str] = []
    clean_rows: list[dict] = []
    seen_ids: set[str] = set()
    replacement_ids: set[str] = set()
    today = date.today()

    for position, (_, row) in enumerate(prepared.iterrows(), start=2):
        errors_before = len(issues)
        loan_id = str(row.get("loan_id", "")).strip()
        if not loan_id:
            issues.append({"row": position, "severity": "Error", "field": "loan_id", "message": "Loan ID is required."})
            continue
        if loan_id in seen_ids:
            issues.append(
                {
                    "row": position,
                    "severity": "Error",
                    "field": "loan_id",
                    "message": f"Duplicate loan ID '{loan_id}' within the upload; the first row is kept.",
                }
            )
            continue
        seen_ids.add(loan_id)

        customer_id = str(row.get("customer_id", "")).strip()
        if not customer_id:
            issues.append({"row": position, "severity": "Error", "field": "customer_id", "message": "Customer ID is required."})
        elif existing_customer_ids is not None and customer_id not in existing_customer_ids:
            issues.append(
                {
                    "row": position,
                    "severity": "Error",
                    "field": "customer_id",
                    "message": f"Customer '{customer_id}' does not exist in the customer master.",
                }
            )

        loan_type = _canonical(row.get("loan_type", ""), LOAN_TYPES)
        if loan_type is None:
            issues.append(
                {
                    "row": position,
                    "severity": "Error",
                    "field": "loan_type",
                    "message": "Unsupported loan type. Use one of: " + ", ".join(LOAN_TYPES) + ".",
                }
            )

        status = _canonical(row.get("status", ""), STATUSES)
        if status is None:
            issues.append(
                {
                    "row": position,
                    "severity": "Error",
                    "field": "status",
                    "message": "Status must be Active, Closed or Defaulted.",
                }
            )

        try:
            principal = float(row.get("principal_amount"))
            if not math.isfinite(principal) or principal <= 0:
                raise ValueError
        except (TypeError, ValueError):
            principal = 0.0
            issues.append(
                {
                    "row": position,
                    "severity": "Error",
                    "field": "principal_amount",
                    "message": "Principal must be a positive number.",
                }
            )

        try:
            outstanding_value = row.get("outstanding_balance")
            outstanding = principal if _is_blank(outstanding_value) else float(outstanding_value)
            if not math.isfinite(outstanding) or outstanding < 0:
                raise ValueError
        except (TypeError, ValueError):
            outstanding = 0.0
            issues.append(
                {
                    "row": position,
                    "severity": "Error",
                    "field": "outstanding_balance",
                    "message": "Outstanding balance must be zero or greater.",
                }
            )

        try:
            interest_rate = float(row.get("interest_rate"))
            if not math.isfinite(interest_rate) or not 0 <= interest_rate <= 50:
                raise ValueError
        except (TypeError, ValueError):
            interest_rate = 0.0
            issues.append(
                {
                    "row": position,
                    "severity": "Error",
                    "field": "interest_rate",
                    "message": "Interest rate must be between 0 and 50.",
                }
            )

        try:
            term_months = int(float(row.get("term_months")))
            if not 1 <= term_months <= 600:
                raise ValueError
        except (TypeError, ValueError):
            term_months = 0
            issues.append(
                {
                    "row": position,
                    "severity": "Error",
                    "field": "term_months",
                    "message": "Term must be a whole number between 1 and 600 months.",
                }
            )

        try:
            disbursement = _parse_date(row.get("disbursement_date"), "disbursement_date")
            if disbursement is None:
                raise ValueError
        except ValueError:
            disbursement = None
            issues.append(
                {
                    "row": position,
                    "severity": "Error",
                    "field": "disbursement_date",
                    "message": "A valid disbursement date is required.",
                }
            )

        try:
            maturity = _parse_date(row.get("maturity_date"), "maturity_date")
        except ValueError:
            maturity = None
            issues.append(
                {
                    "row": position,
                    "severity": "Error",
                    "field": "maturity_date",
                    "message": "Maturity date is invalid.",
                }
            )

        try:
            days_past_due = int(float(row.get("days_past_due", 0) or 0))
            if days_past_due < 0:
                raise ValueError
        except (TypeError, ValueError):
            days_past_due = 0
            issues.append(
                {
                    "row": position,
                    "severity": "Error",
                    "field": "days_past_due",
                    "message": "Days past due must be zero or a positive integer.",
                }
            )

        risk_raw = row.get("risk_grade", "C")
        risk_grade = "C" if _is_blank(risk_raw) else str(risk_raw).strip().upper()
        if risk_grade not in RISK_GRADES:
            issues.append(
                {
                    "row": position,
                    "severity": "Error",
                    "field": "risk_grade",
                    "message": "Risk grade must be A, B, C, D or E.",
                }
            )

        if status == "Closed" and outstanding > 0.01:
            issues.append(
                {
                    "row": position,
                    "severity": "Error",
                    "field": "outstanding_balance",
                    "message": "Closed loans must have an outstanding balance of zero.",
                }
            )

        if status == "Defaulted" and 0 <= days_past_due < 90:
            days_past_due = 90
            warnings.append(f"Row {position}: defaulted loan adjusted to 90 days past due.")

        if len(issues) > errors_before:
            continue

        if disbursement and term_months and not maturity:
            maturity = _add_months(date.fromisoformat(disbursement), term_months).isoformat()
            warnings.append(f"Row {position}: maturity date derived from the loan term.")

        try:
            last_payment = _parse_date(row.get("last_payment_date"), "last_payment_date")
            next_due = _parse_date(row.get("next_due_date"), "next_due_date")
            default_date = _parse_date(row.get("default_date"), "default_date")
            closed_date = _parse_date(row.get("closed_date"), "closed_date")
        except ValueError as error:
            issues.append(
                {
                    "row": position,
                    "severity": "Error",
                    "field": "date",
                    "message": str(error),
                }
            )
            continue

        if status == "Active" and not next_due:
            next_due = (today + timedelta(days=30)).isoformat()
        if status == "Defaulted" and not default_date:
            default_date = (today - timedelta(days=days_past_due)).isoformat()
        if status == "Closed" and not closed_date:
            closed_date = today.isoformat()
            warnings.append(f"Row {position}: closed date defaulted to today.")

        try:
            monthly_payment = float(row.get("monthly_payment", 0) or 0)
            if monthly_payment <= 0:
                monthly_payment = _monthly_payment(principal, interest_rate, term_months)
        except (TypeError, ValueError):
            monthly_payment = _monthly_payment(principal, interest_rate, term_months)

        clean_rows.append(
            {
                "loan_id": loan_id,
                "customer_id": customer_id,
                "loan_type": loan_type,
                "principal_amount": round(principal, 2),
                "outstanding_balance": round(outstanding, 2),
                "interest_rate": round(interest_rate, 2),
                "term_months": term_months,
                "monthly_payment": round(monthly_payment, 2),
                "disbursement_date": disbursement,
                "maturity_date": maturity,
                "status": status,
                "days_past_due": days_past_due,
                "risk_grade": risk_grade,
                "purpose": "Imported" if _is_blank(row.get("purpose")) else str(row.get("purpose")).strip(),
                "branch": "Imported" if _is_blank(row.get("branch")) else str(row.get("branch")).strip(),
                "collateral_type": (
                    "Unsecured"
                    if _is_blank(row.get("collateral_type"))
                    else str(row.get("collateral_type")).strip()
                ),
                "last_payment_date": last_payment,
                "next_due_date": next_due,
                "default_date": default_date,
                "closed_date": closed_date,
            }
        )
        if loan_id in existing_loan_ids:
            replacement_ids.add(loan_id)

    cleaned = pd.DataFrame(clean_rows, columns=LOAN_COLUMNS)
    issue_frame = pd.DataFrame(issues, columns=["row", "severity", "field", "message"]) if issues else _empty_issues()

    return ImportValidation(
        cleaned=cleaned,
        issues=issue_frame,
        summary={
            "total": len(prepared),
            "valid": len(cleaned),
            "invalid": len(prepared) - len(cleaned),
            "new": len(cleaned) - len(replacement_ids),
            "updates": len(replacement_ids),
        },
        warnings=warnings,
    )


def validate_upload_against_database(
    frame: pd.DataFrame,
    db_path,
) -> ImportValidation:
    return validate_loan_csv(
        frame,
        existing_customer_ids=set(fetch_customer_ids(db_path)),
        existing_loan_ids=fetch_existing_loan_ids(db_path),
    )


def build_import_template(customer_id: str | None = None) -> pd.DataFrame:
    """One clean example row users can edit in a spreadsheet."""
    customer = customer_id or "CUST-000001"
    disbursement = date.today() - timedelta(days=180)
    term = 36
    principal = 25_000.0
    rate = 11.9
    return pd.DataFrame(
        [
            {
                "loan_id": "IMPORT-0001",
                "customer_id": customer,
                "loan_type": "Personal Loan",
                "principal_amount": principal,
                "outstanding_balance": 19_825.40,
                "interest_rate": rate,
                "term_months": term,
                "monthly_payment": _monthly_payment(principal, rate, term),
                "disbursement_date": disbursement.isoformat(),
                "maturity_date": _add_months(disbursement, term).isoformat(),
                "status": "Active",
                "days_past_due": 0,
                "risk_grade": "B",
                "purpose": "Home Improvement",
                "branch": "Downtown",
                "collateral_type": "Unsecured",
                "last_payment_date": (date.today() - timedelta(days=14)).isoformat(),
                "next_due_date": (date.today() + timedelta(days=16)).isoformat(),
                "default_date": None,
                "closed_date": None,
            }
        ],
        columns=LOAN_COLUMNS,
    )


def frame_to_csv_bytes(frame: pd.DataFrame) -> bytes:
    return frame.to_csv(index=False).encode("utf-8")


def read_csv_upload(upload) -> pd.DataFrame:
    """Read a Streamlit uploader object while providing a clear error on bad CSV."""
    raw = upload.getvalue() if hasattr(upload, "getvalue") else upload.read()
    try:
        return pd.read_csv(io.BytesIO(raw))
    except Exception as error:  # pandas exposes several parser exception types
        raise ValueError(f"Could not parse the CSV file: {error}") from error
