"""Build pipeline inputs from the second labelling pass (labels/) - Thurro feedback, Nov 2026.

What it does
  1. Market-wide rural trend (Thurro: make this the PRIMARY target).
     Each company-quarter market label comes from:
       - HUL, Dabur : market_rural_label in data/raw/evidence_<co>.csv (3-reader majority, Q1 FY23-Q1 FY27)
       - Marico, Emami: labels/market_wide/draft_market_labels_marico_emami.csv (drafted from the
         market_rural_figure text in labels/<co>/labels_final.csv; human-reviewed)
     The market-wide label for a quarter is the most common direction across the companies that
     commented. Ties, or an Accelerating vs Slowing split, count as Steady (the cautious call).
     -> labels/market_wide/market_labels_by_company.csv, labels/market_wide/market_wide_labels.csv
     -> data/raw/evidence_Market.csv  (run with --company Market --target market)
  2. Own-rural labels (Thurro: SECONDARY check). FY24 onward now use labels/<co>/labels_final.csv
     (two labellers + reconciler, guide v2); FY23 keeps the older 3-reader labels for HUL and Dabur.
     Blank = Insufficient and is excluded from scoring.
     -> data/raw/evidence_<HUL|Dabur|Marico|Emami>.csv
  3. Cut-off: Q1 FY27 is the last quarter (Thurro: "Q1FY27 is fine"). Q2 FY27 rows are dropped.

Run once after editing any label file:  python build_label_inputs.py
"""
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent
RAW = ROOT / "data" / "raw"
LAB = ROOT / "labels"
MW = LAB / "market_wide"
LAST_QUARTER = "Q1 FY27"
COLS = ["company", "quarter", "quarter_end", "results_date", "own_rural_quote", "own_rural_source",
        "market_rural_quote", "market_rural_source", "volume_growth_pct", "reader1_label",
        "reader2_label", "agreed_label", "market_rural_label", "label_source"]


def qkey(q):
    q = str(q).upper().replace(" ", "")
    return int(q.split("FY")[1]) * 10 + int(q[1])


def cap(x):
    x = "" if pd.isna(x) else str(x).strip()
    if x.lower() in ("", "blank", "nan", "insufficient"):
        return "Insufficient"
    return x.capitalize()


LAST = qkey(LAST_QUARTER)
new = pd.read_csv(LAB / "rural_labels_all_companies.csv")
new = new[new["quarter"].map(qkey) <= LAST]
draft = pd.read_csv(MW / "draft_market_labels_marico_emami.csv")
draft = draft[draft["quarter"].map(qkey) <= LAST]

