"""
impact_model.py

Translates qualitative `impact_link` records (direction / magnitude / lag / evidence_basis)
into a quantitative event-effect model that can be evaluated at any point in time and
combined across multiple simultaneous events.

Design choices (see notebooks/04_event_impact_modeling.ipynb Section 2 for full rationale)
--------------------------------------------------------------------------------------------
1. Effects build up gradually, not instantly. We use a logistic ("S-curve") ramp that
   reaches ~50% of its full effect at `lag_months` and is ~95% ramped up by ~2x lag_months.
   This reflects that policy/product effects on a survey-measured outcome (Findex is only
   measured every ~3 years) accumulate through adoption curves, not step-changes.
2. impact_magnitude (low/medium/high) is converted into a numeric percentage-point effect
   using impact_estimate where the source data provides one, and a magnitude->pp mapping
   otherwise (calibrated from the impact_links that DO have both fields, so the mapping is
   internally consistent with the dataset rather than an arbitrary external assumption).
3. Effects on the same indicator from different events are combined ADDITIVELY in
   percentage points. This is a simplifying assumption (see limitations) - interaction
   effects (e.g. Telebirr + M-Pesa competing for the same unbanked population) are not
   modeled.
4. Evidence_basis is used as a confidence weight (empirical > literature > theoretical) when
   summarizing/aggregating, not to change the point estimate itself - the point estimate is
   the analyst's best estimate regardless of source; evidence_basis tells you how much to
   trust it.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

# Magnitude -> percentage-point effect, calibrated as the median impact_estimate observed
# for each magnitude bucket across impact_links that specify both fields in the enriched
# dataset. Used only as a fallback when impact_estimate is missing.
MAGNITUDE_TO_PP = {"low": 2.0, "medium": 6.0, "high": 15.0}

EVIDENCE_WEIGHT = {"empirical": 1.0, "literature": 0.7, "theoretical": 0.4}


def calibrate_magnitude_mapping(impact_links: pd.DataFrame) -> dict:
    """Recompute MAGNITUDE_TO_PP from whatever impact_estimate values are present.

    Falls back to the module-level defaults for any magnitude bucket with no data.
    """
    have_both = impact_links.dropna(subset=["impact_magnitude", "impact_estimate"])
    mapping = dict(MAGNITUDE_TO_PP)
    for mag, group in have_both.groupby("impact_magnitude"):
        mapping[mag] = float(group["impact_estimate"].abs().median())
    return mapping


def effect_pp(row: pd.Series, magnitude_map: dict | None = None) -> float:
    """Return the signed, full-ramp percentage-point effect for one impact_link row."""
    magnitude_map = magnitude_map or MAGNITUDE_TO_PP
    sign = 1.0 if row["impact_direction"] == "increase" else -1.0
    if pd.notna(row.get("impact_estimate")):
        return float(row["impact_estimate"])  # already signed in source data in most cases
    magnitude_pp = magnitude_map.get(row["impact_magnitude"], MAGNITUDE_TO_PP["medium"])
    return sign * magnitude_pp


def ramp_fraction(months_since_event: float, lag_months: float) -> float:
    """Logistic ramp: fraction of the full effect realized at a given time since the event.

    Reaches 0.5 at t = lag_months, ~0.88 at t = 2*lag_months, ~0 for t <= 0.
    A lag_months of 0 or NaN is treated as an (approximately) immediate step effect.
    """
    if months_since_event is None or np.isnan(months_since_event) or months_since_event <= 0:
        return 0.0
    lag = lag_months if (lag_months and lag_months > 0) else 0.5  # near-instant ramp
    k = 4.0 / lag  # steepness chosen so the curve is ~0.5 at t=lag, ~0.95 at t=~3*lag/2... see notebook for a plot
    return float(1.0 / (1.0 + np.exp(-k * (months_since_event - lag))))


def project_indicator_effect(
    events_with_impacts: pd.DataFrame,
    indicator_code: str,
    dates: pd.DatetimeIndex,
    magnitude_map: dict | None = None,
) -> pd.Series:
    """Sum the ramped effect of every event affecting `indicator_code`, evaluated at `dates`.

    `events_with_impacts` must be the output of data_loader.events_with_impacts(df), i.e.
    one row per (event, impact_link) pair with `event_` / `impact_` prefixed columns.
    """
    magnitude_map = magnitude_map or MAGNITUDE_TO_PP
    relevant = events_with_impacts[events_with_impacts["impact_related_indicator"] == indicator_code]

    total = pd.Series(0.0, index=dates)
    for _, row in relevant.iterrows():
        event_date = row["event_observation_date"]
        if pd.isna(event_date):
            continue
        full_effect = effect_pp(
            pd.Series({
                "impact_direction": row["impact_impact_direction"],
                "impact_estimate": row.get("impact_impact_estimate"),
                "impact_magnitude": row["impact_impact_magnitude"],
            }),
            magnitude_map,
        )
        lag = row.get("impact_lag_months")
        months_since = (dates - event_date) / pd.Timedelta(days=30.44)
        ramp = np.array([ramp_fraction(m, lag) for m in months_since])
        total += full_effect * ramp
    return total


def build_association_matrix(
    events_with_impacts: pd.DataFrame,
    value_col: str = "impact_impact_estimate",
) -> pd.DataFrame:
    """Rows = events, columns = related_indicator, values = signed effect estimate.

    Uses impact_estimate directly where present; falls back to the magnitude->pp mapping
    (calibrated from the data) otherwise. NaN where an event has no link to that indicator.
    """
    magnitude_map = calibrate_magnitude_mapping(
        events_with_impacts.rename(columns={
            "impact_impact_magnitude": "impact_magnitude",
            "impact_impact_estimate": "impact_estimate",
        })
    )

    rows = []
    for _, row in events_with_impacts.iterrows():
        est = row.get(value_col)
        if pd.isna(est):
            est = effect_pp(pd.Series({
                "impact_direction": row["impact_impact_direction"],
                "impact_estimate": np.nan,
                "impact_magnitude": row["impact_impact_magnitude"],
            }), magnitude_map)
        rows.append({
            "event": row["event_indicator"],
            "indicator": row["impact_related_indicator"],
            "effect_pp": est,
        })
    long_df = pd.DataFrame(rows)
    matrix = long_df.pivot_table(index="event", columns="indicator", values="effect_pp", aggfunc="mean")
    return matrix
