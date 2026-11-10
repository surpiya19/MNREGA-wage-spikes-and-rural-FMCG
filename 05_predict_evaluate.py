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
    "MGNREGA work demanded": ["dm_yoy_chg"],
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
SELECTABLE = ["MGNREGA persondays", "MGNREGA wage bill", "MGNREGA work demanded"]

models = {}
for name, cols in SIGNALS.items():
    m = fit(train, cols)
    if m:
        models[name] = (cols, m)

lines = [f"Company: {C.COMPANY}   |   Target: {C.TARGET_NAME} ({C.TARGET})",
         f"Coverage: {len(eligible)} of {len(f)} quarters have a usable label. Blank (Insufficient) quarters are "
         "left out of scoring, not counted as misses (Thurro guidance).",
         f"Eligible quarters (labelled, not Insufficient): {len(eligible)}  ->  train {len(train)}, test {len(test)}",
         f"Train: {', '.join(train['quarter'])}", f"Test : {', '.join(test['quarter'])}", "",
         "Candidate rules (fitted on train only; the selected rule is picked among the MGNREGA rules):"]
for name, (cols, m) in models.items():
    direction = "higher signal -> Accelerating" if m["sign"] == 1 else "higher signal -> SLOWING (distress reading)"
    lines.append(f"  {name:22s} train accuracy {m['train_acc']:.0%} on {m['n_train']} qtrs; {direction}; "
                 f"cut-offs (z-score) {m['lower']:.2f} / {m['upper']:.2f}")

import json
summary = {"tag": C.TAG, "company": C.COMPANY, "target": C.TARGET, "usable": len(eligible), "quarters": len(f),
           "n_train": len(train), "n_test": len(test)}

if not models or len(train) < C.MIN_TRAIN_QUARTERS or len(test) < 2:
    lines += ["", f"Finding: {C.COMPANY}'s {C.TARGET_NAME} target can't be tested - only {len(eligible)} of {len(f)} "
              f"quarters have a usable label, too few to fit a rule (needs at least {C.MIN_TRAIN_QUARTERS} training "
              "and 2 test quarters; with fewer, every rule fits the training quarters and the test says nothing)."
              + (" In most quarters the company did not describe this trend (blank = Insufficient)."
                 if len(eligible) < len(f) / 2 else "")]
    summary["status"] = "not testable"
    (C.OUT / f"run_summary_{C.TAG}.json").write_text(json.dumps(summary))
    for stale in [C.OUT / f"predictions_{C.TAG}.csv"]:
        if stale.exists():
            stale.rename(stale.with_name(stale.stem + "_STALE_not_testable.csv"))
    (C.OUT / f"results_{C.TAG}.txt").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    import sys
    sys.exit(0)
if not any(k in models for k in SELECTABLE):
    raise SystemExit("Not enough training quarters with MGNREGA data to fit a rule.")
best_name = max([k for k in SELECTABLE if k in models], key=lambda k: models[k][1]["train_acc"])
cols, m = models[best_name]
sel_dir = "higher MGNREGA -> Accelerating (income reading)" if m["sign"] == 1 else "higher MGNREGA -> Slowing (distress reading)"
lines.append(f"\nSelected on train: {best_name} ({sel_dir})")

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
if len(t) == 0:
    lines.append(f"Finding: {C.COMPANY}'s {C.TARGET_NAME} target can't be tested - only {len(eligible)} of {len(f)} quarters "
                 f"have a usable label, and all {len(train)} were needed for training, leaving no test quarters.")
elif sel_n == 0:
    lines.append(f"Finding: none of the {len(t)} test quarters had a prediction from every main method, so the rule "
                 "can't be compared with the baselines on equal terms.")
elif sel_c > base[best_base]:
    lines.append(f"The selected rule beat the best baseline ({best_base.replace('pred_', '')}) by {sel_c - base[best_base]} of {sel_n} quarters.")
else:
    lines.append(f"Finding: the selected rule did not beat the best baseline ({best_base.replace('pred_', '')}: {base[best_base]} vs {sel_c} of {sel_n}).")
if sel_n > 0:
    lines.append("With this few quarters, one quarter can change the conclusion, so results are given as counts as well as percentages.")
    gap = m["train_acc"] - sel_c / sel_n
    if gap >= 0.3:
        lines.append(f"Overfit warning: the selected rule scored {m['train_acc']:.0%} on train but {sel_c / sel_n:.0%} on test "
                     f"({gap:.0%} points lower) - the training fit does not carry over.")
    for name, (c_, m_) in models.items():
        c1, n1 = score(f"pred_{name}", t)
        if n1 and m_["train_acc"] - c1 / n1 >= 0.4 and name != best_name:
            lines.append(f"Overfit warning: {name} {m_['train_acc']:.0%} on train vs {c1}/{n1} on test.")
summary.update(status="tested", selected=best_name, direction="income" if m["sign"] == 1 else "distress",
               train_acc=round(m["train_acc"], 3), test_correct=sel_c, test_n=sel_n,
               best_baseline=best_base.replace("pred_", ""), best_baseline_correct=base[best_base])
shock = t[t["pd_yoy"] < -0.25]
if len(shock):
    lines.append(f"Note: in {len(shock)} of {len(t)} test quarters MGNREGA persondays were down more than 25% year on year "
                 f"({', '.join(shock['quarter'])}). From Aug 2025 the fall looks like a scheme/policy change rather than rural "
                 "demand, so the signal may be measuring policy in these quarters.")

