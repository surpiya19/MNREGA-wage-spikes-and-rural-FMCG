"""Alternative tests of the MGNREGA -> rural FMCG idea.

Adds three things to the main pipeline without changing it:
  A. A numeric target: each company's reported domestic volume growth, and whether it
     speeds up or slows down next quarter (instead of Accelerating/Steady/Slowing labels).
  B. Broader MGNREGA signals from state-level data: regional totals, breadth (share of
     states with persondays up year on year), the median state's growth, and an
     Emami-specific region-weighted signal from its disclosed regional sales split.
  C. Turning-point scoring of the existing label backtest: when a method calls a change,
     how often is it right, and how many real changes does it catch.

Timing: the signal for target quarter t uses MGNREGA data for the calendar quarter
before t. That quarter ends at least 3 months before t's results date, which matches
Thurro's 3-month revision rule used in the main pipeline.

Run from the repo root:  python alternatives/run_alternatives.py
"""
from pathlib import Path
import sys
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import config as C  # noqa: E402  (analysis window: C.FIRST_QUARTER..C.LAST_QUARTER)
ALT = ROOT / "alternatives"
OUT = ALT / "outputs"
OUT.mkdir(exist_ok=True)
RNG = np.random.default_rng(20261110)
N_PERM = 10000
COMPANIES = ["HUL", "Dabur", "Marico", "Emami"]
CAP_SIGNAL_END = pd.Period("2025Q2")   # last signal quarter before the Aug 2025 spending cap

# Emami Annual Report FY19, p.18: domestic region-wise revenue N 33 / E 20 / W 28 / S 19.
# This is the only regional split any of the four companies has disclosed in the corpus.
EMAMI_REGION_W = {"N": 0.33, "E": 0.20, "W": 0.28, "S": 0.19}


def fq_to_period(fq):
    """'Q1 FY24' -> pandas Period 2023Q2 (Apr-Jun 2023)."""
    q, fy = fq.split()
    q, fy = int(q[1]), 2000 + int(fy[2:])
    month = {1: 4, 2: 7, 3: 10, 4: 1}[q]
    year = fy - 1 if q in (1, 2, 3) else fy
    return pd.Period(f"{year}-{month:02d}", freq="Q")


# ---------------------------------------------------------------- signals
def build_signals():
    reg = pd.read_csv(ALT / "data" / "mgnrega_region_quarterly.csv", parse_dates=["q"])
    reg["p"] = reg.q.dt.to_period("Q")
    pd_ = reg[reg.measure == "persondays_lakh"].set_index("p")[["N", "E", "W", "S", "T"]]
    dm = reg[reg.measure == "persons_demanded_lakh"].set_index("p")[["N", "E", "W", "S", "T"]]
    yoy_pd = pd_ / pd_.shift(4) - 1
    yoy_dm = dm / dm.shift(4) - 1
    br = pd.read_csv(ALT / "data" / "mgnrega_state_breadth_quarterly.csv", parse_dates=["q"])
    br["p"] = br.q.dt.to_period("Q")
    br = br.set_index("p")
    s = pd.DataFrame(index=pd_.index)
    s["pd_yoy"] = yoy_pd["T"]
    s["demand_yoy"] = yoy_dm["T"]
    s["work_vs_demand"] = yoy_pd["T"] - yoy_dm["T"]       # more work given per person asking
    s["breadth_share_up"] = br["share_up"]
    s["median_state_yoy"] = br["median_yoy"]
    s["emami_region_yoy"] = sum(yoy_pd[r] * w for r, w in EMAMI_REGION_W.items())
    for r in "NEWS":
        s[f"region_{r}_yoy"] = yoy_pd[r]
    return s


SIGNALS = ["pd_yoy", "demand_yoy", "work_vs_demand", "breadth_share_up", "median_state_yoy", "company_weighted_yoy"]
PRIMARY = "pd_yoy"   # pre-specified: the same persondays signal the main pipeline uses


# ---------------------------------------------------------------- panel
def build_panel(sig):
    rows = []
    for c in COMPANIES:
        ev = pd.read_csv(ROOT / "data" / "raw" / f"evidence_{c}.csv")
        ev["p"] = ev.quarter.map(fq_to_period)
        ev = ev[ev.quarter.map(C.in_window)]   # same window as the main pipeline
        ev = ev.sort_values("p").set_index("p")
        vol = ev.volume_growth_pct.astype(float)
        for p in ev.index:
            prev = p - 1
            if prev not in vol.index or pd.isna(vol.get(p)) or pd.isna(vol.get(prev)):
                continue
            sp, sp2 = p - 1, p - 2           # signal quarter and the one before it
            if sp not in sig.index or sp2 not in sig.index:
                continue
            r = {"company": c, "quarter": ev.loc[p, "quarter"], "p": p, "vol": vol[p],
                 "vol_prev": vol[prev], "d_vol": vol[p] - vol[prev], "signal_quarter": str(sp),
                 "pre_cap": sp <= CAP_SIGNAL_END}
            for k in [x for x in SIGNALS if x != "company_weighted_yoy"] + ["emami_region_yoy"]:
                r[k] = sig.loc[sp, k]
                r[f"d_{k}"] = sig.loc[sp, k] - sig.loc[sp2, k]
            src = "emami_region_yoy" if c == "Emami" else "pd_yoy"
            r["company_weighted_yoy"] = r[src]
            r["d_company_weighted_yoy"] = r[f"d_{src}"]
            rows.append(r)
    return pd.DataFrame(rows)


