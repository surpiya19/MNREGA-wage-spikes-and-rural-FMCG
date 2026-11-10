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
MGNREGA_LAG_MONTHS = int(os.environ.get("RURAL_MGNREGA_LAG", "3"))
if MGNREGA_LAG_MONTHS < 3:
    raise ValueError("MGNREGA lag must be at least 3 months (Thurro revision guidance)")
RAIN_LAG_MONTHS = 0

# How many months of data make up one "quarter window" of features.
WINDOW_MONTHS = 3

# Share of eligible quarters (oldest first) used to choose the method.
# The rest are held out for evaluation.
TRAIN_FRACTION = 0.6

# When is the prediction made? "day_before_results" uses the results_date
# column of the evidence table (falls back to quarter end + 21 days if blank).
# "quarter_end" predicts on the last day of the quarter.
PREDICTION_DATE_RULE = os.environ.get("RURAL_PREDICTION_RULE", "day_before_results")
if PREDICTION_DATE_RULE not in ("day_before_results", "quarter_end", "early_next_quarter"):
    raise ValueError("Unknown RURAL_PREDICTION_RULE")

# What are we predicting?
#   "own"    = the company's comments on ITS OWN rural business (agreed_label)
#   "market" = its comments on the overall rural market (market_rural_label)
# Override from the command line: python run_all.py --target market
TARGET = os.environ.get("RURAL_TARGET", "own")
if TARGET not in ("own", "market"):
    raise SystemExit(f"TARGET must be 'own' or 'market', not {TARGET!r}")

# Thurro feedback (Nov 2026): MGNREGA months from Aug 2025 reflect the 60% first-half
# spending cap more than rural demand, and VB-G RAM G replaced MGNREGA on 1 Jul 2026
# (same units, new rules). Quarters whose MGNREGA data reaches these months are
# reported separately. With the Q1 FY27 cut-off and the 3-month lag, no post-Jul-2026
# month is ever used, but the flag is kept so later runs stay honest.
SPENDING_CAP_FROM = "2025-08-31"
REGIME_BREAK_FROM = "2026-07-31"

# Walk-forward test: refit on every earlier quarter, predict the next one.
# The first prediction needs at least this many labelled quarters to learn from.
WALK_FORWARD_MIN_TRAIN = 5

# Analysis window. FY23 own and market labels for HUL and Dabur come from the first pass
# (3 AI readers, majority vote, never human spot-checked), and their "reader 1 / reader 2"
# columns are not independent labellers, so FY23 is left out of every test and of the
# agreement scores. Q1 FY24 is the first quarter of the reconciled second pass.
# Q1 FY27 is the last quarter (Thurro: "Q1FY27 is fine").
FIRST_QUARTER = "Q1 FY24"
LAST_QUARTER = "Q1 FY27"

# A rule is only fitted and tested when at least this many labelled quarters are
# available for training. With fewer, any rule can fit the training quarters
# perfectly and the test says nothing.
MIN_TRAIN_QUARTERS = 6

# Market-wide consensus when the companies' votes tie (or split Accelerating vs Slowing).
# "Insufficient" (team rule from 9 Nov 2026): no consensus, left out of scoring.
# "Steady": the earlier convention, kept as a sensitivity option.
MARKET_TIE_RULE = os.environ.get("RURAL_MARKET_TIE", "Insufficient")
assert MARKET_TIE_RULE in ("Insufficient", "Steady"), MARKET_TIE_RULE

LABELS = ["Accelerating", "Steady", "Slowing"]
INSUFFICIENT = "Insufficient"

# Quarters to put in a blank evidence template (Indian fiscal quarters).
TEMPLATE_QUARTERS = [f"Q{q} FY{y}" for y in range(23, 28) for q in range(1, 5)][:-3]  # Q1 FY23..Q1 FY27 (Thurro: stop at Q1 FY27)

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
CLEAN = Path(os.environ.get("RURAL_CLEAN_DIR", str(ROOT / "data" / f"clean{_suffix}")))
OUT = Path(os.environ.get("RURAL_OUTPUT_DIR", str(ROOT / f"outputs{_suffix}")))
for _p in (RAW, CLEAN, OUT):
    _p.mkdir(parents=True, exist_ok=True)

MGNREGA_FILE = RAW / "mgnrega_state_monthly.csv"
RAIN_FILE = RAW / "rainfall_state_daily.csv"
EVIDENCE_FILE = RAW / f"evidence_{COMPANY}.csv"
# Output name tag: results_HUL.txt for own, results_HUL_market.txt for market.
TAG = COMPANY if TARGET == "own" else f"{COMPANY}_market"
TARGET_NAME = "own rural business" if TARGET == "own" else "overall rural market"
if COMPANY == "Market":
    TARGET_NAME = "market-wide rural trend (consensus across HUL, Dabur, Marico, Emami)"

ALL_INDIA_NAMES = {"all india", "india", "total", "all-india"}


def month_end(s):
    """Parse anything date-like and snap it to the month end."""
    return pd.to_datetime(s, errors="coerce") + pd.offsets.MonthEnd(0)


def fiscal_year(ts):
    """Indian fiscal year label number: Apr 2023-Mar 2024 -> 2024."""
    return ts.year + 1 if ts.month >= 4 else ts.year


def in_window(q):
    """True when quarter label q is inside FIRST_QUARTER..LAST_QUARTER."""
    return quarter_end(FIRST_QUARTER) <= quarter_end(q) <= quarter_end(LAST_QUARTER)


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
