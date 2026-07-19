"""Unit tests for src/data_loader.py"""

import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from data_loader import (  # noqa: E402
    get_events,
    get_impact_links,
    get_observations,
    load_reference_codes,
    load_unified_data,
    validate_against_reference,
    events_with_impacts,
)

DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "processed" / "ethiopia_fi_unified_data_enriched.csv"
RAW_DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "raw" / "ethiopia_fi_unified_data.csv"
REF_PATH = Path(__file__).resolve().parents[1] / "data" / "raw" / "reference_codes.csv"


def _data_path():
    """Prefer the enriched dataset once it exists; fall back to raw."""
    return DATA_PATH if DATA_PATH.exists() else RAW_DATA_PATH


def test_load_unified_data_returns_dataframe():
    df = load_unified_data(_data_path())
    assert isinstance(df, pd.DataFrame)
    assert len(df) > 0


def test_load_unified_data_missing_file_raises():
    with pytest.raises(FileNotFoundError):
        load_unified_data("data/raw/does_not_exist.csv")


def test_record_type_values_are_valid():
    df = load_unified_data(_data_path())
    assert set(df["record_type"].dropna().unique()) <= {
        "observation", "event", "impact_link", "target", "baseline", "forecast"
    }


def test_load_reference_codes():
    ref = load_reference_codes(REF_PATH)
    assert {"field", "code"}.issubset(ref.columns)
    assert len(ref) > 0


def test_validate_against_reference_no_issues():
    df = load_unified_data(_data_path())
    ref = load_reference_codes(REF_PATH)
    issues = validate_against_reference(df, ref)
    assert issues == {}, f"Dataset has values outside reference_codes: {issues}"


def test_get_observations_only_observation_and_target():
    df = load_unified_data(_data_path())
    obs = get_observations(df)
    assert set(obs["record_type"].unique()) <= {"observation", "target"}


def test_get_events_pillar_is_empty():
    df = load_unified_data(_data_path())
    events = get_events(df)
    # README design principle: events must NOT be pre-assigned a pillar
    assert events["pillar"].isna().all(), "Events should not have a pillar pre-assigned"


def test_get_impact_links_have_parent_id():
    df = load_unified_data(_data_path())
    impacts = get_impact_links(df)
    assert impacts["parent_id"].notna().all(), "Every impact_link must reference a parent event"


def test_events_with_impacts_join_is_nonempty():
    df = load_unified_data(_data_path())
    merged = events_with_impacts(df)
    assert len(merged) == len(get_impact_links(df))
    assert merged["event_record_id"].notna().all()
