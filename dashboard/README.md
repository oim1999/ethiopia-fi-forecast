# Dashboard

Interactive Streamlit application for exploring the Ethiopia Financial Inclusion dataset,
trends, event impacts, and forecasts.

## Run locally

```bash
pip install -r ../requirements.txt
streamlit run app.py
```

Then open the URL Streamlit prints (typically `http://localhost:8501`).

## Pages

| Page | Contents |
|---|---|
| **Overview** | Summary metric cards (Account Ownership, Digital Payment Adoption, Mobile Money Account Rate, Gender Gap), P2P/ATM crossover ratio, growth highlights |
| **Trends** | Interactive time series with a date-range slider, multi-indicator comparison, event overlay toggle, and an operator channel-comparison view (M-Pesa registered vs. active, mobile money rate over time) |
| **Forecasts** | Access/Usage forecast selector, scenario multiselect (pessimistic/base/optimistic), trend-uncertainty-band toggle, forecast data table, and an event-impact ranking chart |
| **Inclusion Projections** | Scenario slider, progress bars toward the NFIS-II 70% Access target and Usage growth, a full target-vs-projection table, answers to the consortium's key questions, and strategic recommendations |

All four pages read from `data/processed/ethiopia_fi_unified_data_enriched.csv` and reuse
the exact modeling code from `src/impact_model.py` and `src/forecasting.py` — nothing is
recomputed or re-derived independently of the notebooks, so the dashboard's numbers always
match `notebooks/04_event_impact_modeling.ipynb` and `notebooks/05_forecasting.ipynb`.

## Testing

`tests/test_dashboard.py` uses Streamlit's `AppTest` harness to run every page's code path
headlessly and assert no exception is raised — see `../tests/`.

## Data download

The sidebar includes download buttons for the enriched dataset and both forecast tables
(CSV), so consortium members can take the numbers into their own tools.

## Screenshots

`[PLACEHOLDER: insert screenshots of each of the 4 pages here after running `streamlit run app.py`
locally — this environment's sandboxed network could not download a headless browser
(Playwright/Chromium) to capture them automatically. The app was verified to run
error-free on all 4 pages via `streamlit.testing.v1.AppTest` and HTTP health checks
instead — see `tests/test_dashboard.py`.]`
