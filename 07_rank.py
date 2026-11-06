"""Step 8: quarterly ranked list of companies (Thurro deliverable) and its scoring.

How a company is ranked in a quarter
  1. Market call   : the market-wide MGNREGA rule's WALK-FORWARD prediction for that quarter
                     (outputs/predictions_Market_market.csv), i.e. made only with earlier quarters.
                     Accelerating = +1, Steady = 0, Slowing = -1.
  2. Exposure      : the company's rural share of India sales (data/raw/company_exposure.csv).
                     Marico's share is an ASSUMPTION (no disclosure found).
  3. Score         : market call x rural share. A rural pickup helps the most rural-exposed
                     company most; a rural slowdown hurts it most.
  4. Ties          : when the market call is Steady every score is 0. Ties are broken by the
                     company's own rural label from its PREVIOUS call (momentum it reported),
                     then by rural share.
State-level weights are not used: the MGNREGA input is an all-India series and no company
publishes sales by state (Thurro confirmed), so the companies differ only by rural share.

Scoring (reported with coverage, blanks excluded - Thurro guidance)
  - Market call vs the realised market-wide label.
  - Company direction (= market call) vs each company's realised OWN rural label, where given.
  - Robustness: ranking re-run with equal exposure weights; we report how often the order changes.

Outputs: outputs/ranked_list.csv, outputs/ranking_scores.txt
"""
import pandas as pd

import config as C

SIGN = {"Accelerating": 1, "Steady": 0, "Slowing": -1}
COS = ["HUL", "Dabur", "Marico", "Emami"]

mk = pd.read_csv(C.OUT / "predictions_Market_market.csv")
mk = mk[mk["wf_pred"].notna() & (mk["wf_pred"] != "")]
expo = pd.read_csv(C.RAW / "company_exposure.csv").set_index("company")
ev = {c: pd.read_csv(C.RAW / f"evidence_{c}.csv", dtype=str).fillna("").set_index("quarter") for c in COS}
quarters = list(ev["HUL"].index)


def prev_q(q):
    i = quarters.index(q)
    return quarters[i - 1] if i > 0 else None


def own(c, q):
    if q is None or q not in ev[c].index:
        return ""
    lab = ev[c].loc[q, "agreed_label"]
    return lab if lab in C.LABELS else ""


def rank_quarter(q, call, weights, share_tiebreak=True):
    rows = []
    for c in COS:
        p = own(c, prev_q(q))
        rows.append({"company": c, "score": SIGN[call] * weights[c],
                     "tiebreak_prev_own": SIGN.get(p, 0), "rural_share": weights[c], "prev_own_label": p})
    d = pd.DataFrame(rows)
    keys = ["score", "tiebreak_prev_own"] + (["rural_share"] if share_tiebreak else [])
    d = d.sort_values(keys + ["company"], ascending=[False] * len(keys) + [True])
    d["rank"] = range(1, len(d) + 1)
    return d


out, changes = [], 0
for r in mk.itertuples():
    q, call = r.quarter, r.wf_pred
    d = rank_quarter(q, call, expo["rural_share_of_india_sales"].to_dict())
    eq = rank_quarter(q, call, {c: 1.0 for c in COS}, share_tiebreak=False)
    if d["company"].iloc[0] != eq["company"].iloc[0]:
        changes += 1
    actual_mkt = r.target_label if r.target_label in C.LABELS else ""
    for x in d.itertuples():
        own_now = own(x.company, q)
        why = (f"MGNREGA market call {call} (rule: {r.wf_rule.replace('MGNREGA ', '')}, data through {r.mgnrega_data_through}); "
               f"rural share {x.rural_share:.0%}"
               + (" (assumed)" if expo.loc[x.company, "status"].startswith("ASSUMPTION") else "")
               + (f"; last call own rural: {x.prev_own_label}" if x.prev_own_label else "; no own rural comment last call"))
        out.append({"quarter": q, "prediction_date": r.prediction_date, "rank": x.rank, "company": x.company,
                    "predicted_direction": call, "score": round(x.score, 3), "rationale": why,
                    "period": r.period, "actual_market_wide": actual_mkt, "actual_own_rural": own_now,
                    "own_correct": "" if not own_now else ("Yes" if own_now == call else "No")})
rk = pd.DataFrame(out)
rk.to_csv(C.OUT / "ranked_list.csv", index=False)

# --- scoring ---------------------------------------------------------------
lines = ["RANKED LIST - SCORING (walk-forward market calls; blanks excluded from scoring)", ""]
qtr = rk.drop_duplicates("quarter")
m_ok = qtr[qtr["actual_market_wide"] != ""]
m_c = int((m_ok["predicted_direction"] == m_ok["actual_market_wide"]).sum())
m_n = len(m_ok)
mw = pd.read_csv(C.RAW / "evidence_Market.csv", dtype=str).set_index("quarter")["agreed_label"]
rep = sum(mw.get(prev_q(q), "") == a for q, a in zip(m_ok["quarter"], m_ok["actual_market_wide"]))
lines.append(f"Market-wide call correct in {m_c} of {m_n} scorable quarters "
             f"('same as last quarter' baseline: {rep} of {m_n}).")
o_ok = rk[rk["own_correct"] != ""]
lines.append(f"Company direction vs the company's own rural label: correct in {(o_ok['own_correct'] == 'Yes').sum()} of "
             f"{len(o_ok)} scorable company-quarters ({len(rk)} company-quarters ranked; "
             f"{len(rk) - len(o_ok)} had no own rural comment).")
for c in COS:
    g = o_ok[o_ok["company"] == c]
    lines.append(f"  {c:7s} {(g['own_correct'] == 'Yes').sum()} of {len(g)} scorable")
lines += ["", f"Robustness: with equal exposure weights (rural share dropped entirely), the top-ranked company "
          f"changes in {changes} of {qtr.shape[0]} quarters - the order rests mainly on the rural-share assumption.",
          "Calls by quarter: " + ", ".join(f"{a}={b}" for a, b in zip(qtr["quarter"], qtr["predicted_direction"])),
          "", "Reading this: the market call is Steady in most quarters, so most rankings are decided by the",
          "tie-breaks (last reported own rural momentum, then rural share), not by MGNREGA. The ranking is",
          "therefore an exposure ordering more than a MGNREGA signal - say so when presenting it."]
(C.OUT / "ranking_scores.txt").write_text("\n".join(lines) + "\n")
print("\n".join(lines))
print(f"\nSaved {C.OUT / 'ranked_list.csv'}")
