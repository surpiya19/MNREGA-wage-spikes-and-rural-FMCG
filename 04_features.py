"""Step 6a: build the features that were KNOWN on each prediction date.

For each quarter we fix a prediction date (before results are announced), then
use only MGNREGA months that are at least MGNREGA_LAG_MONTHS old by that date.

Features (all year-on-year, to strip out MGNREGA's strong seasonality):
  pd_yoy        persondays in the latest usable 3 months vs the same months a year earlier
  pd_yoy_chg    pd_yoy minus the same measure one quarter earlier (is it speeding up?)
  wb_yoy / wb_yoy_chg   same, for the proxy wage bill (persondays x avg wage)
  rain_dep      monsoon (Jun-Sep) rainfall departure from normal (%) known on the
                prediction date: the current monsoon so far if we are in Jun-Sep,
                otherwise the last completed monsoon. (A plain 3-month window is
                mostly dry-season months, where normal rain is tiny and % swings
                are huge noise.)
  rain_dep_chg  rain_dep minus the same measure one quarter earlier

Output: data/clean/features_<COMPANY>.csv
"""
import numpy as np
import pandas as pd

import config as C

labels = pd.read_csv(C.CLEAN / f"labels_{C.COMPANY}.csv", parse_dates=["quarter_end"], dtype={"results_date": str})
mg = pd.read_csv(C.CLEAN / "mgnrega_india_monthly.csv", parse_dates=["month_end"]).set_index("month_end")
rain = pd.read_csv(C.CLEAN / "rainfall_india_monthly.csv", parse_dates=["month_end"]).set_index("month_end")

weighted = C.STATE_WEIGHTS and "persondays_idx_w" in mg.columns
PD = "persondays_idx_w" if weighted else "persondays"
WB = "wage_bill_inr_idx_w" if weighted else "wage_bill_inr"


def prediction_date(row):
    if C.PREDICTION_DATE_RULE == "day_before_results":
        rd = pd.to_datetime(row.get("results_date"), errors="coerce")
        if pd.notna(rd):
            return rd - pd.Timedelta(days=1)
        return row["quarter_end"] + pd.Timedelta(days=21)
    return row["quarter_end"]


def window(end, n=C.WINDOW_MONTHS):
    return pd.date_range(end=end, periods=n, freq=pd.offsets.MonthEnd())


def yoy_sum(series, end):
    """Sum over the n months ending at `end` vs the same n months a year earlier."""
    now, before = window(end), window(end - pd.DateOffset(years=1) + pd.offsets.MonthEnd(0))
    a, b = series.reindex(now), series.reindex(before)
    if a.isna().any() or b.isna().any() or b.sum() == 0:
        return np.nan
    return a.sum() / b.sum() - 1


def rain_departure(end):
    """Monsoon departure (%) known at month-end `end` (see docstring)."""
    y = end.year if end.month >= 6 else end.year - 1
    last = min(end, pd.Timestamp(y, 9, 30))
    months = pd.date_range(pd.Timestamp(y, 6, 30), last, freq=pd.offsets.MonthEnd())
    a, n = rain["actual_mm"].reindex(months), rain["normal_mm"].reindex(months)
    if len(months) == 0 or a.isna().any() or n.isna().any():
        return np.nan  # that monsoon is not fully covered by the data
    return (a.sum() / n.sum() - 1) * 100


rows = []
for _, r in labels.iterrows():
    pdate = prediction_date(r)
    mg_end = C.last_usable_month(pdate, C.MGNREGA_LAG_MONTHS)
    rain_end = C.last_usable_month(pdate, C.RAIN_LAG_MONTHS)
    prev_mg_end = mg_end - pd.DateOffset(months=3) + pd.offsets.MonthEnd(0)
    prev_rain_end = rain_end - pd.DateOffset(months=3) + pd.offsets.MonthEnd(0)

    pd_now, pd_prev = yoy_sum(mg[PD], mg_end), yoy_sum(mg[PD], prev_mg_end)
    wb_now, wb_prev = yoy_sum(mg[WB], mg_end), yoy_sum(mg[WB], prev_mg_end)
    rd_now, rd_prev = rain_departure(rain_end), rain_departure(prev_rain_end)
    rows.append({
        "company": r["company"], "quarter": r["quarter"], "quarter_end": r["quarter_end"].date(),
        "prediction_date": pdate.date(),
        "mgnrega_data_through": mg_end.date(),
        "rain_data_through": rain_end.date(),
        "pd_yoy": pd_now, "pd_yoy_chg": pd_now - pd_prev,
        "wb_yoy": wb_now, "wb_yoy_chg": wb_now - wb_prev,
        "rain_dep": rd_now, "rain_dep_chg": rd_now - rd_prev,
        "agreed_label": r["agreed_label"], "market_rural_label": r["market_rural_label"],
        "volume_growth_pct": r.get("volume_growth_pct"),
    })

feat = pd.DataFrame(rows)
feat.to_csv(C.CLEAN / f"features_{C.COMPANY}.csv", index=False)
show = ["quarter", "prediction_date", "mgnrega_data_through", "pd_yoy", "pd_yoy_chg", "wb_yoy_chg", "rain_dep", "agreed_label"]
with pd.option_context("display.width", 160, "display.float_format", "{:.3f}".format):
    print(feat[show].to_string(index=False))
print(f"\nUsing {'exposure-weighted' if weighted else 'all-India'} MGNREGA series.")
print(f"Saved {C.CLEAN / f'features_{C.COMPANY}.csv'}  (blank features = data not available yet at that date)")
