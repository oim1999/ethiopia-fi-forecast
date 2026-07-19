"""
data_loader.py

Reusable helpers for loading and validating the Ethiopia Financial Inclusion
unified dataset. Centralizing this logic keeps notebooks clean and ensures
every task (EDA, impact modeling, forecasting, dashboard) reads the data the
same way.

Unified schema recap
---------------------
Every row is one of four record_type values:
    - observation : a measured value (pillar is set, category is empty)
    - target       : an official policy goal (pillar is set, category is empty)
    - event        : a policy/product/market event (category is set, pillar is
                      intentionally left empty -- see README for rationale)
    - impact_link  : a modeled effect of an event on an indicator, linked via
                      parent_id -> event.record_id (pillar is set to the
                      pillar of the *affected* indicator)
"""

from pathlib import Path
import pandas as pd

# Columns that should always exist in the unified table.
REQUIRED_COLUMNS = [
    "record_id", "parent_id", "record_type", "category", "pillar",
    "indicator", "indicator_code", "indicator_direction", "value_numeric",
    "value_text", "value_type", "unit", "observation_date", "period_start",
    "period_end", "fiscal_year", "gender", "location", "region",
    "source_name", "source_type", "source_url", "confidence",
    "related_indicator", "relationship_type", "impact_direction",
    "impact_magnitude", "impact_estimate", "lag_months", "evidence_basis",
    "comparable_country", "collected_by", "collection_date",
    "original_text", "notes",
]

VALID_RECORD_TYPES = {"observation", "event", "impact_link", "target", "baseline", "forecast"}


def load_unified_data(path: str | Path) -> pd.DataFrame:
    """Load the unified dataset CSV and apply light dtype cleanup.

    Parameters
    ----------
    path : str or Path
        Path to ethiopia_fi_unified_data.csv (or an enriched version of it).

    Returns
    -------
    pd.DataFrame
        The unified table with parsed dates and validated record_type values.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Unified dataset not found at {path}")

    df = pd.read_csv(path)

    missing = set(REQUIRED_COLUMNS) - set(df.columns)
    if missing:
        raise ValueError(f"Unified dataset is missing expected columns: {sorted(missing)}")

    # Parse date-like columns; errors='coerce' keeps loading robust to blanks.
    for col in ["observation_date", "period_start", "period_end", "collection_date"]:
        df[col] = pd.to_datetime(df[col], errors="coerce", format="mixed")

    bad_types = set(df["record_type"].dropna().unique()) - VALID_RECORD_TYPES
    if bad_types:
        raise ValueError(f"Unexpected record_type values found: {bad_types}")

    return df


def load_reference_codes(path: str | Path) -> pd.DataFrame:
    """Load the reference_codes lookup table."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Reference codes not found at {path}")
    return pd.read_csv(path)


def validate_against_reference(df: pd.DataFrame, ref: pd.DataFrame) -> dict:
    """Check every categorical field in df against the allowed codes in ref.

    Returns a dict of {field: [invalid values]} for any field/value combos
    that fall outside the reference_codes table. An empty dict means the
    dataset is fully compliant with the schema.
    """
    issues = {}
    for field in ref["field"].unique():
        if field not in df.columns:
            continue
        allowed = set(ref.loc[ref["field"] == field, "code"])
        actual = set(df[field].dropna().unique())
        invalid = actual - allowed
        if invalid:
            issues[field] = sorted(invalid)
    return issues


def get_observations(df: pd.DataFrame) -> pd.DataFrame:
    """Return only observation + target rows (i.e. plottable indicator values)."""
    return df[df["record_type"].isin(["observation", "target"])].copy()


def get_events(df: pd.DataFrame) -> pd.DataFrame:
    """Return only event rows."""
    return df[df["record_type"] == "event"].copy()


def get_impact_links(df: pd.DataFrame) -> pd.DataFrame:
    """Return only impact_link rows."""
    return df[df["record_type"] == "impact_link"].copy()


def events_with_impacts(df: pd.DataFrame) -> pd.DataFrame:
    """Join events to their impact_link rows via parent_id -> record_id.

    Returns one row per (event, impact_link) pair with event metadata
    prefixed `event_` and impact metadata prefixed `impact_`.
    """
    events = get_events(df).add_prefix("event_")
    impacts = get_impact_links(df).add_prefix("impact_")
    merged = impacts.merge(
        events,
        left_on="impact_parent_id",
        right_on="event_record_id",
        how="left",
    )
    return merged
