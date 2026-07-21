"""
dashboard/app.py

Streamlit dashboard for Selam Analytics' Ethiopia Financial Inclusion Forecast.

Run locally with:
    streamlit run dashboard/app.py

Reuses the same src/ modules as the notebooks (data_loader, impact_model, forecasting) so
the dashboard is guaranteed to be consistent with the analysis notebooks - no logic is
duplicated or re-derived here.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from data_loader import load_unified_data, get_observations, get_events, events_with_impacts  # noqa: E402
from impact_model import build_association_matrix  # noqa: E402
from forecasting import fit_trend, predict_trend, heuristic_uncertainty_band, event_augmented_forecast  # noqa: E402

DATA_PATH = ROOT / "data" / "processed" / "ethiopia_fi_unified_data_enriched.csv"

st.set_page_config(
    page_title="Ethiopia Financial Inclusion Forecast",
    page_icon="\U0001F4C8",
    layout="wide",
)

NAVY = "#1F3864"
ACCENT = "#2E5C8A"
GREEN = "#3C8A5C"
RED = "#C0392B"
ORANGE = "#8A5C3C"
PURPLE = "#7D3C98"


# ---------------------------------------------------------------------------
# Data loading (cached so repeated interactions don't re-read/re-fit every time)
# ---------------------------------------------------------------------------
@st.cache_data
def load_data():
    df = load_unified_data(DATA_PATH)
    obs = get_observations(df)
    events = get_events(df)
    ei = events_with_impacts(df)
    return df, obs, events, ei


@st.cache_data
def compute_forecasts(_obs, _ei):
    """Return forecast tables for ACCESS and USAGE. Underscore-prefixed args tell
    st.cache_data not to try hashing the (unhashable) DataFrames by content identity."""
    forecast_dates = pd.to_datetime(["2025-11-29", "2026-11-29", "2027-11-29"])
    year_fracs = np.array([d.year + (d.dayofyear - 1) / 365.25 for d in forecast_dates])

    acc_obs = _obs[(_obs["indicator_code"] == "ACC_OWNERSHIP") & (_obs["gender"] == "all") & (_obs["record_type"] == "observation")]
    acc_model, _ = fit_trend(acc_obs, kind="log")
    acc_summary = predict_trend(acc_model, year_fracs, alpha=0.20)
    acc_forecast = event_augmented_forecast(acc_summary, _ei, "ACC_OWNERSHIP", acc_obs["observation_date"].max(), forecast_dates)
    acc_forecast.insert(0, "year", [2025, 2026, 2027])

    dp_obs = _obs[(_obs["indicator_code"] == "USG_DIGITAL_PAYMENT") & (_obs["gender"] == "all") & (_obs["record_type"] == "observation")]
    dp_model, _ = fit_trend(dp_obs, kind="linear")
    dp_point = predict_trend(dp_model, year_fracs)["mean"]
    dp_point.index = forecast_dates
    dp_band = heuristic_uncertainty_band(dp_point, relative_width=0.30)
    dp_trend_summary = pd.DataFrame(
        {"mean": dp_point.values, "obs_ci_lower": dp_band["obs_ci_lower"].values, "obs_ci_upper": dp_band["obs_ci_upper"].values},
        index=year_fracs,
    )
    dp_forecast = event_augmented_forecast(dp_trend_summary, _ei, "USG_DIGITAL_PAYMENT", dp_obs["observation_date"].max(), forecast_dates)
    dp_forecast.insert(0, "year", [2025, 2026, 2027])

    return acc_forecast.set_index("year"), dp_forecast.set_index("year"), forecast_dates


df, obs, events, ei = load_data()
acc_forecast, dp_forecast, forecast_dates = compute_forecasts(obs, ei)

INDICATOR_LABELS = {
    "ACC_OWNERSHIP": "Account Ownership Rate (Access)",
    "ACC_MM_ACCOUNT": "Mobile Money Account Rate",
    "USG_DIGITAL_PAYMENT": "Digital Payment Adoption Rate (Usage)",
    "USG_P2P_COUNT": "P2P Transaction Count",
    "USG_ATM_COUNT": "ATM Transaction Count",
    "ACC_4G_COV": "4G Population Coverage",
    "ACC_MOBILE_SUBS": "Mobile Subscriptions",
    "GEN_GAP_ACC": "Account Ownership Gender Gap",
}

# ---------------------------------------------------------------------------
# Sidebar navigation
# ---------------------------------------------------------------------------
st.sidebar.title("\U0001F1EA\U0001F1F9 Ethiopia FI Forecast")
st.sidebar.caption("Selam Analytics — for the consortium of DFIs, mobile money operators, and NBE")
page = st.sidebar.radio("Navigate", ["Overview", "Trends", "Forecasts", "Inclusion Projections"], label_visibility="collapsed")
st.sidebar.markdown("---")
st.sidebar.markdown(
    "**About this data**\n\n"
    "Unified schema of observations, events, impact_links, and targets. "
    "See `data_enrichment_log.md` and `notebooks/` for full methodology."
)

with st.sidebar.expander("Download data"):
    st.download_button(
        "Enriched dataset (CSV)",
        data=df.to_csv(index=False).encode("utf-8"),
        file_name="ethiopia_fi_unified_data_enriched.csv",
        mime="text/csv",
    )
    st.download_button(
        "Access forecast (CSV)",
        data=acc_forecast.to_csv().encode("utf-8"),
        file_name="access_forecast_2025_2027.csv",
        mime="text/csv",
    )
    st.download_button(
        "Usage forecast (CSV)",
        data=dp_forecast.to_csv().encode("utf-8"),
        file_name="usage_forecast_2025_2027.csv",
        mime="text/csv",
    )


def latest(indicator_code, gender="all"):
    rows = obs[(obs["indicator_code"] == indicator_code) & (obs["gender"] == gender) & (obs["record_type"] == "observation")].sort_values("observation_date")
    if rows.empty:
        return None, None, None
    last = rows.iloc[-1]
    prev = rows.iloc[-2] if len(rows) > 1 else None
    delta = last["value_numeric"] - prev["value_numeric"] if prev is not None else None
    return last["value_numeric"], delta, last["observation_date"]


# ===========================================================================
# PAGE 1: OVERVIEW
# ===========================================================================
if page == "Overview":
    st.title("Ethiopia Financial Inclusion — Overview")
    st.caption("Key metrics as of the latest available reading for each indicator.")

    c1, c2, c3, c4 = st.columns(4)
    val, delta, date = latest("ACC_OWNERSHIP")
    c1.metric("Account Ownership (Access)", f"{val:.0f}%", f"{delta:+.1f}pp vs. prior survey", help=f"As of {date.date()}")

    val, delta, date = latest("USG_DIGITAL_PAYMENT")
    c2.metric("Digital Payment Adoption (Usage)", f"{val:.0f}%", f"{delta:+.1f}pp vs. prior survey", help=f"As of {date.date()}")

    val, delta, date = latest("ACC_MM_ACCOUNT")
    c3.metric("Mobile Money Account Rate", f"{val:.2f}%", f"{delta:+.2f}pp vs. prior survey", help=f"As of {date.date()}")

    val, delta, date = latest("GEN_GAP_ACC")
    c4.metric("Gender Gap (Account Ownership)", f"{val:.0f}pp", f"{delta:+.0f}pp vs. prior survey" if delta is not None else None, help=f"As of {date.date()}", delta_color="inverse")

    st.markdown("### P2P / ATM Crossover")
    p2p = obs[(obs["indicator_code"] == "USG_P2P_COUNT")].sort_values("observation_date")
    atm = obs[(obs["indicator_code"] == "USG_ATM_COUNT")].sort_values("observation_date")
    if not p2p.empty and not atm.empty:
        latest_p2p = p2p.iloc[-1]["value_numeric"]
        latest_atm = atm.iloc[-1]["value_numeric"]
        ratio = latest_p2p / latest_atm
        col1, col2 = st.columns([1, 2])
        with col1:
            st.metric("P2P : ATM transaction ratio", f"{ratio:.2f}x", "P2P now exceeds ATM volume" if ratio > 1 else "ATM still exceeds P2P")
        with col2:
            fig = go.Figure(go.Bar(
                x=["P2P Transactions", "ATM Withdrawals"], y=[latest_p2p, latest_atm],
                marker_color=[GREEN, ACCENT], text=[f"{latest_p2p/1e6:.0f}M", f"{latest_atm/1e6:.0f}M"], textposition="outside",
            ))
            fig.update_layout(height=260, margin=dict(t=10, b=10, l=10, r=10), showlegend=False)
            st.plotly_chart(fig, width="stretch")

    st.markdown("### Growth Highlights (2021 → latest)")
    hcols = st.columns(3)
    highlights = [
        ("Telebirr users", "USG_TELEBIRR_USERS", "{:,.0f}"),
        ("4G population coverage", "ACC_4G_COV", "{:.1f}%"),
        ("Mobile subscriptions", "ACC_MOBILE_SUBS", "{:,.0f}"),
    ]
    for col, (label, code, fmt) in zip(hcols, highlights):
        rows = obs[(obs["indicator_code"] == code)].sort_values("observation_date")
        if not rows.empty:
            last_row = rows.iloc[-1]
            col.metric(label, fmt.format(last_row["value_numeric"]), help=f"As of {last_row['observation_date'].date()}")

    st.info(
        "**Key takeaway:** Account Ownership growth has decelerated sharply since 2021 "
        "(+1.0pp/year vs. +3.3–3.7pp/year previously) despite Telebirr, M-Pesa, and "
        "infrastructure investment scaling rapidly — see the *Trends* and *Forecasts* pages "
        "for the full analysis.",
        icon="\U0001F4A1",
    )


# ===========================================================================
# PAGE 2: TRENDS
# ===========================================================================
elif page == "Trends":
    st.title("Trends")
    st.caption("Explore indicator trends over time, with events overlaid.")

    all_dates = obs["observation_date"].dropna()
    min_date, max_date = all_dates.min().date(), all_dates.max().date()
    date_range = st.slider("Date range", min_value=min_date, max_value=max_date, value=(min_date, max_date))

    available_indicators = sorted(obs.loc[obs["record_type"] == "observation", "indicator_code"].dropna().unique())
    default_selection = [c for c in ["ACC_OWNERSHIP", "USG_DIGITAL_PAYMENT"] if c in available_indicators]
    selected = st.multiselect(
        "Indicators to compare",
        options=available_indicators,
        default=default_selection or available_indicators[:2],
        format_func=lambda c: INDICATOR_LABELS.get(c, c),
    )
    show_events = st.checkbox("Overlay events", value=True)

    if selected:
        fig = go.Figure()
        colors = px.colors.qualitative.Set1
        for i, code in enumerate(selected):
            series = obs[
                (obs["indicator_code"] == code) & (obs["gender"] == "all") & (obs["record_type"] == "observation")
                & (obs["observation_date"].dt.date >= date_range[0]) & (obs["observation_date"].dt.date <= date_range[1])
            ].sort_values("observation_date")
            if series.empty:
                continue
            fig.add_trace(go.Scatter(
                x=series["observation_date"], y=series["value_numeric"], mode="lines+markers",
                name=INDICATOR_LABELS.get(code, code), line=dict(width=3, color=colors[i % len(colors)]),
                marker=dict(size=9),
            ))

        if show_events:
            ev_in_range = events[(events["observation_date"].dt.date >= date_range[0]) & (events["observation_date"].dt.date <= date_range[1])]
            for _, row in ev_in_range.iterrows():
                fig.add_vline(x=row["observation_date"].timestamp() * 1000, line_dash="dash", line_color="gray", opacity=0.4)

        fig.update_layout(
            height=520, hovermode="x unified", legend=dict(orientation="h", yanchor="bottom", y=1.02),
            xaxis_title="Date", yaxis_title="Value (indicator-native unit)",
        )
        st.plotly_chart(fig, width="stretch")

        if show_events and not ev_in_range.empty:
            with st.expander(f"Events in range ({len(ev_in_range)})"):
                st.dataframe(
                    ev_in_range[["observation_date", "indicator", "category", "confidence"]].sort_values("observation_date").rename(
                        columns={"observation_date": "date", "indicator": "event"}
                    ),
                    hide_index=True, width="stretch",
                )
    else:
        st.warning("Select at least one indicator to plot.")

    st.markdown("### Channel Comparison: Mobile Money Operators")
    channel_cols = st.columns(2)
    with channel_cols[0]:
        mpesa = obs[obs["indicator_code"].isin(["USG_MPESA_USERS", "USG_MPESA_ACTIVE"])]
        if not mpesa.empty:
            fig2 = px.bar(
                mpesa, x="indicator_code", y="value_numeric", color="indicator_code",
                title="M-Pesa: Registered vs. Active Users", labels={"value_numeric": "Users", "indicator_code": ""},
                color_discrete_sequence=[ACCENT, GREEN],
            )
            fig2.update_layout(showlegend=False, height=380)
            st.plotly_chart(fig2, width="stretch")
    with channel_cols[1]:
        telebirr = obs[obs["indicator_code"] == "USG_TELEBIRR_USERS"]
        mm_share = obs[obs["indicator_code"] == "ACC_MM_ACCOUNT"].sort_values("observation_date")
        if not mm_share.empty:
            fig3 = px.line(
                mm_share, x="observation_date", y="value_numeric", markers=True,
                title="Mobile Money Account Rate Over Time", labels={"value_numeric": "% of adults", "observation_date": "Date"},
            )
            fig3.update_traces(line_color=ORANGE, marker_size=10)
            fig3.update_layout(height=380)
            st.plotly_chart(fig3, width="stretch")


# ===========================================================================
# PAGE 3: FORECASTS
# ===========================================================================
elif page == "Forecasts":
    st.title("Forecasts: Access and Usage, 2025–2027")
    st.caption("Trend regression + event-augmented scenarios. See notebooks/05_forecasting.ipynb for full methodology.")

    target_choice = st.selectbox("Indicator", ["Account Ownership Rate (Access)", "Digital Payment Adoption Rate (Usage)"])
    scenario_choice = st.multiselect("Scenarios to show", ["pessimistic", "base", "optimistic"], default=["pessimistic", "base", "optimistic"])
    show_trend_band = st.checkbox("Show trend uncertainty band", value=True)

    is_access = target_choice.startswith("Account")
    forecast_tbl = acc_forecast if is_access else dp_forecast
    indicator_code = "ACC_OWNERSHIP" if is_access else "USG_DIGITAL_PAYMENT"
    hist = obs[(obs["indicator_code"] == indicator_code) & (obs["gender"] == "all") & (obs["record_type"] == "observation")].sort_values("observation_date")

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=hist["observation_date"], y=hist["value_numeric"], mode="lines+markers", name="Observed",
                              line=dict(color=NAVY, width=3), marker=dict(size=10)))

    scenario_colors = {"pessimistic": "#AAAAAA", "base": RED, "optimistic": GREEN}
    for scenario in scenario_choice:
        fig.add_trace(go.Scatter(
            x=forecast_dates, y=forecast_tbl[scenario], mode="lines+markers", name=scenario.capitalize(),
            line=dict(color=scenario_colors[scenario], width=2.5, dash="dot" if scenario != "base" else "solid"),
            marker=dict(size=9),
        ))

    if show_trend_band:
        fig.add_trace(go.Scatter(
            x=list(forecast_dates) + list(forecast_dates[::-1]),
            y=list(forecast_tbl["trend_hi"]) + list(forecast_tbl["trend_lo"][::-1]),
            fill="toself", fillcolor="rgba(46,92,138,0.12)", line=dict(color="rgba(255,255,255,0)"),
            name="Trend uncertainty band", showlegend=True,
        ))

    if is_access:
        fig.add_hline(y=70, line_dash="dash", line_color=PURPLE, annotation_text="NFIS-II target (70% by 2025)")

    fig.update_layout(height=550, hovermode="x unified", xaxis_title="Date", yaxis_title="% of adults",
                       legend=dict(orientation="h", yanchor="bottom", y=1.02))
    st.plotly_chart(fig, width="stretch")

    st.markdown("#### Forecast Table")
    display_cols = ["trend", "trend_lo", "trend_hi"] + scenario_choice
    st.dataframe(forecast_tbl[display_cols].round(1).rename(columns={
        "trend": "Trend (point)", "trend_lo": "Trend low (80% PI)", "trend_hi": "Trend high (80% PI)",
        "pessimistic": "Pessimistic", "base": "Base", "optimistic": "Optimistic",
    }), width="stretch")

    if not is_access:
        st.warning(
            "**Usage forecast caveat:** USG_DIGITAL_PAYMENT has only 2 historical observations "
            "(2021, 2024). The trend band shown is a heuristic ±30% range, not a statistical "
            "confidence interval — treat this forecast as the least reliable in the dashboard.",
            icon="\u26A0\uFE0F",
        )

    st.markdown("#### Events with the Largest Modeled Impact")
    matrix = build_association_matrix(ei)
    event_totals = matrix.abs().sum(axis=1).sort_values(ascending=False)
    fig_rank = px.bar(
        x=event_totals.values, y=event_totals.index, orientation="h",
        labels={"x": "Sum of |estimated effect| across linked indicators (pp)", "y": ""},
        color=event_totals.values, color_continuous_scale="Blues",
    )
    fig_rank.update_layout(height=420, coloraxis_showscale=False, yaxis=dict(autorange="reversed"))
    st.plotly_chart(fig_rank, width="stretch")


# ===========================================================================
# PAGE 4: INCLUSION PROJECTIONS
# ===========================================================================
elif page == "Inclusion Projections":
    st.title("Inclusion Projections & Progress Toward Targets")

    scenario = st.select_slider("Scenario", options=["pessimistic", "base", "optimistic"], value="base")

    targets = obs[obs["record_type"] == "target"]

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### Access: Progress to NFIS-II 70% Target")
        acc_2027 = acc_forecast.loc[2027, scenario]
        acc_target = 70.0
        progress = min(acc_2027 / acc_target, 1.0)
        st.progress(progress, text=f"{acc_2027:.1f}% of adults (target: {acc_target:.0f}% by 2025)")
        gap = acc_target - acc_2027
        st.metric("Projected gap to target by 2027", f"{gap:.1f}pp", delta_color="off")

    with col2:
        st.markdown("#### Usage: Digital Payment Adoption")
        dp_2027 = dp_forecast.loc[2027, scenario]
        st.progress(min(dp_2027 / 100, 1.0), text=f"{dp_2027:.1f}% of adults use digital payments (projected, 2027)")
        dp_2024 = obs[(obs["indicator_code"] == "USG_DIGITAL_PAYMENT") & (obs["observation_date"].dt.year == 2024)]["value_numeric"].iloc[0]
        st.metric("Projected growth, 2024 → 2027", f"+{dp_2027 - dp_2024:.1f}pp", delta_color="off")

    st.markdown("### All Official Targets vs. Projections")
    target_rows = []
    for _, t in targets.iterrows():
        target_rows.append({
            "Indicator": INDICATOR_LABELS.get(t["indicator_code"], t["indicator_code"]),
            "Target value": t["value_numeric"],
            "Target date": t["observation_date"].date() if pd.notna(t["observation_date"]) else None,
            "Source": t["source_name"],
        })
    st.dataframe(pd.DataFrame(target_rows), hide_index=True, width="stretch")

    st.markdown("### Consortium's Key Questions — Answered")
    with st.expander("What drives financial inclusion in Ethiopia?", expanded=True):
        st.write(
            "Access is driven mainly by slower-acting policy/infrastructure events (NFIS-II, "
            "Fayda digital ID, 4G rollout) with 12–36 month lags; Usage is driven by "
            "faster-acting product launches and partnerships (Telebirr, M-Pesa, EthSwitch "
            "interoperability) with 3–6 month lags. See the Event Impact Modeling notebook "
            "(Task 3) for the full association matrix."
        )
    with st.expander("How do events affect inclusion outcomes?"):
        st.write(
            "Individually, often substantially — but effects on the *same* indicator from "
            "multiple events do not simply add up; our Task 3 validation found naive summation "
            "over-predicts actual historical change by roughly 10x, so this dashboard's "
            "scenarios apply discount factors (0% / 25% / 60%) rather than raw event totals."
        )
    with st.expander("What are the projected rates for 2025-2027?"):
        st.write(
            f"Base-case: Access reaches ~{acc_forecast.loc[2027,'base']:.0f}% by 2027 (vs. the "
            f"70% NFIS-II target — very likely to be missed); Usage reaches "
            f"~{dp_forecast.loc[2027,'base']:.0f}% by 2027, the more uncertain of the two "
            "forecasts given only 2 historical data points."
        )

    st.markdown("### Strategic Recommendations")
    st.markdown(
        "- **Re-baseline the NFIS-II 70% target** or explicitly acknowledge it will likely be missed — "
        "continuing to plan against it risks a credibility gap with the consortium.\n"
        "- **Prioritize activation over registration** for mobile money — the 66% M-Pesa "
        "activity rate and the gap between mobile money account growth (+4.75pp) and overall "
        "Account Ownership growth (+3pp) both point to dormant/duplicate accounts, not "
        "under-registration, as the binding constraint.\n"
        "- **Track USG_DIGITAL_PAYMENT going forward** — it was missing from the original "
        "dataset despite being a headline Findex metric; the consortium should ensure it's "
        "captured in future monitoring, not reconstructed retroactively as we had to do here.\n"
        "- **Treat NDPS 2.0 (launched Apr 2025) as the highest-leverage near-term lever** for "
        "the 2025-2027 window specifically, since its effect is the least already 'baked into' "
        "the historical trend."
    )

st.sidebar.markdown("---")
st.sidebar.caption("Data as of the enriched dataset (74–75 records). Forecasts generated by src/forecasting.py.")
