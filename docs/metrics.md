# Metrics and analytics

This document defines every metric shown in the dashboard: its numerator, denominator, grain and intended interpretation. Definitions matter more than formatting — two views can show different percentages while both being mathematically correct if they use different bases.

All metrics are calculated from the selected portfolio and are expressed in USD unless stated otherwise.

---

## Reporting basis

| Question | Current answer |
|---|---|
| As-of date for current metrics | The current loan records, displayed as today’s date in the page header |
| As-of date for overdue trend | Latest completed month-end snapshot, displayed in the chart header |
| Date filter | Loan `disbursement_date`, inclusive both ends |
| Currency | USD |
| Portfolio scope | All products, statuses and segments unless the sidebar is narrowed |
| Empty multi-select | No restriction (all values) |
| Closed loans in balances? | No |
| Defaulted loans in open balances? | Yes |
| Data freshness | Immediate for current records; latest month-end for snapshot trend |

The app displays an “as of” date at the page level. The snapshot chart displays its own latest snapshot date so the two reporting bases cannot be confused.

---

## Primary KPI definition

```text
Total loans          = COUNT(*) over filtered loans
Customers            = COUNT(DISTINCT customer_id) over filtered loans
Total principal      = Σ principal_amount over filtered loans
Outstanding balance  = Σ outstanding_balance where status ≠ 'Closed'
```

Notes:

- Total loans includes closed and defaulted loans because they are part of the selected historical book.
- Customers count distinct borrowers with at least one loan in the filtered population.
- Outstanding balance excludes closed loans, whose generated balance should be zero.
- Originated capital is the denominator used for outstanding ratio and balance-based default rate.

### Total loans

Shown in the top KPI rail and the page header.

```text
count(all filtered loans)
```

The supporting text shows borrower count and active share. The header count uses the same filtered population.

### Outstanding balance

```text
Σ outstanding_balance for filtered loans where status ≠ 'Closed'
```

The KPI detail shows **outstanding ratio**:

```text
outstanding balance / Σ principal_amount × 100
```

A low ratio can reflect either a seasoned book or a portfolio with many closed loans; compare it with origination volume and loan age rather than using it as a quality score.

### Overdue loans

```text
COUNT(filtered loans where status ≠ 'Closed' AND days_past_due > 0)
```

The KPI detail adds:

- **Overdue balance** — `Σ outstanding_balance` for the same loans.
- **Overdue rate** — `overdue balance / outstanding balance × 100`.

Overdue includes any non-closed loan with a positive DPD, including defaulted loans. It is not a count of payments missed.

### Default rate

The headline KPI uses a **count-based** rate:

```text
default rate = defaulted loans / total filtered loans × 100
```

The supporting text shows the **balance-based** rate:

```text
default rate by balance = Σ principal_amount of defaulted loans
                        / Σ principal_amount of all filtered loans × 100
```

Why show both? A single large default and many small defaults can produce very different count and balance rates. The count rate answers “how many loans?”; the balance rate answers “how much originated capital is represented by defaults?”. Neither is universally “the” default rate.

**Demo caveat:** this is a status-based default rate, not a regulatory default-rate model calibrated over a performance window.

---

## Delinquency and risk metrics

### DPD buckets

Open loans are categorized as:

| Bucket | Condition |
|---|---|
| Current | `days_past_due = 0` |
| 1–29 days | `1 <= days_past_due <= 29` |
| 30–59 days | `30 <= days_past_due <= 59` |
| 60–89 days | `60 <= days_past_due <= 89` |
| 90+ days | `days_past_due >= 90` |

The Risk & delinquency tab visualizes loan counts by bucket; the Overview credit-quality panel visualizes the past-due **balance** composition.

### Portfolio at Risk (PAR)

```text
PAR 30+ balance = Σ outstanding_balance
                  where status ≠ 'Closed' and days_past_due >= 30

PAR 30+ rate = PAR 30+ balance / outstanding balance × 100
```

PAR 60+ and PAR 90+ follow the same pattern with thresholds of 60 and 90 days. The KPI rail shows PAR 30+ and 90+ DPD exposure; the underlying KPI calculation also includes PAR 60+.

PAR rates are balance-weighted and use the same open-book denominator as the headline outstanding balance.

### Weighted average interest rate

```text
weighted average rate = Σ(open outstanding × interest_rate)
                        / Σ(open outstanding)
```

This is a balance-weighted current portfolio yield proxy, not a contractual yield-to-maturity and not an interest income calculation. It excludes closed loans.

### Average days past due

```text
average DPD = AVG(days_past_due) across non-closed filtered loans
```

The average includes current loans at DPD 0. It is unweighted by balance, so a small number of heavily delinquent loans can be diluted by a large number of current loans. Use the PAR metrics and DPD bucket distribution for severity; use average DPD as a directional onboarding indicator.

