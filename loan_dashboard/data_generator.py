"""Deterministic synthetic data generation for the loan portfolio demo.

The generator intentionally keeps the data realistic without requiring an
external dataset or an internet connection.  All randomness is seeded so a
fresh database can be reproduced exactly on a given day.
"""

from __future__ import annotations

import calendar
import math
import random
from datetime import date, timedelta

import pandas as pd

FIRST_NAMES = [
    "Aarav", "Amelia", "Amina", "Andre", "Anika", "Arjun", "Ava", "Benjamin",
    "Camila", "Carlos", "Charlotte", "Chloe", "Daniel", "David", "Diego",
    "Elena", "Elias", "Emma", "Ethan", "Fatima", "Gabriel", "Grace", "Hassan",
    "Henry", "Ibrahim", "Isabella", "Jack", "James", "Jasmine", "Javier",
    "Jiah", "Jordan", "Julia", "Kai", "Karen", "Kevin", "Laila", "Liam",
    "Lily", "Lucas", "Maya", "Mei", "Mia", "Michael", "Nadia", "Naomi",
    "Nathan", "Nora", "Olivia", "Omar", "Priya", "Rafael", "Ravi", "Riley",
    "Sakib", "Samantha", "Sara", "Sofia", "Tariq", "Theo", "Valentina",
    "Victor", "Wei", "Yara", "Zara", "Zoe",
]

LAST_NAMES = [
    "Ahmed", "Ali", "Anderson", "Baker", "Bennett", "Brown", "Chen", "Clark",
    "Davis", "Diaz", "Evans", "Fischer", "Garcia", "Gupta", "Harris", "Hassan",
    "Hernandez", "Hill", "Hoang", "Jackson", "Johnson", "Khan", "Kim", "Kumar",
    "Lee", "Lewis", "Lopez", "Martin", "Martinez", "Miller", "Mitchell",
    "Moore", "Morgan", "Nguyen", "Patel", "Perez", "Pham", "Rahman", "Reed",
    "Rivera", "Roberts", "Robinson", "Rodriguez", "Ross", "Sanchez", "Shah",
    "Singh", "Smith", "Taylor", "Thomas", "Thompson", "Torres", "Tran",
    "Walker", "Wang", "White", "Williams", "Wilson", "Wong", "Young", "Zhang",
]

CITIES = [
    ("New York", "NY"), ("Los Angeles", "CA"), ("Chicago", "IL"),
    ("Houston", "TX"), ("Phoenix", "AZ"), ("Philadelphia", "PA"),
    ("San Antonio", "TX"), ("San Diego", "CA"), ("Dallas", "TX"),
    ("San Jose", "CA"), ("Austin", "TX"), ("Jacksonville", "FL"),
    ("Columbus", "OH"), ("Charlotte", "NC"), ("Indianapolis", "IN"),
    ("San Francisco", "CA"), ("Seattle", "WA"), ("Denver", "CO"),
    ("Boston", "MA"), ("Atlanta", "GA"), ("Miami", "FL"), ("Nashville", "TN"),
    ("Portland", "OR"), ("Minneapolis", "MN"), ("Tampa", "FL"),
    ("Raleigh", "NC"), ("Salt Lake City", "UT"), ("Sacramento", "CA"),
]

RELATIONSHIP_MANAGERS = [
    "Alex Morgan", "Dana Whitfield", "Jordan Lee", "Maya Chen",
    "Noah Williams", "Priya Nair", "Sofia Alvarez", "Theo Brooks",
]

BRANCHES = [
    "Downtown", "Midtown", "Financial District", "Northgate", "Harbor Point",
    "Westfield", "Central Plaza", "Riverside",
]

SEGMENT_WEIGHTS = [0.56, 0.25, 0.13, 0.06]
SEGMENT_NAMES = ["Retail", "SME", "Corporate", "Premium"]

PRODUCT_WEIGHTS = {
    "Retail": {
        "Personal Loan": 0.34, "Auto Loan": 0.22, "Home Loan": 0.16,
        "Education Loan": 0.13, "Credit Card": 0.15,
    },
    "SME": {
        "Business Loan": 0.48, "Equipment Loan": 0.22, "Auto Loan": 0.14,
        "Personal Loan": 0.16,
    },
    "Corporate": {
        "Business Loan": 0.62, "Equipment Loan": 0.23, "Home Loan": 0.15,
    },
    "Premium": {
        "Home Loan": 0.34, "Business Loan": 0.26, "Personal Loan": 0.21,
        "Auto Loan": 0.19,
    },
}

