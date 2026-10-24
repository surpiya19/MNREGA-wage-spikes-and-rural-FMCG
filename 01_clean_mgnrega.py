"""Step 3a: clean the MGNREGA state-level monthly export.

Input : data/raw/mgnrega_state_monthly.csv  (one row per state per month)
Output: data/clean/mgnrega_state_monthly.csv
        data/clean/mgnrega_india_monthly.csv
        outputs/mgnrega_data_notes.txt   <- read this and keep it for the deck
"""
import numpy as np
import pandas as pd

import config as C

REQUIRED = ["state", "month_end", "persondays", "avg_wage_paid_inr"]
NUMERIC = ["persondays", "households_worked", "avg_wage_paid_inr",
           "notified_wage_inr", "persons_demanded"]

notes = []
df = pd.read_csv(C.MGNREGA_FILE)
df = C.rename_columns(df, C.MGNREGA_COLUMNS, REQUIRED, "MGNREGA file")
df["month_end"] = C.month_end(df["month_end"])
bad_dates = df["month_end"].isna().sum()
if bad_dates:
    notes.append(f"Dropped {bad_dates} rows with unreadable dates.")
df = df.dropna(subset=["month_end"])
for c in NUMERIC:
    if c in df.columns:
        df[c] = pd.to_numeric(df[c], errors="coerce")

df["state"] = df["state"].astype(str).str.strip()
is_india = df["state"].str.lower().isin(C.ALL_INDIA_NAMES)
india_reported = df[is_india].copy()
states = df[~is_india].copy()

dupes = states.duplicated(["state", "month_end"]).sum()
if dupes:
    notes.append(f"Found {dupes} duplicate state-month rows; kept the last one.")
    states = states.drop_duplicates(["state", "month_end"], keep="last")

states = states.sort_values(["state", "month_end"])
states["fy"] = states["month_end"].apply(C.fiscal_year)

# --- Cumulative check -------------------------------------------------------
# A financial-year running total never falls between consecutive months inside
# the same FY. Real monthly persondays fall often (they peak in May-June).
def share_non_decreasing(g):
    d = g["persondays"].diff().dropna()
    return np.nan if d.empty else (d >= 0).mean()

nd = states.groupby(["state", "fy"]).apply(share_non_decreasing).dropna()
fully_monotone = (nd == 1).mean()
notes.append(f"Share of state-FYs where persondays never fall month to month: {fully_monotone:.0%}.")
if fully_monotone > 0.8:
    notes.append("=> Looks CUMULATIVE (financial-year-to-date). Converting to single-month values by differencing within each FY.")
    for c in ["persondays", "households_worked", "persons_demanded"]:
        if c in states.columns:
            first = states.groupby(["state", "fy"])[c].transform("first")
            diff = states.groupby(["state", "fy"])[c].diff()
            states[c] = diff.fillna(first)
    notes.append("   Households cannot be safely de-cumulated (same household counted again); treat that field with care.")
else:
    notes.append("=> Looks like SINGLE-MONTH values. No conversion applied.")

# --- Missing data report ----------------------------------------------------
all_months = pd.date_range(states["month_end"].min(), states["month_end"].max(), freq=pd.offsets.MonthEnd())
grid = pd.MultiIndex.from_product([states["state"].unique(), all_months], names=["state", "month_end"])
states = states.set_index(["state", "month_end"]).reindex(grid).reset_index()
states["fy"] = states["month_end"].apply(C.fiscal_year)
miss = states["persondays"].isna().groupby(states["state"]).sum()
miss = miss[miss > 0].sort_values(ascending=False)
notes.append(f"Coverage: {all_months.min():%b %Y} to {all_months.max():%b %Y}, {states['state'].nunique()} states.")
notes.append("States with missing persondays months: " + (", ".join(f"{s} ({n})" for s, n in miss.items()) if len(miss) else "none"))

