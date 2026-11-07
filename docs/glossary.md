# Glossary

Terms used across the dashboard, code and documentation.

| Term | Meaning in Northstar |
|---|---|
| **Active** | A loan with `status = 'Active'`. It is open and not in the demo’s defaulted state. |
| **As-of date** | The date or reporting cutoff represented by a metric. Current KPIs use the current loan records; the delinquency trend uses completed month-end snapshots. |
| **Average DPD** | Arithmetic mean of `days_past_due` across non-closed loans, including current loans at zero. Unweighted by balance. |
| **Balance-based default rate** | Defaulted originated principal divided by total originated principal for the filtered population. |
| **Closed** | A loan whose principal has been fully settled. Outstanding balance is zero, and it is excluded from open balance and PAR metrics. |
| **Cohort** | A group of loans sharing a common characteristic, often origination period. The dashboard’s vintage chart uses disbursement quarter as the cohort key. |
| **Concentration** | The share of total open exposure represented by a subset, such as the top six borrowers or one product. |
| **Current book** | The share of open loans (by balance) that are not past due in the DPD bucket view. |
| **Default** | For this demo, a loan with `status = 'Defaulted'`, generally with `days_past_due >= 90`. This is a simplified business status, not a regulatory definition. |
| **Defaulted** | A loan with `status = 'Defaulted'`. It remains in the open portfolio and default metrics while it has outstanding balance. |
| **DPD** | Days past due. The number of days a scheduled payment is overdue. |
| **EAD** | Exposure at default. A credit-risk concept for the estimated exposure outstanding if a borrower defaults. Not calculated in this demo. |
| **ECL** | Expected credit loss. A provisioning measure combining PD, LGD and EAD with discounting and staging. Not calculated in this demo. |
| **Exposure** | In this demo, the current outstanding principal across a borrower, segment or product. |
| **Filtered population** | The set of loans remaining after the sidebar filters are applied. All current-book metrics use it unless stated otherwise. |
| **Loan type / product** | The product classification: Personal, Home, Auto, Education, Business, Equipment or Credit Card. |
| **Month-end snapshot** | A row in `portfolio_snapshots` representing a loan’s balance and DPD at a completed calendar month-end. |
| **Open loan** | A loan with `status != 'Closed'` in the dashboard’s current-book calculations. Active and defaulted loans are in scope. |
| **Origination** | The disbursement of a new loan. The dashboard’s date filter uses disbursement date. |
| **Outstanding balance** | Current unpaid principal, in USD, excluding accrued interest and fees in this demo. |
| **PAR** | Portfolio at Risk. Balance in a specified DPD band divided by open outstanding balance. The dashboard shows PAR 30+ and 90+ prominently. |
| **PD** | Probability of default. A credit-risk model output; not calculated by this demo. |
| **Point-in-time** | A view as it was at a historical date, including attributes and statuses at that date. The snapshot table approximates this for balances/DPD; customer segment and current loan status filters do not reconstruct a full point-in-time state. |
| **PortfolioFilters** | The immutable filter object used by every SQL query in the dashboard. |
| **Principal** | Original disbursed loan amount in this demo. |
| **Risk grade** | A demo A–E internal risk classification derived from synthetic credit score. |
| **Segment** | Customer segment: Retail, SME, Corporate or Premium. |
| **Snapshot grain** | One row per loan per completed month-end in `portfolio_snapshots`. |
| **SQLite WAL** | Write-ahead logging mode used by the database connection to improve concurrent read/write behavior. |
| **Status** | The current loan lifecycle status: Active, Closed or Defaulted. |
| **Vintage** | A loan cohort grouped by origination quarter. The default rate by vintage is an underwriting-quality proxy. |
| **Weighted average rate** | The sum of open outstanding multiplied by interest rate, divided by total open outstanding. |
