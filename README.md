# Ethiopia Financial Inclusion Forecast

Forecasting system for Ethiopia's digital financial transformation, built for a consortium
of development finance institutions, mobile money operators, and the National Bank of
Ethiopia. The project tracks and forecasts two Global Findex pillars:

- **Access** — Account Ownership Rate (`ACC_OWNERSHIP`)
- **Usage** — Digital Payment Adoption (proxied via `USG_P2P_COUNT`, `ACC_MM_ACCOUNT`,
  `USG_TELEBIRR_USERS`, and related transaction indicators)


## Project Status

| Task | Description | Status |
|------|-------------|--------|
| 1 | Data Exploration & Enrichment | ✅ Complete (merged from `task-1`) |
| 2 | Exploratory Data Analysis | ✅ Complete (merged from `task-2`) |
| 3 | Event Impact Modeling | ✅ Complete |
| 4 | Forecasting Access & Usage | ✅ Complete |
| 5 | Dashboard Development | ✅ Complete |

## Data & Schema

This project uses a **unified schema**: every record (`observation`, `event`, `impact_link`,
`target`) lives in the same table and shares the same columns. The `record_type` column
determines how each row should be interpreted.

**Key design principle: events are not pre-assigned to pillars.** A launch like Telebirr
affects both Access and Usage; forcing it into one pillar would bias the analysis. Instead:

| Record Type | `category` | `pillar` |
|---|---|---|
| `observation` | empty | ✅ measured dimension |
| `target` | empty | ✅ goal dimension |
| `event` | ✅ event type (policy, product_launch, ...) | empty — no pre-assignment |
| `impact_link` | empty | ✅ pillar of the *affected* indicator |

`impact_link` records connect an `event` to an indicator via `parent_id` (the event's
`record_id`), capturing the estimated direction, magnitude, lag, and evidence basis of the
effect. See `data/raw/README.md` for the full schema documentation

## Repository Structure

```
ethiopia-fi-forecast/
├── data/
│   ├── raw/                  # Starter dataset + reference codes (as provided)
│   └── processed/            # Enriched dataset (analysis-ready)
├── notebooks/                # EDA and modeling notebooks
├── src/                      # Reusable Python modules (schema loading, helpers)
├── dashboard/                # Streamlit app
├── tests/                    # Unit tests
├── models/                   # Saved model artifacts (forecast task)
├── requirements.txt
└── data_enrichment_log.md    # Log of every record added in Task 1
```

## Setup

```bash
py -3.11 -m venv .venv
.venv\Scripts\activate
python.exe -m pip install --upgrade pip
pip install -r requirements.txt
```


## Running the dashboard (Task 5)

```bash
streamlit run dashboard/app.py
```

## Data Sources

- World Bank Global Findex Database (2011, 2014, 2017, 2021, 2024 rounds)
- National Bank of Ethiopia (NBE) publications
- Ethio Telecom / Telebirr press releases and reports
- Safaricom Ethiopia / M-Pesa press releases
- EthSwitch S.C.
- Fayda National ID Program (NIDP)
- GSMA State of the Industry Report on Mobile Money
- News coverage (Shega Media and other Ethiopia-focused outlets) used only for dating events,
  cross-referenced against operator/regulator sources where possible

Full source-by-source documentation for every enrichment record is in
`data_enrichment_log.md`.

## Branching Model

Each task is developed on its own branch (`task-1`, `task-2`, ...) and merged into `main`
via pull request once its deliverables are complete.
