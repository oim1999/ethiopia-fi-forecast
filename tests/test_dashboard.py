"""Smoke tests for dashboard/app.py using Streamlit's AppTest harness.

These don't assert on visual layout (AppTest can't render pixels), but they do exercise
every page's Python code path end-to-end against the real enriched dataset and fail loudly
if any page raises an exception - the most common way a Streamlit app silently breaks.
"""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
APP_PATH = ROOT / "dashboard" / "app.py"

streamlit_testing = pytest.importorskip("streamlit.testing.v1")
AppTest = streamlit_testing.AppTest

PAGES = ["Overview", "Trends", "Forecasts", "Inclusion Projections"]


@pytest.mark.parametrize("page_name", PAGES)
def test_page_runs_without_exception(page_name):
    at = AppTest.from_file(str(APP_PATH))
    at.run(timeout=45)
    assert not at.exception, f"Overview (initial) page raised: {at.exception}"

    if page_name != "Overview":
        at.radio[0].set_value(page_name).run(timeout=45)
    assert not at.exception, f"{page_name} page raised: {at.exception}"


def test_overview_shows_key_metrics():
    at = AppTest.from_file(str(APP_PATH))
    at.run(timeout=45)
    assert len(at.metric) >= 4, "Overview page should show at least 4 summary metric cards"


def test_forecasts_page_has_scenario_selector():
    at = AppTest.from_file(str(APP_PATH))
    at.run(timeout=45)
    at.radio[0].set_value("Forecasts").run(timeout=45)
    assert len(at.multiselect) >= 1, "Forecasts page should expose a scenario multiselect"
