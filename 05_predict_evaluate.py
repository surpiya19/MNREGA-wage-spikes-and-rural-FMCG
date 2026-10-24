"""Steps 6b + 7: a simple, explainable prediction rule, tested against baselines.

The rule (one signal x, two cut-offs):
    x > upper  -> Accelerating
    x < lower  -> Slowing
    otherwise  -> Steady
The direction is NOT assumed: we also try the flipped signal (-x), because more
MGNREGA work can mean rural distress rather than extra income. Signals tried:
MGNREGA only, wage bill only, rainfall only, and MGNREGA + rainfall combined.

Everything is chosen on the EARLIER quarters (train) and scored on the LATER
quarters (test). Baselines, scored on exactly the same test quarters:
  repeat_last    - predict last quarter's agreed label again
  follow_market  - predict the market-rural label from the previous quarter's call
                   (the latest market read available before the prediction date)
  most_common    - the most common label in the training quarters

Outputs: outputs/predictions_<COMPANY>.csv, outputs/results_<COMPANY>.txt
"""
import itertools

import numpy as np
import pandas as pd

import config as C

f = pd.read_csv(C.CLEAN / f"features_{C.COMPANY}.csv", parse_dates=["prediction_date"]).fillna({"agreed_label": "", "market_rural_label": ""})
f = f.sort_values("prediction_date").reset_index(drop=True)
# The rest of this script predicts the column "agreed_label". For the market
# test, put the market label there (the own label is kept for reference).
f["own_label"] = f["agreed_label"]
if C.TARGET == "market":
    f["agreed_label"] = f["market_rural_label"]
OWN = C.TARGET == "own"

# --- Baselines need the previous quarter, so compute before filtering -------
prev_known = f["agreed_label"].where(f["agreed_label"].isin(C.LABELS)).ffill().shift(1)
f["pred_repeat_last"] = prev_known
prev_mkt = f["market_rural_label"].shift(1)
f["pred_follow_market"] = prev_mkt.where(prev_mkt.isin(C.LABELS))
# For the market test, "follow the market" is the same as "repeat last", so drop it.
MAIN = ["pred_selected", "pred_repeat_last"] + (["pred_follow_market"] if OWN else [])
BASES = ["pred_repeat_last", "pred_most_common"] + (["pred_follow_market"] if OWN else [])

SIGNALS = {
    "MGNREGA persondays": ["pd_yoy_chg"],
    "MGNREGA wage bill": ["wb_yoy_chg"],
    "Rainfall": ["rain_dep"],
    "MGNREGA + rainfall": ["pd_yoy_chg", "rain_dep"],
}

eligible = f[f["agreed_label"].isin(C.LABELS)].copy()
n_train = max(int(round(len(eligible) * C.TRAIN_FRACTION)), 3)
train, test = eligible.iloc[:n_train], eligible.iloc[n_train:]
if len(test) < 2:
    print(f"WARNING: only {len(test)} test quarters. Results will be anecdotal - add quarters or companies.")


def signal(df, cols, stats):
    """Average of z-scores (using TRAIN mean/std only, so no peeking at test)."""
    z = [(df[c] - stats[c][0]) / stats[c][1] for c in cols]
    return sum(z) / len(z)


def apply_rule(x, lower, upper):
    out = np.where(x > upper, "Accelerating", np.where(x < lower, "Slowing", "Steady"))
    return pd.Series(out, index=x.index).where(x.notna())


def fit(train_df, cols):
    d = train_df.dropna(subset=cols)
    if len(d) < 3:
        return None
    stats = {c: (d[c].mean(), d[c].std(ddof=0) or 1.0) for c in cols}
    best = None
    for sign in (1, -1):
        x = sign * signal(d, cols, stats)
        cuts = np.unique(np.concatenate([[-np.inf, np.inf], np.quantile(x, np.linspace(0, 1, 11))]))
        for lo, hi in itertools.product(cuts, cuts):
            if lo > hi:
                continue
            acc = (apply_rule(x, lo, hi) == d["agreed_label"]).mean()
            # Ties: prefer the rule that calls more quarters "Steady" (the more
            # cautious rule). Measured as the share of training quarters inside
            # the Steady band, so an empty band (e.g. -inf/-inf = "always
            # Accelerating") no longer wins ties.
            steady_share = ((x >= lo) & (x <= hi)).mean()
            key = (acc, steady_share)
            if best is None or key > best[0]:
                best = (key, dict(sign=sign, lower=lo, upper=hi, stats=stats, train_acc=acc, n_train=len(d)))
    return best[1]


def predict(df, cols, m):
    x = m["sign"] * signal(df, cols, m["stats"])
    return apply_rule(x, m["lower"], m["upper"])


# The project question is about MGNREGA, so the "selected" rule is chosen among
# the MGNREGA rules only (they share the same training quarters, so the choice is
# fair). Rainfall rules are fitted on the quarters where rainfall exists (the data
# starts Sep 2022, and the first full monsoon is 2023) and shown for comparison.
SELECTABLE = ["MGNREGA persondays", "MGNREGA wage bill"]

