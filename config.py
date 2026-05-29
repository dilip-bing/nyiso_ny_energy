"""
config.py
Central configuration: all constants, paths, color palettes, and model parameters.
Import this module instead of scattering magic numbers across files.
"""

from pathlib import Path

# ── Paths ─────────────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
DATA_RAW = DATA_DIR / "raw"
DATA_PROCESSED = DATA_DIR / "processed"
MODELS_DIR = ROOT / "models"
DASHBOARD_DIR = ROOT / "dashboard"
NOTEBOOKS_DIR = ROOT / "notebooks"

# ── Financial parameters ──────────────────────────────────────────────────────
WACC = 0.07              # weighted average cost of capital (discount rate)
RESERVE_MARGIN = {
    "50% Renewable":    1.15,
    "80% Renewable":    1.12,
    "100% Zero-Carbon": 1.10,
}

# ── System parameters ─────────────────────────────────────────────────────────
ANNUAL_HOURS = 8760
NY_ANNUAL_DEMAND_TWH = 154.0    # NYISO 2023 Gold Book calibration target
NY_PEAK_DEMAND_GW = 28.0        # Summer peak calibration target
NY_BASELINE_CO2_MT = 55.0       # NY power sector 2019 CO₂ emissions (Mt)
US_AVG_RETAIL_PRICE_MWH = 76    # EIA 2023 US average retail electricity ($/MWh)

# ── Technology capacity credit (derate) factors ───────────────────────────────
CAPACITY_CREDIT = {
    "Solar PV (Utility)":   0.15,
    "Onshore Wind":         0.20,
    "Offshore Wind":        0.25,
    "Hydropower":           0.80,
    "Battery Storage (4h)": 1.00,
    "Natural Gas (CCGT)":   0.95,
    "Nuclear":              0.95,
}

# ── Technology sets ───────────────────────────────────────────────────────────
RENEWABLE_TECHS = frozenset({
    "Solar PV (Utility)", "Onshore Wind", "Offshore Wind", "Hydropower"
})
ZERO_CARBON_TECHS = frozenset({
    "Solar PV (Utility)", "Onshore Wind", "Offshore Wind",
    "Hydropower", "Nuclear", "Battery Storage (4h)",
})
ALL_TECHS = (
    "Solar PV (Utility)", "Onshore Wind", "Offshore Wind",
    "Battery Storage (4h)", "Natural Gas (CCGT)", "Nuclear", "Hydropower",
)

# ── NY State capacity limits (GW) ────────────────────────────────────────────
NY_CAPACITY_LIMITS = {
    "Solar PV (Utility)":   {"min_gw": 0.0,  "max_gw": 25.0},
    "Onshore Wind":         {"min_gw": 0.0,  "max_gw": 10.0},
    "Offshore Wind":        {"min_gw": 0.0,  "max_gw": 30.0},
    "Battery Storage (4h)": {"min_gw": 0.0,  "max_gw": 20.0},
    "Natural Gas (CCGT)":   {"min_gw": 2.0,  "max_gw": 15.0},
    "Nuclear":              {"min_gw": 3.0,  "max_gw":  5.0},
    "Hydropower":           {"min_gw": 4.0,  "max_gw":  6.5},
}

# ── Technology learning curve rates (annual capital cost decline) ─────────────
LEARNING_RATES = {
    "Solar PV (Utility)":   0.06,   # 6% per year
    "Onshore Wind":         0.03,   # 3% per year
    "Offshore Wind":        0.045,  # 4.5% per year
    "Battery Storage (4h)": 0.08,   # 8% per year
}

# ── Scenarios ─────────────────────────────────────────────────────────────────
SCENARIOS = ("50% Renewable", "80% Renewable", "100% Zero-Carbon")
SCENARIO_COLORS = {
    "50% Renewable":    "#4A7FB5",  # steel blue
    "80% Renewable":    "#1F4E79",  # deep navy
    "100% Zero-Carbon": "#3A7D55",  # forest green
}
SCENARIO_SHORT = {
    "50% Renewable":    "50% RPS",
    "80% Renewable":    "80% RPS",
    "100% Zero-Carbon": "100% ZCE",
}

# ── Technology color palette (professional muted spectrum) ────────────────────
TECH_COLORS = {
    "Solar PV (Utility)":   "#D4893A",  # warm sienna-amber
    "Onshore Wind":         "#4A7FB5",  # steel blue
    "Offshore Wind":        "#1F4E79",  # deep navy
    "Battery Storage (4h)": "#7B68AE",  # muted amethyst
    "Natural Gas (CCGT)":   "#A94442",  # brick red
    "Nuclear":              "#6B7280",  # slate gray
    "Hydropower":           "#3A8A7B",  # deep teal
}

# ── Dashboard theme (Apple-inspired) ─────────────────────────────────────────
PRIMARY_BLUE   = "#0066CC"   # energy-sector blue (distinctive, near Apple)
PAGE_BG        = "#F5F5F7"   # Apple's exact page background
CARD_BG        = "#FFFFFF"
SIDEBAR_BG     = "#1D1D1F"   # Apple near-black (macOS dark sidebar)
SIDEBAR_2      = "#2C2C2E"
BORDER_COLOR   = "#D2D2D7"   # Apple separator
GRID_COLOR     = "#F0F0F3"   # very subtle gridlines
TEXT_PRIMARY   = "#1D1D1F"   # Apple primary text
TEXT_SECONDARY = "#6E6E73"   # Apple secondary text
TEXT_TERTIARY  = "#86868B"   # Apple tertiary / captions

# ── Seasons (month ranges) ────────────────────────────────────────────────────
SEASONS = {
    "Winter": [12, 1, 2],
    "Spring": [3, 4, 5],
    "Summer": [6, 7, 8],
    "Fall":   [9, 10, 11],
}
SEASON_COLORS = {
    "Winter": "#4A7FB5",   # steel blue
    "Spring": "#4A8C62",   # sage green
    "Summer": "#C0504D",   # muted coral
    "Fall":   "#D4893A",   # warm sienna
}
