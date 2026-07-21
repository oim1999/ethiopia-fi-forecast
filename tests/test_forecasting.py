"""Unit tests for src/forecasting.py"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from data_loader import load_unified_data, get_observations, events_with_impacts  # noqa: E402
from forecasting import (  # noqa: E402
    fit_trend,
    predict_trend,
    heuristic_uncertainty_band,
    event_augmented_forecast,
    SCENARIO_DISCOUNTS,
)

DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "processed" / "ethiopia_fi_unified_data_enriched.csv"


@pytest.fixture(scope="module")
def acc_obs():
    df = load_unified_data(DATA_PATH)
    obs = get_observations(df)
    return obs[(obs["indicator_code"] == "ACC_OWNERSHIP") & (obs["gender"] == "all") & (obs["record_type"] == "observation")]


@pytest.fixture(scope="module")
def ei():
    df = load_unified_data(DATA_PATH)
    return events_with_impacts(df)


def test_fit_trend_linear_runs(acc_obs):
    model, data = fit_trend(acc_obs, kind="linear")
    assert model.params["x"] > 0  # account ownership is rising
    assert 0 <= model.rsquared <= 1


def test_fit_trend_log_better_fit_than_linear(acc_obs):
    lin_model, _ = fit_trend(acc_obs, kind="linear")
    log_model, _ = fit_trend(acc_obs, kind="log")
    # The EDA found decelerating growth; the log trend should fit at least as well
    assert log_model.rsquared >= lin_model.rsquared - 1e-6


def test_fit_trend_invalid_kind_raises(acc_obs):
    with pytest.raises(ValueError):
        fit_trend(acc_obs, kind="quadratic")


def test_predict_trend_monotonic_for_positive_slope(acc_obs):
    model, _ = fit_trend(acc_obs, kind="linear")
    years = np.array([2025.5, 2026.5, 2027.5])
    summary = predict_trend(model, years)
    assert summary["mean"].is_monotonic_increasing


def test_heuristic_uncertainty_band_symmetric():
    point = pd.Series([40.0, 45.0], index=[2025, 2026])
    band = heuristic_uncertainty_band(point, relative_width=0.2)
    assert np.allclose(band["obs_ci_lower"], point * 0.8)
    assert np.allclose(band["obs_ci_upper"], point * 1.2)
    assert (band["obs_ci_lower"] < band["mean"]).all()
    assert (band["obs_ci_upper"] > band["mean"]).all()


def test_event_augmented_forecast_scenario_ordering(acc_obs, ei):
    model, _ = fit_trend(acc_obs, kind="log")
    years = np.array([2025.9, 2026.9, 2027.9])
    trend_summary = predict_trend(model, years)
    last_obs_date = acc_obs["observation_date"].max()
    forecast_dates = pd.to_datetime(["2025-11-29", "2026-11-29", "2027-11-29"])
    result = event_augmented_forecast(trend_summary, ei, "ACC_OWNERSHIP", last_obs_date, forecast_dates)

    # pessimistic <= base <= optimistic at every horizon, since discounts are increasing
    assert (result["pessimistic"] <= result["base"] + 1e-9).all()
    assert (result["base"] <= result["optimistic"] + 1e-9).all()
    # pessimistic scenario (0 discount) should equal the trend itself
    assert np.allclose(result["pessimistic"], result["trend"])


def test_scenario_discounts_are_ordered():
    assert SCENARIO_DISCOUNTS["pessimistic"] < SCENARIO_DISCOUNTS["base"] < SCENARIO_DISCOUNTS["optimistic"]
