"""Step 3b: turn daily state rainfall into monthly state and all-India tables.

Input : data/raw/rainfall_state_daily.csv  (one row per state per day,
        SINGLE-DAY actual and normal rainfall in mm)
Output: data/clean/rainfall_state_monthly.csv
        data/clean/rainfall_india_monthly.csv
        outputs/rainfall_data_notes.txt
"""
import pandas as pd

import config as C

notes = []
df = pd.read_csv(C.RAIN_FILE)
df = C.rename_columns(df, C.RAIN_COLUMNS, ["state", "date", "actual_mm", "normal_mm"], "Rainfall file")
df["date"] = pd.to_datetime(df["date"], errors="coerce")
df = df.dropna(subset=["date"])
df["state"] = df["state"].astype(str).str.strip().str.title()
for c in ["actual_mm", "normal_mm"]:
    df[c] = pd.to_numeric(df[c], errors="coerce")
df = df.drop_duplicates(["state", "date"], keep="last").sort_values(["state", "date"])

# --- Cumulative check: month-to-date totals never fall within a month --------
df["month_end"] = C.month_end(df["date"])
d = df.groupby(["state", "month_end"])["normal_mm"].diff().dropna()
if len(d) and (d >= 0).mean() > 0.95:
    raise SystemExit("Normal rainfall never falls within a month: this looks like a MONTH-TO-DATE export. "
                     "Export single-day values instead, or take the last day of each month as the monthly total.")
notes.append("Daily values look like single-day amounts (not running totals).")

monthly = (df.groupby(["state", "month_end"])
             .agg(actual_mm=("actual_mm", "sum"), normal_mm=("normal_mm", "sum"),
                  days_reported=("actual_mm", "count"))
             .reset_index())
monthly["days_in_month"] = monthly["month_end"].dt.day
monthly["complete"] = monthly["days_reported"] >= monthly["days_in_month"] - 2
MONTHLY_INPUT = df.groupby(["state", "month_end"]).size().max() == 1
if MONTHLY_INPUT:
    # Input is already one row per state per month (monthly totals), not daily.
    # days_with_data = days that had data; missing = days in month - days_with_data.
    notes.append("Input has one row per state per month: treated as monthly totals.")
    if "days_with_data" in df.columns:
        dwd = pd.to_numeric(df.set_index(["state", "month_end"])["days_with_data"], errors="coerce")
        monthly["days_reported"] = monthly.set_index(["state", "month_end"]).index.map(dwd)
        monthly["complete"] = monthly["days_reported"] >= monthly["days_in_month"] - 2
        short = monthly[monthly["days_reported"] < monthly["days_in_month"] - 5]
        if len(short):
            notes.append("Months with 5+ days missing (kept: actual and normal cover the same days, so the departure "
                         "is valid for the days reported, but it may miss heavy-rain days): "
                         + ", ".join(f"{r.month_end:%b %Y} ({int(r.days_in_month - r.days_reported)} of {r.days_in_month} days missing)"
                                     for r in short.itertuples()))
    else:
        monthly["complete"] = True
monthly["departure_pct"] = (monthly["actual_mm"] / monthly["normal_mm"] - 1) * 100
inc = monthly[~monthly["complete"]]
_names = df["state"].dropna().unique()
if len(_names) == 1 and "all states" in str(_names[0]).lower():
    _cov = f"one all-India series ('{_names[0]}': the file has no separate state rows, so state weights can't be applied)"
else:
    _cov = f"{len(_names)} states"
notes.append(f"Coverage: {df['date'].min():%d %b %Y} to {df['date'].max():%d %b %Y}, {_cov}.")
notes.append(f"{len(inc)} month(s) have more than 2 missing days and are flagged complete=False"
             + (f": {', '.join(f'{d:%b %Y}' for d in inc['month_end'])}" if len(inc) else "") + ".")

# All-India: total actual / total normal across states. This weights states by
# their normal rainfall, not by area or farm output - say so in the deck.
# Monthly input: partial months are kept (see note above). Daily input: only complete months.
good = monthly if MONTHLY_INPUT else monthly[monthly["complete"]]
india = good.groupby("month_end")[["actual_mm", "normal_mm"]].sum().reset_index()
india["states_reporting"] = good.groupby("month_end")["state"].count().values
india["departure_pct"] = (india["actual_mm"] / india["normal_mm"] - 1) * 100
notes.append("All-India departure = sum of state actuals / sum of state normals - 1 (normal-weighted, not area-weighted).")

# Monsoon (Jun-Sep) departure by year, handy for the story slides.
mon = india[india["month_end"].dt.month.isin([6, 7, 8, 9])]
season = mon.groupby(mon["month_end"].dt.year).agg(actual=("actual_mm", "sum"), normal=("normal_mm", "sum"),
                                                   months=("actual_mm", "count"))
season["departure_pct"] = (season["actual"] / season["normal"] - 1) * 100
for y, r in season.iterrows():
    flag = "" if r["months"] == 4 else f" (only {int(r['months'])} of 4 months)"
    notes.append(f"Monsoon {y}: {r['departure_pct']:+.0f}% vs normal{flag}")

monthly.to_csv(C.CLEAN / "rainfall_state_monthly.csv", index=False)
india.to_csv(C.CLEAN / "rainfall_india_monthly.csv", index=False)
(C.OUT / "rainfall_data_notes.txt").write_text("\n".join(notes) + "\n")
print("\n".join(notes))
print(f"\nSaved clean rainfall tables to {C.CLEAN}")
