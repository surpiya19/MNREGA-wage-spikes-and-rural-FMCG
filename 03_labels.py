"""Step 5: company evidence table and the two-reader labels.

First run : creates data/raw/evidence_<COMPANY>.csv as a blank template.
            Fill it in from the extension's company-evidence output.
Later runs: checks the labels, measures how often the two readers agree,
            and lists disagreements to discuss.

Columns to fill (leave a cell BLANK when the evidence isn't there):
  quarter              e.g. "Q1 FY24"
  results_date         date of the results/earnings call, YYYY-MM-DD
  own_rural_quote      exact quote about the COMPANY'S OWN rural business
  own_rural_source     link / document + page
  market_rural_quote   quote about the overall rural MARKET (e.g. Nielsen)
  market_rural_source  link / document + page
  volume_growth_pct    reported overall volume growth (e.g. UVG), number only
  reader1_label        Accelerating / Steady / Slowing / Insufficient
  reader2_label        same choices, labelled independently
  agreed_label         filled in after you discuss disagreements
  market_rural_label   Accelerating / Steady / Slowing / Insufficient for the
                       MARKET commentary (used by the "follow the market" baseline)

Label question for every quarter: "Compared with the PREVIOUS quarter, did the
company describe its own rural business as gaining momentum, staying similar or
losing momentum?"  "Rural beat urban" on its own is NOT "Accelerating".
"""
import sys

import pandas as pd

import config as C

COLUMNS = ["company", "quarter", "quarter_end", "results_date",
           "own_rural_quote", "own_rural_source", "market_rural_quote", "market_rural_source",
           "volume_growth_pct", "reader1_label", "reader2_label", "agreed_label", "market_rural_label"]
ALLOWED = set(C.LABELS) | {C.INSUFFICIENT}

if not C.EVIDENCE_FILE.exists():
    t = pd.DataFrame({"company": C.COMPANY, "quarter": C.TEMPLATE_QUARTERS})
    t["quarter_end"] = t["quarter"].map(C.quarter_end).dt.date
    for c in COLUMNS:
        if c not in t.columns:
            t[c] = ""
    t[COLUMNS].to_csv(C.EVIDENCE_FILE, index=False)
    print(f"Created blank template: {C.EVIDENCE_FILE}\nFill it in, then run this script again.")
    sys.exit(0)

ev = pd.read_csv(C.EVIDENCE_FILE, dtype=str).fillna("")
for c in COLUMNS:
    if c not in ev.columns:
        sys.exit(f"Evidence file is missing column '{c}'.")
ev["quarter_end"] = ev["quarter"].map(C.quarter_end)
ev = ev.sort_values("quarter_end").reset_index(drop=True)

def norm(x):
    x = str(x).strip().capitalize()
    if x in ("Insufficient information", "Na", "N/a"):
        return C.INSUFFICIENT
    return x  # blank stays blank = "not labelled yet"

problems = []
for c in ["reader1_label", "reader2_label", "agreed_label", "market_rural_label"]:
    ev[c] = ev[c].map(norm)
    bad = ev.loc[~ev[c].isin(ALLOWED | {""}), ["quarter", c]]
    for _, r in bad.iterrows():
        problems.append(f"{r['quarter']}: '{r[c]}' in {c} is not one of {sorted(ALLOWED)}")

# A label needs a quote behind it.
for _, r in ev.iterrows():
    if r["agreed_label"] in C.LABELS and not r["own_rural_quote"].strip():
        problems.append(f"{r['quarter']}: agreed_label is {r['agreed_label']} but own_rural_quote is blank.")

both = ev[(ev["reader1_label"] != "") & (ev["reader2_label"] != "")]
agree = (both["reader1_label"] == both["reader2_label"])
n = len(both)
po = agree.mean() if n else float("nan")

# Cohen's kappa: agreement beyond what chance alone would give.
cats = sorted(ALLOWED)
p1 = both["reader1_label"].value_counts(normalize=True).reindex(cats, fill_value=0)
p2 = both["reader2_label"].value_counts(normalize=True).reindex(cats, fill_value=0)
pe = float((p1 * p2).sum())
kappa = (po - pe) / (1 - pe) if n and pe < 1 else float("nan")

dis = both.loc[~agree, ["quarter", "reader1_label", "reader2_label", "own_rural_quote"]]
dis.to_csv(C.OUT / f"label_disagreements_{C.COMPANY}.csv", index=False)

ev.to_csv(C.CLEAN / f"labels_{C.COMPANY}.csv", index=False)
counts = ev["agreed_label"].replace("", "(not agreed yet)").value_counts()
lines = [
    f"Quarters in table: {len(ev)}",
    f"Both readers labelled: {n};  agreed on {int(agree.sum())} ({po:.0%});  Cohen's kappa = {kappa:.2f}",
    "  (kappa guide: <0.4 weak, 0.4-0.6 moderate, >0.6 good - weak agreement means the label rules need tightening)",
    f"Agreed labels: " + ", ".join(f"{k} {v}" for k, v in counts.items()),
    f"Usable quarters for testing (not Insufficient): {int(ev['agreed_label'].isin(C.LABELS).sum())}",
    f"Disagreements saved to {C.OUT / f'label_disagreements_{C.COMPANY}.csv'}",
]
if problems:
    lines += ["", "PROBLEMS TO FIX:"] + [f"  - {p}" for p in problems]
(C.OUT / f"label_summary_{C.COMPANY}.txt").write_text("\n".join(lines) + "\n")
print("\n".join(lines))
