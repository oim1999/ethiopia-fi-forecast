"""Unit tests for src/impact_model.py"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from data_loader import load_unified_data, events_with_impacts  # noqa: E402
from impact_model import (  # noqa: E402
    ramp_fraction,
    effect_pp,
    build_association_matrix,
    project_indicator_effect,
    calibrate_magnitude_mapping,
)

DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "processed" / "ethiopia_fi_unified_data_enriched.csv"


@pytest.fixture(scope="module")
def ei():
    df = load_unified_data(DATA_PATH)
    return events_with_impacts(df)


def test_ramp_fraction_zero_before_event():
    assert ramp_fraction(-5, 12) == 0.0
    assert ramp_fraction(0, 12) == 0.0


def test_ramp_fraction_half_at_lag():
    frac = ramp_fraction(12, 12)
    assert abs(frac - 0.5) < 1e-6


def test_ramp_fraction_monotonic_increasing():
    lags = [ramp_fraction(m, 12) for m in range(0, 48, 6)]
    assert all(x <= y for x, y in zip(lags, lags[1:]))


def test_effect_pp_uses_impact_estimate_when_present():
    row = pd.Series({"impact_direction": "increase", "impact_estimate": 7.5, "impact_magnitude": "low"})
    assert effect_pp(row) == 7.5


def test_effect_pp_falls_back_to_magnitude_map():
    row = pd.Series({"impact_direction": "decrease", "impact_estimate": np.nan, "impact_magnitude": "medium"})
    val = effect_pp(row, magnitude_map={"low": 2, "medium": 6, "high": 15})
    assert val == -6


def test_calibrate_magnitude_mapping_returns_all_buckets(ei):
    renamed = ei.rename(columns={"impact_impact_magnitude": "impact_magnitude", "impact_impact_estimate": "impact_estimate"})
    mapping = calibrate_magnitude_mapping(renamed)
    assert set(mapping.keys()) >= {"low", "medium", "high"}
    assert mapping["high"] > mapping["medium"] > mapping["low"] > 0


def test_build_association_matrix_shape(ei):
    matrix = build_association_matrix(ei)
    assert matrix.shape[0] > 0 and matrix.shape[1] > 0
    # Telebirr Launch should have a non-null entry for at least one indicator
    assert matrix.loc["Telebirr Launch"].notna().any()


def test_project_indicator_effect_zero_before_any_event(ei):
    dates = pd.date_range("2010-01-01", "2010-06-01", freq="MS")
    eff = project_indicator_effect(ei, "ACC_OWNERSHIP", dates)
    assert (eff == 0).all()


def test_project_indicator_effect_nonzero_after_events(ei):
    dates = pd.date_range("2024-01-01", "2025-12-01", freq="MS")
    eff = project_indicator_effect(ei, "ACC_OWNERSHIP", dates)
    assert eff.iloc[-1] > 0