def spearman(x, y):
    return pd.Series(x).rank().corr(pd.Series(y).rank())


def perm_test(df, xcol, ycol):
    """Spearman of x with company-demeaned y; p-value by shuffling x within company."""
    d = df[[xcol, ycol, "company"]].dropna().copy()
    d["y"] = d[ycol] - d.groupby("company")[ycol].transform("mean")
    obs = spearman(d[xcol].values, d.y.values)
    groups = [g.index.values for _, g in d.groupby("company")]
    x = d[xcol].values.copy()
    pos = {ix: i for i, ix in enumerate(d.index)}
    hits = 0
    for _ in range(N_PERM):
        xs = x.copy()
        for g in groups:
            ii = [pos[i] for i in g]
            xs[ii] = RNG.permutation(xs[ii])
        if abs(spearman(xs, d.y.values)) >= abs(obs):
            hits += 1
    return obs, (hits + 1) / (N_PERM + 1), len(d)


def walk_forward(df, feat, min_train=12):
    """Pooled expanding-window OLS of d_vol on one feature + company mean-reversion term.
    Compared with two baselines: no change (repeat last volume) and mean reversion only."""
    d = df.dropna(subset=[feat, "d_vol"]).sort_values(["p", "company"]).reset_index(drop=True)
    out = []
    for p in sorted(d.p.unique()):
        train, test = d[d.p < p], d[d.p == p]
        if len(train) < min_train:
            continue
        cm = train.groupby("company").vol.mean()
        def gap(frame):
            return frame.vol_prev - frame.company.map(cm).fillna(train.vol.mean())
        Xr = np.c_[np.ones(len(train)), gap(train)]
        br = np.linalg.lstsq(Xr, train.d_vol, rcond=None)[0]
        Xf = np.c_[np.ones(len(train)), gap(train), train[feat]]
        bf = np.linalg.lstsq(Xf, train.d_vol, rcond=None)[0]
        for _, t in test.iterrows():
            g = t.vol_prev - cm.get(t.company, train.vol.mean())
            out.append({"quarter": t.quarter, "company": t.company, "pre_cap": t.pre_cap,
                        "actual_d_vol": t.d_vol,
                        "pred_mgnrega": bf[0] + bf[1] * g + bf[2] * t[feat],
                        "pred_meanrev": br[0] + br[1] * g, "pred_nochange": 0.0,
                        "mgnrega_coef": bf[2]})
    return pd.DataFrame(out)


def score(wf, subset_name, mask):
    w = wf[mask]
    moved = w[w.actual_d_vol != 0]
    res = {"subset": subset_name, "n": len(w)}
    for m in ["mgnrega", "meanrev", "nochange"]:
        res[f"mae_{m}"] = round((w[f"pred_{m}"] - w.actual_d_vol).abs().mean(), 2)
        if m != "nochange":
            res[f"dir_hits_{m}"] = f"{int((np.sign(moved[f'pred_{m}']) == np.sign(moved.actual_d_vol)).sum())}/{len(moved)}"
    return res


# ---------------------------------------------------------------- turning points
def turning_points():
    tp = pd.read_csv(ROOT / "outputs" / "quality" / "turning_points.csv")
    tp = tp[(tp.scenario == "corrected") & (tp.evaluation == "walk_forward")]
    rows = []
    for (c, t), g in tp.groupby(["company", "target"]):
        rows.append(_tp_row(f"{c} ({t})", g))
    rows.append(_tp_row("ALL company-targets", tp))
    rows.append(_tp_row("Market-wide only", tp[tp.company == "Market"]))
    return pd.DataFrame(rows)


def _tp_row(name, g):
    called = g[g.model_called_change.astype(bool)]
    actual = g[g.actual_changed.astype(bool)]
    caught = actual[actual.model_correct.astype(bool)]
    right_calls = called[called.model_correct.astype(bool)]
    return {"set": name, "quarters": len(g), "actual_changes": len(actual),
            "model_change_calls": len(called), "change_calls_right": len(right_calls),
            "precision": round(len(right_calls) / len(called), 2) if len(called) else np.nan,
            "changes_caught": len(caught),
            "recall": round(len(caught) / len(actual), 2) if len(actual) else np.nan,
            "repeat_last_changes_caught": 0}