### Credit quality panel

The Overview credit-quality panel shows:

- **PAR 30+ rate** and **90+ DPD exposure**.
- **Past-due balance composition** by DPD bucket:
  ```text
  bucket share = bucket outstanding_balance
                 / Σ outstanding_balance for non-current buckets × 100
  ```
- The leading past-due bucket and its share.
- **Current book share**:
  ```text
  current bucket outstanding / all open outstanding × 100
  ```
- The balance-weighted average rate in the footer.

This is a view of where overdue dollars sit, not a migration matrix.

---

## Segment and risk-grade analytics

### Segment summary

For each customer segment in the filtered population:

| Field | Definition |
|---|---|
| `loan_count` | Count of filtered loans |
| `customer_count` | Distinct customers with filtered loans |
| `outstanding_balance` | Σ open outstanding |
| `overdue_balance` | Σ outstanding for open loans with DPD > 0 |
| `overdue_loans` | Count of open loans with DPD > 0 |
| `defaulted_loans` | Count of status = Defaulted |
| `defaulted_principal` | Σ principal of defaulted loans |
| `default_rate` | defaulted_principal / total_principal × 100 |
| `par30_balance` | Σ outstanding for open loans with DPD >= 30 |
| `par30_rate` | par30_balance / outstanding_balance × 100 |
| `overdue_rate` | overdue_balance / outstanding_balance × 100 |
| `avg_rate` | Average `interest_rate` on open loans, unweighted |
| `avg_dpd` | Average DPD on open loans, unweighted |

The dashboard table uses “Default” for the balance-based default rate. A segment with a higher count of defaults may not be the segment with the highest balance-based default rate.

### Risk grade

For each credit grade A–E:

```text
default rate = Σ principal_amount of defaulted loans
               / Σ principal_amount of all loans in that grade × 100
```

The risk-grade chart is balance-weighted. The underlying query also returns loan counts, outstanding balance, PAR 30+ and average DPD by grade for future views.

Grade is assigned from the customer’s synthetic credit score group in the demo. It is a transparent illustration of credit-quality dispersion, not a real rating model.

### Segment risk table

The Risk tab’s compact table shows, by segment:

- PAR 30+ (balance-weighted);
- default rate (balance-weighted);
- average DPD.

Values at or above the presentation thresholds receive warning or risk emphasis. Those thresholds are visual cues; they are not regulatory classifications.

---

## Origination and mix analytics

### Monthly originations

```text
month = month of disbursement_date
loan_count = count of loans disbursed in the month
disbursed_amount = Σ principal_amount
outstanding_balance = Σ current open balance of those loans
defaulted_loans = count of those loans that are now Defaulted
```

Closed loans remain in the historical origination count and disbursed amount. The chart gets its data from `get_monthly_originations`, and the dashboard fills months with no originations with zeros for continuity.

### Product allocation

```text
product share = Σ open outstanding for product
                / Σ open outstanding across all products × 100
```

The allocation panel is sorted by outstanding balance. It shows product-level current balance share, not origination share or loan count.

### Top borrower exposures

```text
borrower exposure = Σ open outstanding_balance
                    grouped by customer_id
```

The Overview shows six borrowers by default (`limit=6`). The SQL also returns each borrower’s:

- segment and relationship manager;
- number of loans;
- maximum DPD;
- number of defaulted loans.

The footer shows top-borrower concentration as a share of total open balance.

---

## Vintage analytics

The vintage chart groups loans by **disbursement quarter**:

```text
vintage = YYYY-Qn derived from disbursement_date

vintage default rate = Σ principal_amount of defaulted loans in the vintage
                       / Σ principal_amount of all loans in the vintage × 100
```

The UI removes the current, incomplete quarter so that partial-quarter originations do not create a misleading final data point. This choice is explicit in `app.py`.

Vintage analysis is a proxy for underwriting quality, but observed default rate is confounded by:

- loan age and maturity;
- product mix and collateral;
- repayment history;
- the state of the economy;
- definition of default;
- collection and recovery performance.

It should not be read as a full vintage loss curve. A production model would use observed defaults by months-on-book and recoveries.

---

## Portfolio health metrics in the risk panel

The Overview risk panel combines several bases:

| Display | Basis |
|---|---|
| PAR 30+ | Open balance, DPD ≥ 30 |
| 90+ DPD exposure | Open balance, DPD ≥ 90 |
| Past-due composition | Outstanding balance of overdue buckets only |
| Current book | Current bucket / total open balance |
| Weighted rate | Open balance weighted |
| Insight | Highest-balance overdue bucket share |

These differing denominators are intentional. For example, “90+ days = 40%” in the past-due composition means 40% of overdue balance, not 40% of the portfolio.

The card always shows the numerator context in the header and legend so the denominator can be inferred.

---

