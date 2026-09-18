# Paths and column names
# Every other script will import this one

from pathlib import Path

# config.py sits in src/, so the repo folder is one level up
REPO = Path(__file__).resolve().parents[1]
CSV = REPO / "data" / "raw" / "EngineFaultDB_Final.csv"
RESULTS = REPO / "results"
FIGURES = REPO / "figures"

# This maps the header text (lower case) to the name I use in code.
COLUMN_NAMES = {
    "fault": "fault",
    "map": "map",
    "tps": "tps",
    "force": "force",
    "power": "power",
    "rpm": "rpm",
    "consumption l/h": "cons_lph",
    "consumption l/100km": "cons_l100km",
    "speed": "speed",
    "co": "co",
    "hc": "hc",
    "co2": "co2",
    "o2": "o2",
    "lambda": "lambda_",
    "afr": "afr",
}

LABEL = "fault"
FEATURES = [name for name in COLUMN_NAMES.values() if name != LABEL]

# MAP and TPS are documented in kPa and percent, but their ranges look like volts.
UNITS_IN_QUESTION = ["map", "tps"]