# ---------------------------------------------------------------- main
def main():
    sig = build_signals()
    sig.to_csv(OUT / "signals_quarterly.csv")
    panel = build_panel(sig)
    panel.to_csv(OUT / "volume_panel.csv", index=False)

    lines = ["ALTERNATIVE TESTS - generated by alternatives/run_alternatives.py", f"Window: {C.FIRST_QUARTER} to {C.LAST_QUARTER} (same as the main pipeline).", ""]
    lines.append(f"Volume panel: {len(panel)} company-quarters with this and last quarter's volume growth "
                 f"({', '.join(f'{c} {n}' for c, n in panel.company.value_counts().reindex(COMPANIES).items())}).")
    lines.append(f"Pre-cap (signal quarter <= {CAP_SIGNAL_END}): {int(panel.pre_cap.sum())}; after: {int((~panel.pre_cap).sum())}.")
    lines.append(f"Volume growth sped up in {int((panel.d_vol > 0).sum())}, slowed in {int((panel.d_vol < 0).sum())}, "
                 f"unchanged in {int((panel.d_vol == 0).sum())} - far more movement than the labels "
                 f"(the market-wide label is Steady in most quarters).")
    lines.append("")

    # A/B. association tests
    lines.append("A. DOES THE MGNREGA SIGNAL LINE UP WITH CHANGES IN VOLUME GROWTH?")
    lines.append("Spearman correlation of last quarter's signal with the change in volume growth (company-demeaned);")
    lines.append(f"p-value from {N_PERM:,} within-company shuffles. Primary (pre-specified) test is marked *; the rest are exploratory,")
    lines.append("so with 12 tests one 'p<0.05' would be expected by chance.")
    assoc = []
    for subset, mask in [("all", panel.index == panel.index), ("pre_cap", panel.pre_cap)]:
        for s in SIGNALS:
            for form in ["level", "change"]:
                col = s if form == "level" else f"d_{s}"
                rho, pval, n = perm_test(panel[mask], col, "d_vol")
                assoc.append({"subset": subset, "signal": s, "form": form, "rho": round(rho, 3),
                              "p": round(pval, 4), "n": n, "primary": s == PRIMARY and form == "change"})
    assoc = pd.DataFrame(assoc)
    assoc.to_csv(OUT / "association_tests.csv", index=False)
    for subset in ["all", "pre_cap"]:
        lines.append(f"  [{subset}]")
        for _, r in assoc[assoc.subset == subset].iterrows():
            star = "*" if r.primary else " "
            lines.append(f"   {star} {r.signal:<22} {r.form:<6} rho={r.rho:+.2f}  p={r.p:.3f}  n={r.n}")
    n_sig = int(((assoc.p < 0.05)).sum())
    lines.append(f"  Tests with p<0.05: {n_sig} of {len(assoc)}.")
    lines.append("")

    # forecasting
    lines.append("B. WALK-FORWARD FORECAST OF THE CHANGE IN VOLUME GROWTH (pooled, refit every quarter)")
    lines.append("Model = mean reversion to each company's average + one MGNREGA feature. Baselines: mean reversion only; no change.")
    fc_rows = []
    for feat in ["d_pd_yoy", "pd_yoy", "d_company_weighted_yoy", "d_breadth_share_up"]:
        wf = walk_forward(panel, feat)
        wf.to_csv(OUT / f"walk_forward_{feat}.csv", index=False)
        for name, m in [("all", wf.index == wf.index), ("pre_cap", wf.pre_cap)]:
            r = score(wf, name, m); r["feature"] = feat
            r["coef_sign_last"] = "+" if wf.mgnrega_coef.iloc[-1] > 0 else "-"
            r["coef_sign_flips"] = int((np.sign(wf.mgnrega_coef).diff().fillna(0) != 0).sum())
            fc_rows.append(r)
    fc = pd.DataFrame(fc_rows)[["feature", "subset", "n", "mae_mgnrega", "mae_meanrev", "mae_nochange",
                                "dir_hits_mgnrega", "dir_hits_meanrev", "coef_sign_last", "coef_sign_flips"]]
    fc.to_csv(OUT / "walk_forward_scores.csv", index=False)
    lines.append(fc.to_string(index=False))
    lines.append("MAE = mean absolute error in percentage points of volume growth (lower is better).")
    lines.append("dir_hits = quarters where the predicted direction of change matched (unchanged quarters left out).")
    lines.append("")

    # C turning points
    lines.append("C. TURNING-POINT SCORING OF THE EXISTING LABEL BACKTEST (corrected scenario, walk-forward)")
    tp = turning_points()
    tp.to_csv(OUT / "turning_point_scores.csv", index=False)
    lines.append(tp.to_string(index=False))
    lines.append("precision = share of the model's change calls that were right; recall = share of real changes it caught.")
    lines.append("'Repeat last quarter' never calls a change, so it catches 0 turning points by construction.")
    lines.append("")

    (OUT / "RESULTS.txt").write_text("\n".join(lines))
    print("\n".join(lines))


if __name__ == "__main__":
    main()
