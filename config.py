"""Shared settings and helpers for the rural FMCG project.

Edit the SETTINGS block if your exported files use different column names
or you want to change the company, lag or train/test split.
"""
import os
import re
from pathlib import Path

import pandas as pd

# ----------------------------------------------------------------- SETTINGS
# Which company? Override from the command line: python run_all.py --company Dabur
COMPANY = os.environ.get("RURAL_COMPANY", "HUL")

# Thurro guidance: month M is only usable from M+3 onward (recent MGNREGA
# figures get revised). Rainfall is not revised, so it gets no lag by default.
MGNREGA_LAG_MONTHS = 3
RAIN_LAG_MONTHS = 0

# How many months of data make up one "quarter window" of features.
WINDOW_MONTHS = 3

# Share of eligible quarters (oldest first) used to choose the method.
# The rest are held out for evaluation.
TRAIN_FRACTION = 0.6

# When is the prediction made? "day_before_results" uses the results_date
# column of the evidence table (falls back to quarter end + 21 days if blank).
# "quarter_end" predicts on the last day of the quarter.
PREDICTION_DATE_RULE = "day_before_results"

# What are we predicting?
#   "own"    = the company's comments on ITS OWN rural business (agreed_label)
#   "market" = its comments on the overall rural market (market_rural_label)
# Override from the command line: python run_all.py --target market
TARGET = os.environ.get("RURAL_TARGET", "own")
if TARGET not in ("own", "market"):
    raise SystemExit(f"TARGET must be 'own' or 'market', not {TARGET!r}")

LABELS = ["Accelerating", "Steady", "Slowing"]
INSUFFICIENT = "Insufficient"

# Quarters to put in a blank evidence template (Indian fiscal quarters).
TEMPLATE_QUARTERS = [f"Q{q} FY{y}" for y in range(23, 28) for q in range(1, 5)][:-3]  # Q1 FY23..Q1 FY27

# Optional: weight states by your assumed company exposure instead of using
# the all-India total, e.g. {"Uttar Pradesh": 0.15, "Maharashtra": 0.12, ...}.
# Leave as None to use all-India. Document any weights as ASSUMPTIONS.
STATE_WEIGHTS = None

# Map the column headers in YOUR exported files to the names the scripts use.
# Left side = name the scripts expect, right side = header in your CSV.
MGNREGA_COLUMNS = {
    "state": "state",
    "month_end": "month_end",
    "persondays": "persondays",
    "households_worked": "households_worked",
    "avg_wage_paid_inr": "avg_wage_paid_inr",
    "notified_wage_inr": "notified_wage_inr",      # optional
    "persons_demanded": "persons_demanded",        # optional
}
RAIN_COLUMNS = {
    "state": "state",
    "date": "date",
    "actual_mm": "actual_mm",
    "normal_mm": "normal_mm",
}
# --------------------------------------------------------------------------

ROOT = Path(__file__).resolve().parent
DEMO = os.environ.get("RURAL_DEMO") == "1"
_suffix = "_demo" if DEMO else ""
RAW = ROOT / "data" / f"raw{_suffix}"
CLEAN = ROOT / "data" / f"clean{_suffix}"
OUT = ROOT / f"outputs{_suffix}"
for _p in (RAW, CLEAN, OUT):
    _p.mkdir(parents=True, exist_ok=True)

MGNREGA_FILE = RAW / "mgnrega_state_monthly.csv"
RAIN_FILE = RAW / "rainfall_state_daily.csv"
EVIDENCE_FILE = RAW / f"evidence_{COMPANY}.csv"
# Output name tag: results_HUL.txt for own, results_HUL_market.txt for market.
TAG = COMPANY if TARGET == "own" else f"{COMPANY}_market"
TARGET_NAME = "own rural business" if TARGET == "own" else "overall rural market"

ALL_INDIA_NAMES = {"all india", "india", "total", "all-india"}


def month_end(s):
    """Parse anything date-like and snap it to the month end."""
    return pd.to_datetime(s, errors="coerce") + pd.offsets.MonthEnd(0)


def fiscal_year(ts):
    """Indian fiscal year label number: Apr 2023-Mar 2024 -> 2024."""
    return ts.year + 1 if ts.month >= 4 else ts.year


def quarter_end(q):
    """'Q1 FY24' -> 2023-06-30 (Indian fiscal quarters, FY starts in April)."""
    m = re.match(r"\s*Q([1-4])\s*FY\s*(\d{2,4})\s*$", str(q).upper())
    if not m:
        raise ValueError(f"Cannot parse quarter label: {q!r} (expected e.g. 'Q1 FY24')")
    qn, fy = int(m.group(1)), int(m.group(2))
    fy = fy + 2000 if fy < 100 else fy
    month = {1: 6, 2: 9, 3: 12, 4: 3}[qn]
    year = fy - 1 if qn in (1, 2, 3) else fy
    return pd.Timestamp(year, month, 1) + pd.offsets.MonthEnd(0)


def rename_columns(df, mapping, required, file_label):
    inverse = {v: k for k, v in mapping.items()}
    df = df.rename(columns=inverse)
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise SystemExit(
            f"{file_label}: missing columns {missing}. Found {list(df.columns)}. "
            "Fix the column mapping in config.py."
        )
    return df


def last_usable_month(prediction_date, lag_months):
    """Latest month-end M such that M + lag months <= prediction date."""
    cutoff = pd.Timestamp(prediction_date) - pd.DateOffset(months=lag_months)
    return (cutoff + pd.offsets.MonthEnd(0)) if cutoff.is_month_end else (cutoff - pd.offsets.MonthEnd(1))