models = {}
for name, cols in SIGNALS.items():
    m = fit(train, cols)
    if m:
        models[name] = (cols, m)

lines = [f"Company: {C.COMPANY}   |   Target: {C.TARGET_NAME} ({C.TARGET})",
         f"Eligible quarters (labelled, not Insufficient): {len(eligible)}  ->  train {len(train)}, test {len(test)}",
         f"Train: {', '.join(train['quarter'])}", f"Test : {', '.join(test['quarter'])}", "",
         "Candidate rules (fitted on train only; the selected rule is picked among the MGNREGA rules):"]
for name, (cols, m) in models.items():
    direction = "higher signal -> Accelerating" if m["sign"] == 1 else "higher signal -> SLOWING (distress reading)"
    lines.append(f"  {name:22s} train accuracy {m['train_acc']:.0%} on {m['n_train']} qtrs; {direction}; "
                 f"cut-offs (z-score) {m['lower']:.2f} / {m['upper']:.2f}")

if not models:
    raise SystemExit("Not enough training quarters with data to fit any rule.")
if not any(k in models for k in SELECTABLE):
    raise SystemExit("Not enough training quarters with MGNREGA data to fit a rule.")
best_name = max([k for k in SELECTABLE if k in models], key=lambda k: models[k][1]["train_acc"])
cols, m = models[best_name]
lines.append(f"\nSelected on train: {best_name}")

for name, (c_, m_) in models.items():
    f[f"pred_{name}"] = predict(f, c_, m_)
f["pred_selected"] = f[f"pred_{best_name}"]
f["most_common"] = train["agreed_label"].mode().iloc[0]
f["pred_most_common"] = f["most_common"]
f["split"] = np.where(f.index.isin(train.index), "train", np.where(f.index.isin(test.index), "test", "not eligible"))

# --- Score everything on the same test quarters ------------------------------
def score(col, rows):
    p = rows[col]
    ok = p.notna()
    return int((p[ok] == rows.loc[ok, "agreed_label"]).sum()), int(ok.sum())

t = f[f["split"] == "test"]
# Fair comparison: only quarters where EVERY method could make a prediction.
methods = MAIN + ["pred_most_common"] + [f"pred_{k}" for k in models]
common = t.dropna(subset=MAIN)
lines += ["", f"TEST RESULTS ({len(t)} test quarters; {len(common)} where all main methods could predict):"]
for col in dict.fromkeys(methods):
    c_all, n_all = score(col, t)
    c_com, n_com = score(col, common)
    lines.append(f"  {col.replace('pred_', ''):22s} {c_all}/{n_all} correct overall   |   {c_com}/{n_com} on common quarters")

sel_c, sel_n = score("pred_selected", common)
base = {k: score(k, common)[0] for k in BASES}
best_base = max(base, key=base.get)
lines.append("")
if sel_n == 0:
    lines.append("No common test quarters - cannot compare. Extend the history or add companies.")
elif sel_c > base[best_base]:
    lines.append(f"The selected rule beat the best baseline ({best_base.replace('pred_', '')}) by {sel_c - base[best_base]} of {sel_n} quarters.")
else:
    lines.append(f"The selected rule did NOT beat the best baseline ({best_base.replace('pred_', '')}: {base[best_base]} vs {sel_c} of {sel_n}). "
                 "Report this honestly and explain what limited it.")
lines.append("Caution: with this few quarters, one quarter changes the conclusion. Present counts, not just percentages.")
shock = t[t["pd_yoy"] < -0.25]
if len(shock):
    lines.append(f"Note: in {len(shock)} of {len(t)} test quarters MGNREGA persondays were down more than 25% year on year "
                 f"({', '.join(shock['quarter'])}). From Aug 2025 the fall looks like a scheme/policy change rather than rural "
                 "demand, so the signal may be measuring policy in these quarters.")

out_cols = ["company", "quarter", "split", "prediction_date", "mgnrega_data_through", "rain_data_through",
            "pd_yoy", "pd_yoy_chg", "rain_dep", "rain_dep_chg", "pred_selected", "agreed_label",
            "own_label", "market_rural_label"] + MAIN[1:] + ["pred_most_common"] + [f"pred_{k}" for k in models]
pred = f[list(dict.fromkeys(out_cols))].copy()
pred["selected_correct"] = np.where(pred["pred_selected"].isna() | ~pred["agreed_label"].isin(C.LABELS), "",
                                    np.where(pred["pred_selected"] == pred["agreed_label"], "Yes", "No"))
pred = pred.rename(columns={"agreed_label": "target_label"})
pred["target"] = C.TARGET
pred.to_csv(C.OUT / f"predictions_{C.TAG}.csv", index=False)
(C.OUT / f"results_{C.TAG}.txt").write_text("\n".join(lines) + "\n")
print("\n".join(lines))
print(f"\nSaved {C.OUT / f'predictions_{C.TAG}.csv'}")