PRODUCT_RANGES = {
    "Personal Loan": (5_000, 75_000),
    "Home Loan": (80_000, 1_200_000),
    "Auto Loan": (12_000, 120_000),
    "Education Loan": (8_000, 120_000),
    "Business Loan": (25_000, 650_000),
    "Equipment Loan": (15_000, 350_000),
    "Credit Card": (2_000, 40_000),
}

PRODUCT_RATE = {
    "Personal Loan": 12.4,
    "Home Loan": 6.7,
    "Auto Loan": 8.4,
    "Education Loan": 7.1,
    "Business Loan": 10.4,
    "Equipment Loan": 8.9,
    "Credit Card": 20.5,
}

PRODUCT_RATE_BOUNDS = {
    "Personal Loan": (8.0, 24.0),
    "Home Loan": (4.5, 9.5),
    "Auto Loan": (5.5, 14.0),
    "Education Loan": (4.5, 12.0),
    "Business Loan": (6.5, 18.0),
    "Equipment Loan": (6.0, 16.0),
    "Credit Card": (15.0, 29.0),
}

TERM_CHOICES = {
    "Personal Loan": ([12, 24, 36, 48, 60], [0.10, 0.28, 0.34, 0.18, 0.10]),
    "Home Loan": ([120, 180, 240, 300, 360], [0.10, 0.22, 0.30, 0.18, 0.20]),
    "Auto Loan": ([36, 48, 60, 72], [0.22, 0.28, 0.32, 0.18]),
    "Education Loan": ([36, 60, 84, 120], [0.18, 0.32, 0.28, 0.22]),
    "Business Loan": ([12, 24, 36, 60, 84], [0.16, 0.28, 0.28, 0.18, 0.10]),
    "Equipment Loan": ([24, 36, 48, 60, 84], [0.18, 0.28, 0.26, 0.18, 0.10]),
    "Credit Card": ([12, 24, 36], [0.42, 0.36, 0.22]),
}

PURPOSES = {
    "Personal Loan": ["Debt Consolidation", "Home Improvement", "Medical", "Wedding", "Travel"],
    "Home Loan": ["Home Purchase", "Refinance", "Renovation"],
    "Auto Loan": ["New Vehicle", "Used Vehicle", "Refinance"],
    "Education Loan": ["Tuition", "Living Expenses", "Certification"],
    "Business Loan": ["Working Capital", "Expansion", "Inventory", "Payroll"],
    "Equipment Loan": ["Machinery", "Technology", "Fleet"],
    "Credit Card": ["Everyday Spend", "Balance Transfer", "Travel"],
}

COLLATERAL = {
    "Personal Loan": "Unsecured",
    "Home Loan": "Property",
    "Auto Loan": "Vehicle",
    "Education Loan": "Unsecured",
    "Business Loan": "Blanket Lien",
    "Equipment Loan": "Equipment",
    "Credit Card": "Unsecured",
}

PRODUCT_RISK = {
    "Personal Loan": 1.00,
    "Home Loan": 0.45,
    "Auto Loan": 0.80,
    "Education Loan": 1.15,
    "Business Loan": 1.35,
    "Equipment Loan": 1.10,
    "Credit Card": 1.45,
}

CLOSE_FACTOR = {
    "Personal Loan": 0.20,
    "Home Loan": 0.03,
    "Auto Loan": 0.14,
    "Education Loan": 0.06,
    "Business Loan": 0.05,
    "Equipment Loan": 0.07,
    "Credit Card": 0.13,
}

SEGMENT_INCOME = {
    "Retail": (45_000, 0.42),
    "SME": (180_000, 0.62),
    "Corporate": (1_400_000, 0.82),
    "Premium": (460_000, 0.55),
}

SEGMENT_SCORE_MEAN = {"Retail": 690, "SME": 712, "Corporate": 756, "Premium": 742}
SEGMENT_RATE_ADJ = {"Retail": 0.35, "SME": -0.15, "Corporate": -0.85, "Premium": -0.55}
SEGMENT_PRINCIPAL_ADJ = {"Retail": 0.90, "SME": 1.20, "Corporate": 2.10, "Premium": 1.45}


