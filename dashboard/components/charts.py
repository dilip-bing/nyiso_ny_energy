"""
dashboard/components/charts.py
Plotly chart factories — Apple-inspired modern design.

Design conventions
------------------
- Apple system font stack (SF Pro on macOS natively)
- White plot area, #F5F5F7 paper background
- Very subtle gridlines (#F0F0F3), no axis borders
- Rounded chart corners not possible in Plotly, so we rely on
  the Streamlit container providing the 12px radius
- No emojis in any annotation or label text
- Color palette: Apple spectrum (amber, blue, purple, green, red, gray)
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

# ── Design tokens ──────────────────────────────────────────────────────────────
_FONT  = "-apple-system, BlinkMacSystemFont, 'Helvetica Neue', Arial, sans-serif"
_T1    = "#1D1D1F"   # Apple primary text
_T2    = "#6E6E73"   # Apple secondary
_T3    = "#86868B"   # Apple tertiary
_BG    = "#F5F5F7"   # Apple page background
_CARD  = "#FFFFFF"
_GRID  = "#F0F0F3"   # very subtle gridlines
_SEP   = "#D2D2D7"   # separator
_BLUE  = "#0066CC"   # energy blue


# ── Base layout ────────────────────────────────────────────────────────────────

def _base_layout(**kwargs) -> dict:
    """
    Apple-inspired Plotly layout with deep-merge for nested dict overrides.
    """
    base: dict = dict(
        plot_bgcolor=_CARD,
        paper_bgcolor=_BG,
        font=dict(family=_FONT, color=_T1, size=12),
        yaxis=dict(
            gridcolor=_GRID, zeroline=False, gridwidth=1,
            linecolor="rgba(0,0,0,0)",
            tickfont=dict(size=11, color=_T3),
            title_font=dict(size=11, color=_T2),
        ),
        xaxis=dict(
            gridcolor=_GRID,
            linecolor="rgba(0,0,0,0)",
            tickfont=dict(size=11, color=_T3),
            title_font=dict(size=11, color=_T2),
        ),
        legend=dict(
            orientation="h", y=-0.22, x=0,
            font=dict(size=11, color=_T2),
            bgcolor="rgba(0,0,0,0)", borderwidth=0,
        ),
        margin=dict(t=16, b=68, l=58, r=16),
        colorway=["#4A7FB5","#D4893A","#3A8A7B","#A94442","#7B68AE","#6B7280","#1F4E79"],
    )
    for key, val in kwargs.items():
        if key in base and isinstance(base[key], dict) and isinstance(val, dict):
            base[key] = {**base[key], **val}
        else:
            base[key] = val
    return base


def _bar(x, y, colors, text=None, orientation="v", **kwargs):
    """Shared clean bar trace — no marker borders, optional text labels."""
    return go.Bar(
        x=x, y=y,
        orientation=orientation,
        marker=dict(color=colors, line=dict(width=0)),
        text=text,
        textposition="outside" if text else None,
        textfont=dict(size=12, color=_T1, family=_FONT),
        cliponaxis=False,
        **kwargs,
    )


# ── Overview ───────────────────────────────────────────────────────────────────

def cost_comparison_bar(results: list, colors: list[str]) -> go.Figure:
    """Bar: total annualized system cost per scenario."""
    fig = go.Figure(_bar(
        x=[r.scenario_name for r in results],
        y=[r.total_cost_b_yr for r in results],
        colors=colors,
        text=[f"${r.total_cost_b_yr:.2f}B" for r in results],
    ))
    fig.update_layout(
        **_base_layout(
            yaxis_title="Annualized Cost ($B / yr)",
            yaxis=dict(range=[0, max(r.total_cost_b_yr for r in results) * 1.22]),
            height=320, showlegend=False,
        )
    )
    return fig


def co2_bar(results: list, baseline_mt: float = 55.0) -> go.Figure:
    """Bar: CO2 emissions vs 2019 baseline (no CO₂ unicode in axis label)."""
    bar_colors = ["#D4893A", "#A94442", "#3A7D55"]
    fig = go.Figure(_bar(
        x=[r.scenario_name for r in results],
        y=[r.co2_mt_yr for r in results],
        colors=bar_colors,
        text=[f"{r.co2_mt_yr:.1f} Mt" for r in results],
    ))
    fig.add_hline(
        y=baseline_mt,
        line_dash="dash", line_color=_SEP, line_width=1.5,
        annotation_text=f"2019 Baseline  {baseline_mt:.0f} Mt",
        annotation_position="top right",
        annotation_font=dict(size=11, color=_T3),
    )
    fig.update_layout(
        **_base_layout(
            yaxis_title="CO2 Emissions (Mt / yr)",
            yaxis=dict(range=[0, baseline_mt * 1.28]),
            height=320, showlegend=False,
        )
    )
    return fig


# ── Capacity & Generation Mix ──────────────────────────────────────────────────

def capacity_donut(result, tech_colors: dict) -> go.Figure:
    items = [(t, gw) for t, gw in result.capacity_gw.items() if gw > 0.05]
    total = sum(gw for _, gw in items)
    fig = go.Figure(go.Pie(
        labels=[t for t, _ in items],
        values=[gw for _, gw in items],
        hole=0.52,
        marker=dict(
            colors=[tech_colors[t] for t, _ in items],
            line=dict(color=_CARD, width=2.5),
        ),
        textinfo="label+percent",
        textfont=dict(size=11, family=_FONT, color=_T1),
        hovertemplate="%{label}: %{value:.1f} GW (%{percent})<extra></extra>",
        insidetextorientation="radial",
    ))
    fig.update_layout(
        height=360, showlegend=False,
        paper_bgcolor=_BG, plot_bgcolor=_BG,
        margin=dict(t=8, b=8, l=8, r=8),
        annotations=[dict(
            text=f"<b>{total:.1f}</b><br><span style='font-size:11px'>GW</span>",
            x=0.5, y=0.5,
            font=dict(size=18, family=_FONT, color=_T1),
            showarrow=False,
        )],
    )
    return fig


def generation_donut(result, tech_colors: dict) -> go.Figure:
    items = [(t, twh) for t, twh in result.generation_twh.items() if twh > 0.5]
    total = sum(twh for _, twh in items)
    fig = go.Figure(go.Pie(
        labels=[t for t, _ in items],
        values=[twh for _, twh in items],
        hole=0.52,
        marker=dict(
            colors=[tech_colors[t] for t, _ in items],
            line=dict(color=_CARD, width=2.5),
        ),
        textinfo="label+percent",
        textfont=dict(size=11, family=_FONT, color=_T1),
        hovertemplate="%{label}: %{value:.1f} TWh (%{percent})<extra></extra>",
        insidetextorientation="radial",
    ))
    fig.update_layout(
        height=360, showlegend=False,
        paper_bgcolor=_BG, plot_bgcolor=_BG,
        margin=dict(t=8, b=8, l=8, r=8),
        annotations=[dict(
            text=f"<b>{total:.1f}</b><br><span style='font-size:11px'>TWh</span>",
            x=0.5, y=0.5,
            font=dict(size=18, family=_FONT, color=_T1),
            showarrow=False,
        )],
    )
    return fig


def capacity_stack_bar(scenario_map: dict, scenarios: list, tech_colors: dict) -> go.Figure:
    fig = go.Figure()
    for tech, color in tech_colors.items():
        fig.add_trace(go.Bar(
            name=tech,
            y=scenarios,
            x=[scenario_map[s].capacity_gw.get(tech, 0) for s in scenarios],
            orientation="h",
            marker=dict(color=color, line=dict(width=0)),
            hovertemplate=f"{tech}: %{{x:.1f}} GW<extra></extra>",
        ))
    fig.update_layout(
        **_base_layout(
            barmode="stack",
            xaxis_title="Installed Capacity (GW)",
            xaxis=dict(gridcolor=_GRID),
            yaxis=dict(gridcolor="rgba(0,0,0,0)"),
            height=220,
        )
    )
    return fig


def generation_stack_bar(
    scenario_map: dict, scenarios: list, tech_colors: dict, demand_twh: float
) -> go.Figure:
    fig = go.Figure()
    for tech, color in tech_colors.items():
        fig.add_trace(go.Bar(
            name=tech,
            x=scenarios,
            y=[scenario_map[s].generation_twh.get(tech, 0) for s in scenarios],
            marker=dict(color=color, line=dict(width=0)),
            hovertemplate=f"{tech}: %{{y:.1f}} TWh<extra></extra>",
        ))
    fig.add_hline(
        y=demand_twh, line_dash="dot", line_color=_T1, line_width=1.5,
        annotation_text=f"Annual Demand  {demand_twh:.0f} TWh",
        annotation_position="top right",
        annotation_font=dict(size=11, color=_T2),
    )
    fig.update_layout(
        **_base_layout(barmode="stack", yaxis_title="Annual Generation (TWh)", height=340)
    )
    return fig


# ── Cost Analysis ──────────────────────────────────────────────────────────────

def cost_by_tech_bar(result, tech_colors: dict) -> go.Figure:
    items = sorted(
        [(t, c) for t, c in result.cost_breakdown_m.items() if c > 5],
        key=lambda x: x[1], reverse=True,
    )
    fig = go.Figure(_bar(
        x=[t for t, _ in items],
        y=[c for _, c in items],
        colors=[tech_colors[t] for t, _ in items],
        text=[f"${c/1e3:.2f}B" for _, c in items],
    ))
    max_c = max(c for _, c in items)
    fig.update_layout(
        **_base_layout(
            yaxis_title="Annual Cost ($M / yr)",
            yaxis=dict(range=[0, max_c * 1.2]),
            height=340, showlegend=False,
        )
    )
    return fig


def lcoe_comparison_bar(
    scenario_map: dict, scenarios: list, colors: list, benchmark_mwh: float = 76
) -> go.Figure:
    fig = go.Figure(_bar(
        x=scenarios,
        y=[scenario_map[s].lcoe_system for s in scenarios],
        colors=colors,
        text=[f"${scenario_map[s].lcoe_system:.0f}/MWh" for s in scenarios],
    ))
    fig.add_hline(
        y=benchmark_mwh, line_dash="dot", line_color="#A94442", line_width=1.5,
        annotation_text=f"US avg retail  ${benchmark_mwh}/MWh",
        annotation_position="top right",
        annotation_font=dict(size=11, color=_T3),
    )
    fig.update_layout(
        **_base_layout(yaxis_title="System LCOE ($/MWh)", height=320, showlegend=False)
    )
    return fig


def cost_stack_scenarios(
    scenario_map: dict, scenarios: list, tech_colors: dict
) -> go.Figure:
    fig = go.Figure()
    for tech, color in tech_colors.items():
        fig.add_trace(go.Bar(
            name=tech,
            x=scenarios,
            y=[scenario_map[s].cost_breakdown_m.get(tech, 0) / 1e3 for s in scenarios],
            marker=dict(color=color, line=dict(width=0)),
            hovertemplate=f"{tech}: $%{{y:.2f}}B / yr<extra></extra>",
        ))
    fig.update_layout(
        **_base_layout(barmode="stack", yaxis_title="Annual Cost ($B / yr)", height=340)
    )
    return fig


# ── Sensitivity ────────────────────────────────────────────────────────────────

def sensitivity_heatmap(
    sens_df: pd.DataFrame, value_col: str, title_text: str, fmt: str = ".1f"
) -> go.Figure:
    pivot = sens_df.pivot_table(
        values=value_col, index="solar_capital_per_kw", columns="wind_capital_per_kw"
    )
    text_arr = [[f"${v:{fmt}}" for v in row] for row in pivot.values]
    fig = go.Figure(go.Heatmap(
        z=pivot.values,
        x=[f"${int(c)}" for c in pivot.columns],
        y=[f"${int(r)}" for r in pivot.index],
        colorscale=[
            [0.0,  "#1F4E79"],
            [0.30, "#5B9BD5"],
            [0.55, "#DDEAF9"],
            [0.75, "#F0C285"],
            [1.0,  "#A94442"],
        ],
        text=text_arr,
        texttemplate="%{text}",
        textfont=dict(size=11, family=_FONT),
        colorbar=dict(
            title=dict(text=title_text, font=dict(size=11, family=_FONT, color=_T2)),
            thickness=10,
            tickfont=dict(size=10, family=_FONT, color=_T3),
            outlinewidth=0,
        ),
        hovertemplate="Solar: %{y}<br>Wind: %{x}<br>%{text}<extra></extra>",
    ))
    fig.update_layout(
        xaxis_title="Onshore Wind Capital Cost ($/kW)",
        yaxis_title="Solar PV Capital Cost ($/kW)",
        font=dict(family=_FONT, size=11, color=_T2),
        paper_bgcolor=_BG,
        height=340,
        margin=dict(t=8, b=68, l=88, r=16),
    )
    return fig


def capacity_response_line(
    df: pd.DataFrame, x_col: str, y_col: str,
    x_label: str, y_label: str, color: str = _BLUE,
) -> go.Figure:
    avg = df.groupby(x_col)[y_col].mean().reset_index()
    fig = go.Figure(go.Scatter(
        x=avg[x_col], y=avg[y_col],
        mode="lines+markers",
        line=dict(color=color, width=2.5),
        marker=dict(size=7, color=color, symbol="circle",
                    line=dict(color=_CARD, width=2)),
        hovertemplate=f"${'{'}x{'}'}<br>%{{y:.1f}} GW<extra></extra>",
    ))
    fig.update_layout(
        **_base_layout(xaxis_title=x_label, yaxis_title=y_label,
                       height=280, showlegend=False)
    )
    return fig


# ── Demand Profile ─────────────────────────────────────────────────────────────

def demand_timeseries(demand_df: pd.DataFrame) -> go.Figure:
    fig = go.Figure(go.Scatter(
        x=demand_df["timestamp"],
        y=demand_df["demand_gw"],
        mode="lines",
        line=dict(color="#4A7FB5", width=0.9),
        fill="tozeroy",
        fillcolor="rgba(74,127,181,0.09)",
        hovertemplate="%{x|%b %d  %H:%M}<br><b>%{y:.2f} GW</b><extra></extra>",
    ))
    fig.update_layout(
        **_base_layout(yaxis_title="Demand (GW)", height=340, showlegend=False)
    )
    fig.update_xaxes(
        rangeslider_visible=True,
        rangeslider_thickness=0.04,
        rangeslider=dict(bgcolor="#EBEBF0", bordercolor=_SEP, borderwidth=0),
    )
    return fig


def monthly_avg_bar(demand_df: pd.DataFrame) -> go.Figure:
    month_names = ["Jan","Feb","Mar","Apr","May","Jun",
                   "Jul","Aug","Sep","Oct","Nov","Dec"]
    monthly = demand_df.groupby("month")["demand_gw"].mean().reset_index()
    monthly["month_name"] = monthly["month"].apply(lambda m: month_names[m - 1])
    season_color = {
        1:  "#4A7FB5", 2:  "#4A7FB5", 12: "#4A7FB5",   # winter — steel blue
        3:  "#4A8C62", 4:  "#4A8C62", 5:  "#4A8C62",   # spring — sage green
        6:  "#C0504D", 7:  "#C0504D", 8:  "#C0504D",   # summer — muted coral
        9:  "#D4893A", 10: "#D4893A", 11: "#D4893A",   # fall   — warm sienna
    }
    fig = go.Figure(go.Bar(
        x=monthly["month_name"],
        y=monthly["demand_gw"],
        marker=dict(color=[season_color[m] for m in monthly["month"]], line=dict(width=0)),
        hovertemplate="%{x}: %{y:.2f} GW<extra></extra>",
    ))
    fig.update_layout(
        **_base_layout(yaxis_title="Average Demand (GW)", height=280, showlegend=False)
    )
    return fig


def seasonal_daily_curves(demand_df: pd.DataFrame, season_colors: dict) -> go.Figure:
    season_map = {
        1: "Winter", 2: "Winter", 12: "Winter",
        3: "Spring", 4: "Spring",  5: "Spring",
        6: "Summer", 7: "Summer",  8: "Summer",
        9: "Fall",  10: "Fall",   11: "Fall",
    }
    df = demand_df.copy()
    df["season"] = df["month"].map(season_map)
    fig = go.Figure()
    for season, color in season_colors.items():
        profile = (
            df[df["season"] == season]
            .groupby("hour_of_day")["demand_gw"]
            .mean().reset_index()
        )
        fig.add_trace(go.Scatter(
            x=profile["hour_of_day"], y=profile["demand_gw"],
            name=season, mode="lines",
            line=dict(color=color, width=2.2),
            hovertemplate=f"{season}  %{{x}}:00  %{{y:.2f}} GW<extra></extra>",
        ))
    fig.update_layout(
        **_base_layout(
            xaxis_title="Hour of Day",
            yaxis_title="Average Demand (GW)",
            xaxis=dict(
                tickvals=list(range(0, 24, 3)),
                ticktext=[f"{h:02d}:00" for h in range(0, 24, 3)],
                gridcolor=_GRID,
            ),
            height=280,
        )
    )
    return fig


def demand_heatmap(demand_df: pd.DataFrame) -> go.Figure:
    pivot = (
        demand_df.groupby(["month", "hour_of_day"])["demand_gw"]
        .mean().unstack(level="hour_of_day")
    )
    month_names = ["Jan","Feb","Mar","Apr","May","Jun",
                   "Jul","Aug","Sep","Oct","Nov","Dec"]
    fig = go.Figure(go.Heatmap(
        z=pivot.values,
        x=[f"{h:02d}:00" for h in pivot.columns],
        y=[month_names[m - 1] for m in pivot.index],
        colorscale=[
            [0.0, "#EBF2FB"],
            [0.4, "#6FA8DC"],
            [0.7, "#1F4E79"],
            [1.0, "#7B2D2D"],
        ],
        colorbar=dict(
            title=dict(text="GW", font=dict(size=11, family=_FONT, color=_T2)),
            thickness=10, outlinewidth=0,
            tickfont=dict(size=10, family=_FONT, color=_T3),
        ),
        hovertemplate="Month: %{y}<br>Hour: %{x}<br><b>%{z:.2f} GW</b><extra></extra>",
    ))
    fig.update_layout(
        xaxis_title="Hour of Day", yaxis_title="Month",
        font=dict(family=_FONT, size=11, color=_T2),
        paper_bgcolor=_BG,
        height=340,
        margin=dict(t=8, b=68, l=52, r=16),
    )
    return fig


# ── Price Projections ──────────────────────────────────────────────────────────

def price_projection_lines(
    projections: pd.DataFrame,
    cols: list[str],
    names: list[str],
    colors: list[str],
    y_label: str,
) -> go.Figure:
    fig = go.Figure()
    for col, name, color in zip(cols, names, colors):
        fig.add_trace(go.Scatter(
            x=projections["year"], y=projections[col],
            name=name, mode="lines+markers",
            line=dict(color=color, width=2.2),
            marker=dict(size=6, symbol="circle", line=dict(color=_CARD, width=1.5)),
        ))
    fig.update_layout(
        **_base_layout(xaxis_title="Year", yaxis_title=y_label, height=340)
    )
    return fig
