"""Creates FAKE input files in data/raw_demo/ so you can test the pipeline
before your real exports are ready. Never use these numbers in the deck.

Run:  python run_all.py --demo
"""
import os
os.environ["RURAL_DEMO"] = "1"

import numpy as np
import pandas as pd

import config as C

rng = np.random.default_rng(7)
states = ["Uttar Pradesh", "Bihar", "Rajasthan", "Maharashtra", "Tamil Nadu", "West Bengal"]
months = pd.period_range("2019-04", "2026-09", freq="M").to_timestamp(how="end").normalize()
season = {4: 1.3, 5: 1.7, 6: 1.4, 7: 0.8, 8: 0.7, 9: 0.65, 10: 0.7, 11: 0.8, 12: 1.0, 1: 1.0, 2: 0.95, 3: 0.75}
cycle = np.sin(np.arange(len(months)) / 7)

rows = []
for s in states:
    base = rng.uniform(1e7, 4e7)
    wage = rng.uniform(180, 220)
    for i, m in enumerate(months):
        pdays = base * season[m.month] * (1 + 0.15 * cycle[i]) * rng.normal(1, 0.05)
        rows.append({"state": s, "month_end": m.date(), "persondays": round(pdays),
                     "households_worked": round(pdays / 9), "avg_wage_paid_inr": round(wage * 1.005 ** i),
                     "notified_wage_inr": round(wage * 1.005 ** i * 1.08), "persons_demanded": round(pdays / 7)})
pd.DataFrame(rows).to_csv(C.MGNREGA_FILE, index=False)

days = pd.date_range("2022-09-06", "2026-10-22", freq="D")
normal = 2 + 10 * np.exp(-((days.dayofyear - 210) / 40.0) ** 2)
rr = []
for s in states:
    for d, n in zip(days, normal):
        rr.append({"state": s, "date": d.date(), "normal_mm": round(n, 1),
                   "actual_mm": round(max(0, n * rng.lognormal(0, 0.6)), 1)})
pd.DataFrame(rr).to_csv(C.RAIN_FILE, index=False)

ev = pd.DataFrame({"company": C.COMPANY, "quarter": C.TEMPLATE_QUARTERS})
ev["quarter_end"] = ev["quarter"].map(C.quarter_end)
ev["results_date"] = (ev["quarter_end"] + pd.Timedelta(days=24)).dt.date
labs = rng.choice(C.LABELS + [C.INSUFFICIENT], size=len(ev), p=[0.3, 0.35, 0.25, 0.1])
ev["own_rural_quote"] = np.where(labs == C.INSUFFICIENT, "", "demo quote")
ev["own_rural_source"] = ""
ev["market_rural_quote"] = "demo market quote"
ev["market_rural_source"] = ""
ev["volume_growth_pct"] = rng.integers(-2, 8, size=len(ev))
ev["reader1_label"] = labs
ev["reader2_label"] = np.where(rng.random(len(ev)) < 0.8, labs, rng.choice(C.LABELS, size=len(ev)))
ev["agreed_label"] = labs
ev["market_rural_label"] = rng.choice(C.LABELS, size=len(ev))
ev["quarter_end"] = ev["quarter_end"].dt.date
ev.to_csv(C.EVIDENCE_FILE, index=False)
print(f"Demo inputs written to {C.RAW}")