def _weighted_choice(rng: random.Random, values: list[str], weights: list[float]) -> str:
    return rng.choices(values, weights=weights, k=1)[0]


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _add_months(value: date, months: int) -> date:
    month_index = value.month - 1 + months
    year = value.year + month_index // 12
    month = month_index % 12 + 1
    day = min(value.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def _month_end(value: date) -> date:
    return date(value.year, value.month, calendar.monthrange(value.year, value.month)[1])


def _previous_month_end(value: date) -> date:
    return _month_end(value.replace(day=1) - timedelta(days=1))


def _monthly_payment(principal: float, annual_rate: float, term_months: int) -> float:
    monthly_rate = annual_rate / 100 / 12
    if monthly_rate <= 0:
        return principal / term_months
    factor = (1 + monthly_rate) ** term_months
    return principal * monthly_rate * factor / (factor - 1)


def _balance_after_months(
    principal: float, annual_rate: float, term_months: int, months_elapsed: float
) -> float:
    """Remaining principal using a standard amortizing-loan schedule."""
    if months_elapsed <= 0:
        return principal
    if months_elapsed >= term_months:
        return 0.0
    monthly_rate = annual_rate / 100 / 12
    if monthly_rate <= 0:
        return principal * (1 - months_elapsed / term_months)
    growth = (1 + monthly_rate) ** term_months
    elapsed = (1 + monthly_rate) ** months_elapsed
    return principal * (growth - elapsed) / (growth - 1)


def _risk_grade(score: int) -> str:
    if score >= 760:
        return "A"
    if score >= 700:
        return "B"
    if score >= 650:
        return "C"
    if score >= 600:
        return "D"
    return "E"


def _whole_months(start: date, end: date) -> int:
    months = (end.year - start.year) * 12 + (end.month - start.month)
    if end.day < start.day:
        months -= 1
    return max(0, months)


def generate_customers(n_customers: int = 900, seed: int = 42) -> pd.DataFrame:
    """Create a realistic customer table with segment and credit attributes."""
    rng = random.Random(seed)
    today = date.today()
    rows: list[dict] = []

    for index in range(1, n_customers + 1):
        segment = _weighted_choice(rng, SEGMENT_NAMES, SEGMENT_WEIGHTS)
        first = rng.choice(FIRST_NAMES)
        last = rng.choice(LAST_NAMES)
        city, state = rng.choice(CITIES)
        income_center, income_sigma = SEGMENT_INCOME[segment]
        annual_income = max(28_000, rng.lognormvariate(math.log(income_center), income_sigma))
        credit_score = int(_clamp(rng.gauss(SEGMENT_SCORE_MEAN[segment], 58), 535, 835))
        customer_since = today - timedelta(days=rng.randint(120, 4_800))

        rows.append(
            {
                "customer_id": f"CUST-{index:06d}",
                "full_name": f"{first} {last}",
                "email": f"{first.lower()}.{last.lower()}{index}@example.com",
                "phone": f"+1 ({rng.randint(201, 989)}) {rng.randint(200, 999)}-{rng.randint(1000, 9999)}",
                "city": city,
                "state": state,
                "segment": segment,
                "relationship_manager": rng.choice(RELATIONSHIP_MANAGERS),
                "credit_score": credit_score,
                "annual_income": round(annual_income / 500) * 500,
                "customer_since": customer_since.isoformat(),
            }
        )

    return pd.DataFrame(rows)


def generate_loans(
    customers: pd.DataFrame,
    n_loans: int = 1_600,
    seed: int = 42,
    as_of: date | None = None,
) -> pd.DataFrame:
    """Create a loan book with coherent balances, delinquency and statuses."""
    rng = random.Random(seed + 1)
    as_of = as_of or date.today()
    horizon_days = 1_095  # 36 months of origination history
    customer_records = customers.to_dict("records")

    # Give every customer at least one loan, then distribute the remainder.
    assignments = [record["customer_id"] for record in customer_records]
    remaining = max(0, n_loans - len(assignments))
    assignments.extend(rng.choices(assignments, k=remaining))
    rng.shuffle(assignments)
    records_by_id = {record["customer_id"]: record for record in customer_records}

    rows: list[dict] = []
    for index, customer_id in enumerate(assignments, start=1):
        customer = records_by_id[customer_id]
        segment = customer["segment"]
        credit_score = int(customer["credit_score"])
        product = _weighted_choice(
            rng,
            list(PRODUCT_WEIGHTS[segment].keys()),
            list(PRODUCT_WEIGHTS[segment].values()),
        )

        low, high = PRODUCT_RANGES[product]
        principal = math.exp(rng.uniform(math.log(low), math.log(high)))
        principal *= SEGMENT_PRINCIPAL_ADJ[segment] * rng.uniform(0.78, 1.2)
        principal = round(principal / 100) * 100
        principal = max(low, principal)

        term_values, term_weights = TERM_CHOICES[product]
        term_months = rng.choices(term_values, weights=term_weights, k=1)[0]

        rate_center = (
            PRODUCT_RATE[product]
            + (700 - credit_score) * 0.014
            + SEGMENT_RATE_ADJ[segment]
            + rng.gauss(0, 0.65)
        )
        lower_rate, upper_rate = PRODUCT_RATE_BOUNDS[product]
        interest_rate = round(_clamp(rate_center, lower_rate, upper_rate), 2)

        days_ago = rng.randint(20, horizon_days)
        disbursement_date = as_of - timedelta(days=days_ago)
        maturity_date = _add_months(disbursement_date, term_months)
        age_months = _whole_months(disbursement_date, as_of)
        grade = _risk_grade(credit_score)

        grade_factor = {"A": 0.25, "B": 0.48, "C": 1.0, "D": 2.1, "E": 3.7}[grade]
        default_probability = _clamp(
            0.026 * grade_factor * PRODUCT_RISK[product] * (0.8 + age_months / 28),
            0.001,
            0.30,
        )
        matured = age_months >= term_months
        is_defaulted = False if matured else rng.random() < default_probability

        close_probability = _clamp(
            CLOSE_FACTOR[product] * (0.55 + age_months / 26),
            0.01,
            0.42,
        )
        is_closed = matured or (not is_defaulted and rng.random() < close_probability)

        if is_defaulted:
            dpd = rng.choices(
                [90, 105, 120, 150, 180, 240, 300, 365],
                weights=[0.18, 0.16, 0.16, 0.16, 0.14, 0.10, 0.07, 0.03],
                k=1,
            )[0]
            dpd += rng.randint(0, 9)
            default_date = as_of - timedelta(days=dpd)
            if default_date < disbursement_date:
                default_date = disbursement_date
                dpd = max(90, (as_of - default_date).days)
            balance = _balance_after_months(principal, interest_rate, term_months, age_months)
            outstanding = min(principal * 1.04, max(principal * 0.04, balance) * rng.uniform(1.0, 1.06))
            status = "Defaulted"
            last_payment_date = default_date - timedelta(days=rng.randint(3, 28))
            next_due_date = None
            closed_date = None
        elif is_closed:
            status = "Closed"
            dpd = 0
            outstanding = 0.0
            if matured:
                closed_date = maturity_date
            else:
                earliest = _add_months(disbursement_date, min(6, term_months))
                span = max(1, (as_of - earliest).days)
                closed_date = earliest + timedelta(days=rng.randint(0, span))
                closed_date = min(closed_date, as_of)
            last_payment_date = closed_date
            next_due_date = None
            default_date = None
        else:
            status = "Active"
            balance = _balance_after_months(principal, interest_rate, term_months, age_months)
            delinquency_probability = {
                "A": 0.030, "B": 0.045, "C": 0.080, "D": 0.135, "E": 0.200
            }[grade] * PRODUCT_RISK[product]
            if rng.random() < delinquency_probability:
                dpd = rng.choices(
                    [1, 8, 15, 25, 32, 45, 60, 75, 88],
                    weights=[0.15, 0.16, 0.16, 0.16, 0.12, 0.10, 0.07, 0.05, 0.03],
                    k=1,
                )[0]
                dpd += rng.randint(0, 1)
                balance *= 1 + min(dpd, 90) / 2_500
                last_payment_date = as_of - timedelta(days=dpd + rng.randint(0, 12))
                if last_payment_date < disbursement_date:
                    last_payment_date = disbursement_date
            else:
                dpd = 0
                last_payment_date = as_of - timedelta(days=rng.randint(0, 28))
            outstanding = min(principal, max(0.0, balance))
            next_due_date = as_of + timedelta(days=rng.randint(2, 30))
            default_date = None
            closed_date = None

        monthly_payment = round(_monthly_payment(principal, interest_rate, term_months), 2)
        purpose = rng.choice(PURPOSES[product])
        branch = rng.choice(BRANCHES)

        rows.append(
            {
                "loan_id": f"LN-{index:05d}",
                "customer_id": customer_id,
                "loan_type": product,
                "principal_amount": round(principal, 2),
                "outstanding_balance": round(max(0.0, outstanding), 2),
                "interest_rate": interest_rate,
                "term_months": term_months,
                "monthly_payment": monthly_payment,
                "disbursement_date": disbursement_date.isoformat(),
                "maturity_date": maturity_date.isoformat(),
                "status": status,
                "days_past_due": int(dpd),
                "risk_grade": grade,
                "purpose": purpose,
                "branch": branch,
                "collateral_type": COLLATERAL[product],
                "last_payment_date": last_payment_date.isoformat() if last_payment_date else None,
                "next_due_date": next_due_date.isoformat() if next_due_date else None,
                "default_date": default_date.isoformat() if default_date else None,
                "closed_date": closed_date.isoformat() if closed_date else None,
            }
        )

    return pd.DataFrame(rows)


def generate_snapshots(
    loans: pd.DataFrame,
    months: int = 18,
    as_of: date | None = None,
) -> pd.DataFrame:
    """Build monthly month-end snapshots used by the overdue-trend chart."""
    as_of = as_of or date.today()
    snapshot_dates: list[date] = []
    cursor = _previous_month_end(as_of)
    for _ in range(months):
        snapshot_dates.append(cursor)
        cursor = _previous_month_end(cursor)
    snapshot_dates.reverse()

    rows: list[dict] = []
    for loan in loans.itertuples(index=False):
        disbursed = date.fromisoformat(loan.disbursement_date)
        closed = date.fromisoformat(loan.closed_date) if loan.closed_date else None
        defaulted = date.fromisoformat(loan.default_date) if loan.default_date else None
        current_dpd = int(loan.days_past_due)

        for snapshot_date in snapshot_dates:
            if disbursed > snapshot_date:
                continue
            if closed is not None and closed <= snapshot_date:
                continue

            elapsed = _whole_months(disbursed, snapshot_date)
            balance = _balance_after_months(
                float(loan.principal_amount),
                float(loan.interest_rate),
                int(loan.term_months),
                elapsed,
            )
            if balance <= 0.01:
                continue

            if loan.status == "Defaulted" and defaulted is not None and snapshot_date >= defaulted:
                dpd_at_snapshot = max(90, min(current_dpd, (as_of - snapshot_date).days + 30))
                status_at_snapshot = "Defaulted"
            elif loan.status == "Defaulted":
                dpd_at_snapshot = 0
                status_at_snapshot = "Active"
            elif loan.status == "Active" and current_dpd > 0:
                months_ago = (as_of.year - snapshot_date.year) * 12 + (as_of.month - snapshot_date.month)
                dpd_at_snapshot = max(0, current_dpd - months_ago * 11)
                status_at_snapshot = "Active"
            else:
                dpd_at_snapshot = 0
                status_at_snapshot = "Active"

            rows.append(
                {
                    "snapshot_date": snapshot_date.isoformat(),
                    "loan_id": loan.loan_id,
                    "outstanding_balance": round(balance, 2),
                    "days_past_due": int(dpd_at_snapshot),
                    "status": status_at_snapshot,
                }
            )

    return pd.DataFrame(rows)


def generate_dataset(
    n_customers: int = 900,
    n_loans: int = 1_600,
    seed: int = 42,
    as_of: date | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Return ``(customers, loans, snapshots)`` ready for SQLite persistence."""
    as_of = as_of or date.today()
    customers = generate_customers(n_customers=n_customers, seed=seed)
    loans = generate_loans(customers, n_loans=n_loans, seed=seed, as_of=as_of)
    snapshots = generate_snapshots(loans, as_of=as_of)
    return customers, loans, snapshots
