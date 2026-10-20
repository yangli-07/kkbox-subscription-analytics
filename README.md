# KKBOX Subscription Analytics

An evidence-first analytics project for exploring KKBOX subscription transactions with a reproducible local workflow. The project separates data review, sample preparation, transaction reconciliation, SQL aggregation, BI preparation, and a small Streamlit demonstration.

The work is intentionally scoped as a learning and portfolio project. Results are based on a development sample and should not be interpreted as platform-wide revenue, retention, or churn estimates.

## What this project demonstrates

- User-level sampling rather than random transaction-row sampling.
- Separate v1 and v2 transaction analysis with an explicit `source_version` field.
- Excel reconciliation using `COUNTIFS`, `SUMIFS`, and pivot tables.
- PostgreSQL table definitions, transaction profiles, and BI-oriented aggregate exports.
- A Streamlit dashboard that reads only aggregate CSV files.
- Deterministic question answering with explicit unsupported-data boundaries.

## Workflow

### 1. Data review and sample preparation

The project reviewed the available KKBOX files and documented fields, dates, missing values, version differences, and usage constraints. A fixed-seed user sample was prepared from `members_v3`; selected users retain their available transaction history. Large log processing and some full-population overlap checks remain outside the completed transaction branch.

v1 and v2 are analyzed separately. The project does not assume that the later v2 date means v2 is a complete replacement for v1, and it does not blindly append the two versions.

### 2. Excel reconciliation

The Excel workflow uses small, prepared CSV inputs rather than loading the original logs into a worksheet. It checks transaction counts, transaction-record amounts, duplicate rows, same-day multiple transactions, date anomalies, and version-specific monthly results.

The detailed steps are in [`docs/excel_steps.md`](docs/excel_steps.md). The repository does not publish the real-data Excel workbook or real processed-data files.

### 3. PostgreSQL and SQL aggregates

The SQL workflow is organized as:

1. [`sql/01_create_tables.sql`](sql/01_create_tables.sql) — creates separate v1/v2 transaction tables and supporting tables.
2. [`sql/02_transaction_profile.sql`](sql/02_transaction_profile.sql) — profiles transaction counts, distinct users, auto-renew flags, cancellation flags, and transaction-record amounts.
3. [`sql/03_export_bi_tables.sql`](sql/03_export_bi_tables.sql) — exports version-separated monthly, payment-plan, and version-profile aggregates.

The SQL export targets are under `data/processed/` for local use. That directory remains excluded from Git.

### 4. Tableau and Power BI

The planned BI workflow uses Tableau for exploratory retention/usage views and Power BI for operating summaries and renewal operations. v1/v2, sample scope, and observation windows must remain visible in the analysis.

The local project has Tableau and Power BI artifacts, but the public repository does not publish the Tableau workbook, Power BI file, original data, or real processed-data exports. Separate archival acceptance records are not included.

### 5. Streamlit

The application entry point is [`app/streamlit_app.py`](app/streamlit_app.py). It provides:

- v1/v2 selection;
- a selectable month range;
- monthly transaction-count, distinct-user-count, and transaction-record-amount charts;
- payment-plan summaries;
- version-level auto-renew and cancellation-flag summaries;
- a natural-language question area with deterministic answers.

The application reads only these three aggregate files in local SQL mode:

- `data/processed/sql_monthly_summary.csv`
- `data/processed/sql_payment_plan_summary.csv`
- `data/processed/sql_version_profile.csv`

It does not read `data/raw`, ZIP files, transaction detail, or user-level records.

## Public demo mode

The public demo uses independently generated simulated data in [`app/demo_data/`](app/demo_data/). These CSVs have the same aggregate field structures required by the app but are not copies of the real CSV values.

Start the app and select **模拟演示数据** in the sidebar under **数据模式**. The page displays the active data mode. If the local SQL aggregate files are unavailable, the app can still run in simulated-data mode.

Example questions to try:

- “Which version has more transaction records by month?”
- “What are the transaction-record amounts by payment plan?”
- “How do the auto-renewal record shares differ between v1 and v2?”
- “What does the cancellation-flag share show?”
- “Can this data determine real retention or churn?”

The default question answering is deterministic rule-based answering. The code contains an optional OpenAI integration path, but the public demo does not configure a key and does not call OpenAI. Unsupported questions are explicitly declined.

## Limitations and metric definitions

- `transaction_record_amount` is the sum of `actual_amount_paid` in transaction records. It is not net revenue and is not MRR.
- A cancellation flag is a transaction-level field. It does not directly represent real user churn.
- Real churn would require an appropriate expiration and post-expiration renewal observation window; the current aggregate files do not provide enough evidence for real churn classification.
- The current aggregate files do not support user-level retention, cohort retention, or log-based behavior analysis.
- Monthly distinct-user counts are separate monthly counts. Their sum is not the distinct-user count for the entire period.
- v1 and v2 remain separate; the project does not treat v2 as a complete historical replacement or blindly combine versions.
- The analysis is sample-based. It is suitable for workflow development and reconciliation, not direct extrapolation to the full platform.

## Project structure

```text
app/
  streamlit_app.py
  demo_data/                 # Independent simulated aggregate CSVs
docs/                        # Data, metric, workflow, and status documentation
sql/                         # Table definitions, profiles, and aggregate exports
src/                         # Streaming audit and transaction-sample scripts
data/raw/                    # Local original archive; excluded from Git
data/processed/              # Local processed/aggregate outputs; excluded from Git
excel/                       # Local Excel artifacts and inputs; not published
tableau/                     # Local Tableau artifacts; not published
powerbi/                     # Local Power BI artifacts; not published
```

## Installation and startup

From the project root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
streamlit run app/streamlit_app.py
```

No API key is required for the dashboard or deterministic question answering. Do not place secrets in source code or commit `.env`. If the optional OpenAI path is ever enabled for a private local run, configure credentials through environment variables and continue to send only the currently filtered aggregate data.

## Data and publication boundary

This public project does not include the original data, real processed-data exports, the real-data Excel workbook, the Tableau workbook, or the Power BI file. Public demonstrations should use `app/demo_data/` only. No claims of revenue improvement, churn reduction, retention performance, or causal impact are made.
