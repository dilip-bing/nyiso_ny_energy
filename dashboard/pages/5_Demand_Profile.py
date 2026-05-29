"""
dashboard/pages/5_Demand_Profile.py
Demand Profile — full 8,760-hour timeseries, monthly averages,
seasonal daily curves, and hour×month heatmap.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st

from config import SEASON_COLORS
from dashboard.components.metrics import get_demand_data, insight_box
from dashboard.components.charts import (
    demand_timeseries, monthly_avg_bar, seasonal_daily_curves, demand_heatmap,
)

# ── Data ──────────────────────────────────────────────────────────────────────
demand_df = get_demand_data()

peak_gw = demand_df["demand_gw"].max()
avg_gw = demand_df["demand_gw"].mean()
min_gw = demand_df["demand_gw"].min()
total_twh = demand_df["demand_mw"].sum() / 1e6
load_factor = avg_gw / peak_gw

# ── Header ────────────────────────────────────────────────────────────────────
st.title("NYISO Hourly Demand Profile (2023)")
st.markdown(
    "Synthetic NYISO demand calibrated to 2023 Gold Book values: "
    "~154 TWh annual energy, ~28 GW summer peak. "
    "Captures seasonal (summer AC, winter heating), diurnal, and weekend patterns."
)

# ── Key stats ─────────────────────────────────────────────────────────────────
k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Annual Energy", f"{total_twh:.1f} TWh")
k2.metric("Summer Peak", f"{peak_gw:.1f} GW")
k3.metric("Average Load", f"{avg_gw:.1f} GW")
k4.metric("Minimum Load", f"{min_gw:.1f} GW")
k5.metric("Load Factor", f"{load_factor:.1%}")

st.divider()

# ── Full timeseries ────────────────────────────────────────────────────────────
st.subheader("8,760-Hour Demand Timeseries (Zoomable)")
st.plotly_chart(demand_timeseries(demand_df), use_container_width=True)

# ── Monthly + seasonal ────────────────────────────────────────────────────────
col1, col2 = st.columns(2)

with col1:
    st.subheader("Average Demand by Month")
    st.plotly_chart(monthly_avg_bar(demand_df), use_container_width=True)

with col2:
    st.subheader("Average Daily Profile by Season")
    st.plotly_chart(seasonal_daily_curves(demand_df, SEASON_COLORS), use_container_width=True)

# ── Heatmap ───────────────────────────────────────────────────────────────────
st.subheader("Demand Intensity: Hour of Day × Month")
st.plotly_chart(demand_heatmap(demand_df), use_container_width=True)

# ── Observations ──────────────────────────────────────────────────────────────
insight_box(
    "<b>NYISO demand characteristics:</b>"
    "<ul style='margin:6px 0 0 16px;padding:0'>"
    "<li>Summer AC-driven peak (July–August): highest demand hours are 14:00–19:00 EST</li>"
    "<li>Secondary winter peak (December–January) from electric heating under CLCPA electrification</li>"
    "<li>Weekend demand ~8% lower than weekday average (reduced commercial/industrial load)</li>"
    "<li>Morning ramp (6:00–9:00) and evening ramp (17:00–21:00) define the duck-curve challenge for solar integration</li>"
    "</ul>"
)