## Data-quality metrics

The Data quality workspace reports:

```text
checks run   = number of checks
passed       = checks with zero findings
review       = checks with > 0 findings
score        = passed / checks_run × 100
critical issues = Σ issue counts for checks marked Critical
rows scanned = customers + loans + portfolio_snapshots
```

Quality checks run against the complete database, independent of sidebar filters.

The completeness scan reports, for every field:

```text
missing = null or blank values
completeness = (1 - missing / row_count) × 100
```

Critical fields are flagged. Optional lifecycle dates are expected to be blank for some records; a low completeness percentage for `default_date` is not necessarily a defect.

---

## Query catalogue

The SQL layer lives in [`queries.py`](../loan_dashboard/queries.py). All functions accept a `PortfolioFilters` object (except helpers that enumerate options) and a database path.

| Function | Result grain | Primary fields |
|---|---|---|
| `get_filter_options` | One row per option/date bounds | Filter domains and counts |
| `get_kpis` | One row | All KPI numerators and denominators |
| `get_monthly_originations` | Month | Count, disbursed, current outstanding, defaults |
| `get_portfolio_mix` | Product | Count, principal, outstanding, defaults, avg rate, share |
| `get_status_mix` | Status | Count, principal, outstanding |
| `get_overdue_trend` | Snapshot month | Total, overdue, PAR 30, overdue count, loan count |
| `get_dpd_buckets` | DPD bucket | Count, outstanding, principal |
| `get_segment_performance` | Customer segment | Exposure, overdue, defaults, PAR, avg rate/DPD |
| `get_risk_grade_performance` | Risk grade | Count, outstanding, defaults, PAR, avg DPD |
| `get_quarterly_vintage` | Origination quarter | Count, principal, defaults, default rate |
| `get_top_exposures` | Customer | Loan count, exposure, max DPD, default count |
| `get_loans_table` | Loan | Loan-level detail for explorer/export |

### Query SQL patterns

- Every filter value is a bound parameter.
- The filter fields are allow-listed in code; user values do not become SQL fragments.
- Month groupings use `strftime()`.
- The snapshot trend joins `portfolio_snapshots` to `loan_details`.
- The app removes the current vintage quarter after querying.
- The app uses `limit=6` for the exposure panel even though `get_top_exposures` defaults to 8.

A typical filtered pattern:

```sql
SELECT
    COALESCE(SUM(d.outstanding_balance), 0) AS outstanding,
    COALESCE(SUM(CASE WHEN d.days_past_due >= 30
                      THEN d.outstanding_balance ELSE 0 END), 0) AS par30
FROM loan_details AS d
WHERE 1 = 1
  AND d.disbursement_date >= ?
  AND d.loan_type IN (?, ?)
  AND d.status IN (?);
```

---

## Presentation versus calculation

Raw values remain numeric in the query outputs. The UI formats them with:

- compact currency (`$156.5M`);
- percent labels with one or two decimals;
- formatted dates (`08 Nov 2026`);
- integer grouping.

Formatting does not alter exported CSVs or underlying values. The summary export writes raw numeric values with metric names.

---

## Interpretation caveats

Use these guardrails when presenting metrics:

1. **Do not mix bases.** State whether a rate is count-based or balance-based, and whether the denominator includes closed loans.
2. **Closed loans still matter** for historical origination and total principal, but are excluded from open balance and PAR denominators.
3. **Overdue is not default.** A positive DPD is an early-stage delinquency signal; the demo’s default status starts at 90+ DPD.
4. **Default rate is not expected loss.** There is no PD, LGD, EAD, staging, discounting or recovery in this demo.
5. **Vintage rate is not a full loss curve.** Use observed transitions and months-on-book in a real model.
6. **Average DPD is unweighted.** Pair it with PAR and bucket counts.
7. **Snapshot filters use current attributes.** Historical point-in-time segmentation or status filtering requires a different data mart.
8. **Synthetic relationships are directional.** The generator creates plausible correlations, not statistically validated ones.
9. **No seasonality, macro scenarios or stress paths** are modelled.
10. **All amounts are USD.** Multi-currency and FX translation are out of scope.

---

## Adding a metric safely

The recommended sequence for a new metric:

1. Define the grain and denominator in this document first.
2. Implement the calculation in `queries.py` as a parameterized query.
3. Add a unit test that asserts the filtered numerator/denominator relationship.
4. Add a presentation function or chart builder; keep formatting separate.
5. Confirm behavior with no rows, closed loans only and a single filtered segment.
6. If exposed in CSV, define whether the export contains raw or formatted values.
7. If used externally, annotate whether it contains PII or is a regulatory metric.

---

## Related documentation

- [Data model](data-model.md)
- [Architecture](architecture.md)
- [User guide](user-guide.md)
- [Implementation guide](implementation-guide.md)