# --- Derived measures -------------------------------------------------------
# No direct wage-payment series exists, so build a PROXY wage bill.
states["wage_bill_inr"] = states["persondays"] * states["avg_wage_paid_inr"]
notes.append("wage_bill_inr = persondays x average wage paid per day. This is a constructed proxy, not reported payments.")
if "persons_demanded" in states.columns:
    notes.append("persons_demanded is a count of PEOPLE asking for work; persondays is DAYS worked. Different units - don't compare levels.")

def add_yoy(frame, cols, by=None):
    for c in cols:
        if c not in frame.columns:
            continue
        lag = frame.groupby(by)[c].shift(12) if by else frame[c].shift(12)
        frame[f"{c}_yoy"] = frame[c] / lag - 1
    return frame

states = states.sort_values(["state", "month_end"])
states = add_yoy(states, ["persondays", "wage_bill_inr", "persons_demanded"], by="state")

# --- All-India series (sum of states; wage = persondays-weighted average) ---
agg = {"persondays": "sum", "wage_bill_inr": "sum"}
for c in ["households_worked", "persons_demanded"]:
    if c in states.columns:
        agg[c] = "sum"
counts = states.groupby("month_end")["persondays"].count().rename("states_reporting")
india = states.groupby("month_end").agg(agg).join(counts)
india["avg_wage_paid_inr"] = india["wage_bill_inr"] / india["persondays"]
full = india["states_reporting"].max()
thin = india[india["states_reporting"] < 0.9 * full]
if len(thin):
    notes.append(f"WARNING: {len(thin)} months have <90% of states reporting; all-India totals there are understated: "
                 + ", ".join(f"{d:%b %Y}" for d in thin.index))
india = india.reset_index()

if C.STATE_WEIGHTS:
    w = pd.Series(C.STATE_WEIGHTS, name="w")
    unknown = set(w.index) - set(states["state"])
    if unknown:
        notes.append(f"WARNING: STATE_WEIGHTS names not found in data: {sorted(unknown)}")
    s = states.merge(w, left_on="state", right_index=True)
    for c in ["persondays", "wage_bill_inr"]:
        idx = s.groupby("state")[c].transform(lambda x: x / x.mean())  # normalise state size away
        s[f"{c}_idx_w"] = idx * s["w"]
    wtd = s.groupby("month_end")[["persondays_idx_w", "wage_bill_inr_idx_w"]].sum().reset_index()
    india = india.merge(wtd, on="month_end", how="left")
    notes.append("Added exposure-weighted indices using STATE_WEIGHTS (assumed, not disclosed, weights).")

india = india.sort_values("month_end")
india = add_yoy(india, ["persondays", "wage_bill_inr", "persons_demanded",
                        "persondays_idx_w", "wage_bill_inr_idx_w"])

if not india_reported.empty:
    chk = india.merge(india_reported[["month_end", "persondays"]], on="month_end", suffixes=("", "_reported"))
    gap = (chk["persondays"] / chk["persondays_reported"] - 1).abs().median()
    notes.append(f"Sum of states vs reported All-India persondays: median gap {gap:.1%}.")

# --- Big year-on-year swings worth investigating ----------------------------
big = india[india["persondays_yoy"].abs() > 0.3]
if len(big):
    notes.append("Months with persondays YoY beyond +/-30% (check for revisions or scheme changes before modelling): "
                 + ", ".join(f"{d:%b %Y} ({v:+.0%})" for d, v in zip(big["month_end"], big["persondays_yoy"])))

states.drop(columns="fy").to_csv(C.CLEAN / "mgnrega_state_monthly.csv", index=False)
india.to_csv(C.CLEAN / "mgnrega_india_monthly.csv", index=False)
(C.OUT / "mgnrega_data_notes.txt").write_text("\n".join(notes) + "\n")
print("\n".join(notes))
print(f"\nSaved clean MGNREGA tables to {C.CLEAN}")
