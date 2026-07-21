"""
forecasting.py

Given how sparse Ethiopia's Findex-anchored series are (5-6 points over 13 years for
Access; 2 points for the Usage metric added in Task 1), we deliberately keep the
statistical part of this simple and let the *event* evidence from Task 3 carry the rest of
the signal via scenario bands, rather than fitting a complex time-series model to a handful
of points.

Two building blocks
--------------------
1. `fit_trend` - OLS linear regression of indicator value on year, with statsmodels
   prediction intervals. This is the "baseline: trend continuation" forecast the brief asks
   for.
2. `event_augmented_forecast` - adds the *incremental* (not yet realized as of the last
   observation) portion of known event effects on top of the trend, at three discount
   levels (optimistic/base/pessimistic) to produce a scenario range. This directly reuses
   `impact_model.project_indicator_effect` from Task 3, so the same functional form
   (logistic ramp, data-calibrated magnitudes) underlies both the impact modeling and the
   forecast - one consistent model, not two.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.api as sm

# Scenario discount factors applied to each event's full modeled effect. Chosen based on
# the Task 3 finding that naively summing full literature/theoretical estimates over-predicts
# actual historical change by roughly an order of magnitude (see 04_event_impact_modeling.ipynb
# Section 6.1) - so even the "optimistic" scenario does NOT use the raw undiscounted matrix.
SCENARIO_DISCOUNTS = {
    "pessimistic": 0.0,   # no incremental event effect realizes; trend only
    "base": 0.25,         # partial realization, consistent with the ~10x historical over-prediction
    "optimistic": 0.60,   # most (not all) of the modeled effect realizes
}


def fit_trend(obs: pd.DataFrame, value_col: str = "value_numeric", date_col: str = "observation_date", kind: str = "linear"):
    """Fit an OLS trend on an observation series and return the fitted results object.

    kind='linear': value ~ year_frac (constant pp/year growth - can overstate future growth
        for a series that is visibly decelerating, since it weights early rapid-growth years
        equally with the recent slowdown).
    kind='log': value ~ ln(year_frac - 2010) (decelerating growth, appropriate for an
        adoption curve approaching saturation - generally a better fit for Ethiopia's
        Access series given the documented 2021-2024 slowdown).

    `obs` should already be filtered to one indicator, national, all-gender, record_type
    'observation' rows.
    """
    data = obs.dropna(subset=[value_col, date_col]).copy()
    data["year_frac"] = data[date_col].dt.year + (data[date_col].dt.dayofyear - 1) / 365.25

    if kind == "log":
        data["x"] = np.log(data["year_frac"] - 2010)
    elif kind == "linear":
        data["x"] = data["year_frac"]
    else:
        raise ValueError("kind must be 'linear' or 'log'")

    X = sm.add_constant(data["x"])
    y = data[value_col]
    model = sm.OLS(y, X).fit()
    model.trend_kind = kind  # stash for predict_trend
    return model, data


def predict_trend(model, year_fracs: np.ndarray, alpha: float = 0.20):
    """Return point forecast + (alpha)-level prediction interval for given year_fracs.

    alpha=0.20 -> 80% prediction interval (deliberately wider than the conventional 95%
    given how few points the trend is fit on - a 95% PI from 5-6 points is not very
    informative and can look falsely precise).
    """
    kind = getattr(model, "trend_kind", "linear")
    x = np.log(year_fracs - 2010) if kind == "log" else year_fracs
    X_new = sm.add_constant(pd.DataFrame({"x": x}), has_constant="add")
    pred = model.get_prediction(X_new)
    summary = pred.summary_frame(alpha=alpha)
    summary.index = year_fracs
    return summary


def heuristic_uncertainty_band(point_estimate: pd.Series, relative_width: float = 0.25) -> pd.DataFrame:
    """Symmetric +/- relative_width% band around a point estimate.

    Used ONLY when a trend has too few points for a statistically meaningful OLS
    prediction interval (e.g. USG_DIGITAL_PAYMENT has just 2 observations -> 0 residual
    degrees of freedom, so statsmodels returns NaN/undefined intervals). This is an
    explicit, documented judgment call, not a statistical estimate - the width should be
    treated as illustrative, not calibrated.
    """
    return pd.DataFrame({
        "mean": point_estimate,
        "obs_ci_lower": point_estimate * (1 - relative_width),
        "obs_ci_upper": point_estimate * (1 + relative_width),
    }, index=point_estimate.index)



def event_augmented_forecast(
    trend_summary: pd.DataFrame,
    events_with_impacts: pd.DataFrame,
    indicator_code: str,
    last_obs_date: pd.Timestamp,
    forecast_dates: pd.DatetimeIndex,
):
    """Combine the trend forecast with the incremental (not-yet-realized) event effect,
    at three discount levels, returning a DataFrame with one row per forecast_date and
    columns: trend, trend_lo, trend_hi, pessimistic, base, optimistic.
    """
    from impact_model import project_indicator_effect  # local import to avoid a hard dependency at module load time

    # Cumulative modeled effect at the last observed date (already "baked into" history,
    # and therefore into the trend fit) vs. at each forecast date.
    effect_at_last_obs = project_indicator_effect(events_with_impacts, indicator_code, pd.DatetimeIndex([last_obs_date])).iloc[0]
    effect_at_forecast = project_indicator_effect(events_with_impacts, indicator_code, forecast_dates)
    incremental_effect = (effect_at_forecast - effect_at_last_obs).clip(lower=0)

    out = pd.DataFrame(index=forecast_dates)
    out["trend"] = trend_summary["mean"].values
    out["trend_lo"] = trend_summary["obs_ci_lower"].values
    out["trend_hi"] = trend_summary["obs_ci_upper"].values
    for scenario, discount in SCENARIO_DISCOUNTS.items():
        out[scenario] = out["trend"] + incremental_effect.values * discount
    out["incremental_event_effect_full"] = incremental_effect.values
    return out
