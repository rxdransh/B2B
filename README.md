# GTM Lead Qualification & Revenue Pipeline System

A polished, local B2B CRM and revenue operations dashboard built with Python, Streamlit, Pandas, SQLite, and Plotly.

## Problem statement

Early-stage sales teams often keep leads in disconnected spreadsheets. That makes it difficult to judge lead quality, understand where prospects sit in the funnel, follow up on time, and estimate the revenue that may close.

## Solution

This B2B brings lead capture, rule-based qualification, funnel tracking, follow-up prioritisation, pipeline visibility, and revenue analytics into one small internal tool. It is deliberately simple enough to explain in an interview while still modelling realistic CRM and RevOps workflows.

## Key features

- Live dashboard with six database-driven KPIs
- Searchable and filterable CRM lead table
- Transparent rule-based lead scoring and Hot/Warm/Cold classification
- Lead detail view with the complete score explanation
- Editable GTM and sales stages
- Open-pipeline tracking by stage and deal value
- Automated follow-up queue for leads inactive for more than two days
- One-click “Mark contacted” workflow
- Lead source, conversion, revenue, pipeline, and temperature analytics
- Automatic SQLite setup with 50 realistic fictional demo leads

## Tech stack

- **Python** — application language and business logic
- **Streamlit** — multipage-style user interface and forms
- **SQLite** — local persistent CRM database
- **Pandas** — filtering, grouping, and business metric calculations
- **Plotly** — interactive charts

No external services, APIs, authentication systems, machine learning models, or cloud infrastructure are required.

## CRM and GTM concepts demonstrated

The product follows a practical revenue workflow:

```text
Business Problem
       ↓
Lead Capture
       ↓
Lead Qualification
       ↓
Lead Scoring
       ↓
GTM Funnel
       ↓
Sales Pipeline
       ↓
Follow-up Management
       ↓
Revenue Analytics
```

- **Lead qualification** helps sales teams spend time on prospects with stronger buying signals.
- **CRM stages** create a shared definition of where each buyer is in the sales journey.
- **Follow-up tracking** prevents high-value leads from going inactive and simulates a simple sales SLA.
- **Pipeline analytics** helps a revenue team estimate open deal value, find bottlenecks, and compare acquisition sources.

## Lead scoring logic

Scoring is deterministic and intentionally transparent. `calculate_lead_score()` in `scoring.py` awards points for four business signals:

| Signal | Rule | Points |
|---|---|---:|
| Company size | Under 50 / 50–199 / 200–499 / 500+ | 5 / 10 / 20 / 30 |
| Buyer role | CEO or Founder / CTO or CIO / VP / Director / Manager / Other | 25 / 25 / 20 / 15 / 10 / 5 |
| Budget | Under ₹50k / ₹50k–₹1L / ₹1L–₹5L / Over ₹5L | 5 / 10 / 20 / 25 |
| Lead source | Demo / Referral / LinkedIn or Webinar / Website / Cold or Email | 20 / 15 / 10 / 8 / 5 |

The result is capped at 100 and mapped to:

- **Hot:** 80–100
- **Warm:** 50–79
- **Cold:** 0–49

The Lead Details page shows the exact points behind every lead's score.

## GTM funnel

```text
New Lead → MQL → SQL → Opportunity → Closed Won / Closed Lost
```

Open pipeline value includes only **MQL**, **SQL**, and **Opportunity** records. Won revenue includes only **Closed Won** records. Dashboard conversion rate is Closed Won deals divided by all leads.

## Database structure

The app creates `crm.db` automatically on first run. The `leads` table contains:

| Group | Fields |
|---|---|
| Identity | `id`, `name`, `email`, `phone` |
| Company | `company`, `industry`, `job_title`, `company_size` |
| Qualification | `lead_source`, `budget`, `lead_score`, `temperature` |
| Pipeline | `gtm_stage`, `sales_stage`, `deal_value` |
| Activity | `last_contacted`, `created_at` |

All inserts and updates use parameterized SQL. Demo data is seeded only when the table is empty, so restarting the app does not duplicate records.

## How to run

From this project directory:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
streamlit run app.py
```

Open the local URL shown by Streamlit, normally `http://localhost:8501`.

To reset the demo database, stop Streamlit, delete `crm.db`, and start the app again. A fresh database and 50 demo leads will be created automatically.

## Example workflow

1. Open **Dashboard** to inspect current lead, pipeline, revenue, and follow-up KPIs.
2. Go to **Add Lead** and enter buyer, company, budget, and source data.
3. Review the automatically calculated score and temperature.
4. Open **Lead Details** to see why the score was awarded and update funnel stages.
5. Check **Follow-ups** for leads inactive for more than two days and mark one as contacted.
6. Use **Analytics** to compare lead sources, funnel conversion, industry revenue, and pipeline mix.

## Project structure

```text
B2B/
├── .streamlit/      # Stable light theme and local server defaults
├── app.py           # Streamlit UI and page workflows
├── analytics.py     # KPI, funnel, follow-up, and performance calculations
├── database.py      # SQLite schema and parameterized data access
├── scoring.py       # Explainable lead scoring rules
├── seed_data.py     # Deterministic fictional demo records
├── tests/            # Core workflow and UI smoke tests
├── requirements.txt
├── README.md
└── crm.db           # Created automatically on first run
```

## Future improvements

- Activity notes and a timeline per lead
- CSV import and export
- Pipeline targets and quota attainment
- Owner assignment and team-level reporting
- Configurable scoring rules and follow-up SLA
- Lightweight role-based access for a shared deployment

These are intentionally outside the current scope so the core CRM and RevOps workflow stays reliable and easy to understand.