# ---------------------------------------------------------------- own labels
evid = {}
for co in ["HUL", "Dabur", "Marico", "Emami"]:
    n = new[new["company"] == co].set_index("quarter")
    old_path = RAW / f"evidence_{co}.csv"
    if old_path.exists():
        old = pd.read_csv(old_path, dtype=str).fillna("")
        old = old[old["quarter"].map(qkey) <= LAST].copy()
    else:
        old = pd.DataFrame({"company": co, "quarter": n.index})
        for c in COLS:
            if c not in old.columns:
                old[c] = ""
    old = old.set_index("quarter")
    # quarters present in either source
    quarters = sorted(set(old.index) | set(n.index), key=qkey)
    old = old.reindex(quarters).fillna("")
    old["company"] = co
    if "label_source" not in old.columns:
        old["label_source"] = ""
    for q in quarters:
        if q in n.index:
            r = n.loc[q]
            old.loc[q, "agreed_label"] = cap(r["final_label"])
            old.loc[q, "reader1_label"] = cap(r["label_A"])
            old.loc[q, "reader2_label"] = cap(r["label_B"])
            old.loc[q, "own_rural_source"] = "" if pd.isna(r["evidence_link"]) else r["evidence_link"]
            note = "" if pd.isna(r["reconciliation_note"]) else str(r["reconciliation_note"])
            if old.loc[q, "agreed_label"] != "Insufficient":
                old.loc[q, "own_rural_quote"] = note[:400] or "see labels/<company>/labels_final.csv"
            else:
                old.loc[q, "own_rural_quote"] = ""
            if pd.notna(r["overall_volume_growth_pct"]):
                old.loc[q, "volume_growth_pct"] = str(r["overall_volume_growth_pct"])
            if pd.notna(r["market_rural_figure"]) and not old.loc[q, "market_rural_quote"]:
                old.loc[q, "market_rural_quote"] = r["market_rural_figure"]
            old.loc[q, "label_source"] = "Own label: 2nd pass (2 labellers + reconciler, guide v2); human spot-checked non-steady labels"
        elif not old.loc[q, "label_source"]:
            old.loc[q, "label_source"] = "Own label: 1st pass (3 AI readers, majority)"
    if co in ("Marico", "Emami"):
        d = draft[draft["company"] == co].set_index("quarter")
        for q in quarters:
            if q in d.index:
                old.loc[q, "market_rural_label"] = d.loc[q, "market_label"]
    old["quarter_end"] = [pd.Timestamp(year=(2000 + qkey(q) // 10) - (1 if qkey(q) % 10 in (1, 2, 3) else 0),
                                       month={1: 6, 2: 9, 3: 12, 4: 3}[qkey(q) % 10], day=1) + pd.offsets.MonthEnd(0)
                          for q in quarters]
    old["quarter_end"] = pd.to_datetime(old["quarter_end"]).dt.date
    out = old.reset_index()[COLS]
    out.to_csv(RAW / f"evidence_{co}.csv", index=False)
    evid[co] = out
    print(f"{co}: {len(out)} quarters, own labels: " + ", ".join(f"{k} {v}" for k, v in out['agreed_label'].replace('', 'Insufficient').value_counts().items()))

# ------------------------------------------------------- market-wide target
rows = []
for co, ev in evid.items():
    for _, r in ev.iterrows():
        lab = cap(r["market_rural_label"])
        src = ("3 AI readers, majority (1st pass)" if co in ("HUL", "Dabur")
               else "Drafted from 2nd-pass market text; human-reviewed")
        rows.append({"company": co, "quarter": r["quarter"], "market_label": lab, "label_source": src,
                     "market_text": r["market_rural_quote"], "results_date": r["results_date"]})
by_co = pd.DataFrame(rows).sort_values(["quarter", "company"], key=lambda s: s.map(qkey) if s.name == "quarter" else s)
by_co.to_csv(MW / "market_labels_by_company.csv", index=False)

out = []
for q, g in by_co.groupby("quarter", sort=False):
    votes = g[g["market_label"] != "Insufficient"]
    counts = votes["market_label"].value_counts()
    if counts.empty:
        lab, conf = "Insufficient", ""
    else:
        top = counts[counts == counts.max()]
        split = {"Accelerating", "Slowing"} <= set(counts.index) and counts.get("Accelerating", 0) == counts.get("Slowing", 0)
        lab = "Steady" if (len(top) > 1 or split) else top.index[0]
        agree = counts.max() / counts.sum()
        conf = "high" if agree >= 0.75 and len(top) == 1 else "low"
    dates = pd.to_datetime(g["results_date"], errors="coerce").dropna()
    out.append({"quarter": q, "market_wide_label": lab, "confidence": conf,
                "votes": "; ".join(f"{r.company}: {r.market_label}" for r in g.itertuples()),
                "n_companies_commenting": int(len(votes)),
                "first_results_date": dates.min().date() if len(dates) else ""})
mw = pd.DataFrame(out).sort_values("quarter", key=lambda s: s.map(qkey))
mw.to_csv(MW / "market_wide_labels.csv", index=False)

ev = pd.DataFrame({"company": "Market", "quarter": mw["quarter"]})
ev["quarter_end"] = evid["HUL"].set_index("quarter").reindex(mw["quarter"])["quarter_end"].values
ev["results_date"] = mw["first_results_date"].values
ev["own_rural_quote"] = "Market-wide consensus. Votes: " + mw["votes"].values
ev["own_rural_source"] = "labels/market_wide/market_labels_by_company.csv"
ev["market_rural_quote"] = ""
ev["market_rural_source"] = ""
ev["volume_growth_pct"] = ""
ev["reader1_label"] = ""
ev["reader2_label"] = ""
ev["agreed_label"] = mw["market_wide_label"].values
ev["market_rural_label"] = mw["market_wide_label"].values
ev["label_source"] = "Market-wide consensus across HUL, Dabur, Marico, Emami (ties = Steady)"
ev[COLS].to_csv(RAW / "evidence_Market.csv", index=False)
print("\nMarket-wide labels:")
print(mw[["quarter", "market_wide_label", "confidence", "votes"]].to_string(index=False))