# --- Walk-forward test (Thurro/teammate suggestion) ---------------------------
# Refit on every earlier labelled quarter and predict the next one, so every
# quarter after the first few gets a true out-of-sample prediction. Scored
# separately before and after the 2025 spending cap (see config.py).
def choose(train_df):
    fitted = {k: fit(train_df, SIGNALS[k]) for k in SELECTABLE}
    fitted = {k: v for k, v in fitted.items() if v}
    if not fitted:
        return None, None
    k = max(fitted, key=lambda n: fitted[n]["train_acc"])
    return k, fitted[k]

f["wf_rule"] = ""
f["wf_pred"] = np.nan
f["wf_pred"] = f["wf_pred"].astype(object)
f["wf_most_common"] = np.nan
f["wf_most_common"] = f["wf_most_common"].astype(object)
elig_idx = list(eligible.index)
for j in range(C.WALK_FORWARD_MIN_TRAIN, len(elig_idx)):
    i = elig_idx[j]
    past = eligible.loc[elig_idx[:j]]
    k, m_ = choose(past)
    if k is None:
        continue
    f.at[i, "wf_rule"] = k
    f.at[i, "wf_pred"] = predict(f.loc[[i]], SIGNALS[k], m_).iloc[0]
    f.at[i, "wf_most_common"] = past["agreed_label"].mode().iloc[0]

wf = f[f["wf_rule"] != ""]
lines += ["", f"WALK-FORWARD TEST (refit before every quarter; first {C.WALK_FORWARD_MIN_TRAIN} labelled quarters used only for training):"]
if wf.empty:
    lines.append("  Not enough labelled quarters for a walk-forward test.")
else:
    lines.append(f"  {'period':32s} {'MGNREGA rule':>14s} {'repeat last':>12s} {'most common':>12s}")
    groups = [("all", wf)] + [(p, g) for p, g in wf.groupby("period", sort=False)]
    for pname, g in groups:
        g2 = g.dropna(subset=["wf_pred", "pred_repeat_last"])
        n = len(g2)
        if n == 0:
            continue
        a = int((g2["wf_pred"] == g2["agreed_label"]).sum())
        b = int((g2["pred_repeat_last"] == g2["agreed_label"]).sum())
        c = int((g2["wf_most_common"] == g2["agreed_label"]).sum())
        lines.append(f"  {pname:32s} {a:>6d} of {n:<5d} {b:>4d} of {n:<5d} {c:>4d} of {n:<5d}")
    lines.append("  Rule picked at each step: " + ", ".join(f"{r.quarter}={r.wf_rule.replace('MGNREGA ', '')}" for r in wf.itertuples()))
    pre = wf[wf["period"] == "before spending cap"].dropna(subset=["wf_pred", "pred_repeat_last"])
    if len(pre):
        a = int((pre["wf_pred"] == pre["agreed_label"]).sum()); b = int((pre["pred_repeat_last"] == pre["agreed_label"]).sum())
        c = int((pre["wf_most_common"] == pre["agreed_label"]).sum())
        best_b, best_name_b = max((b, "same as last quarter"), (c, "most common label"))
        verdict = "beat" if a > best_b else "tied with" if a == best_b else "did not beat"
        lines.append(f"  Before the spending cap, the MGNREGA rule {verdict} the best baseline, {best_name_b} "
                     f"({a} vs {best_b} of {len(pre)}; same as last quarter {b}, most common {c}).")
    g2 = wf.dropna(subset=["wf_pred", "pred_repeat_last"])
    summary.update(wf_n=len(g2), wf_rule=int((g2["wf_pred"] == g2["agreed_label"]).sum()),
                   wf_repeat=int((g2["pred_repeat_last"] == g2["agreed_label"]).sum()),
                   wf_most_common=int((g2["wf_most_common"] == g2["agreed_label"]).sum()))

out_cols = ["company", "quarter", "split", "prediction_date", "mgnrega_data_through", "rain_data_through",
            "pd_yoy", "pd_yoy_chg", "dm_yoy", "dm_yoy_chg", "rain_dep", "rain_dep_chg", "pred_selected", "agreed_label",
            "own_label", "market_rural_label", "period", "wf_rule", "wf_pred", "wf_most_common"] + MAIN[1:] + ["pred_most_common"] + [f"pred_{k}" for k in models]
pred = f[list(dict.fromkeys(out_cols))].copy()
pred["selected_correct"] = np.where(pred["pred_selected"].isna() | ~pred["agreed_label"].isin(C.LABELS), "",
                                    np.where(pred["pred_selected"] == pred["agreed_label"], "Yes", "No"))
pred = pred.rename(columns={"agreed_label": "target_label"})
pred["target"] = C.TARGET
pred.to_csv(C.OUT / f"predictions_{C.TAG}.csv", index=False)
(C.OUT / f"results_{C.TAG}.txt").write_text("\n".join(lines) + "\n")
(C.OUT / f"run_summary_{C.TAG}.json").write_text(json.dumps(summary))
print("\n".join(lines))
print(f"\nSaved {C.OUT / f'predictions_{C.TAG}.csv'}")
