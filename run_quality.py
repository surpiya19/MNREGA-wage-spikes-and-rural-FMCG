"""Reproduce corrected results and conservative timing checks without changing legacy outputs.

Run: python run_quality.py
Outputs: outputs/quality/REPORT.md, metrics.csv, per_class.csv, confusion.csv,
         turning_points.csv, timing_checks.csv, label_sensitivity.csv,
         review_queue.csv, volume_review.csv and runs/<scenario>/.
These are exploratory checks on the SAME small history, not a new holdout.
"""
import json
import hashlib
import os
from pathlib import Path
import platform
import subprocess
import sys

import numpy as np
import pandas as pd

import config as C
from quality_core import LABELS, classification_metrics, market_consensus

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "outputs" / "quality"
COMPANIES = ["HUL", "Dabur", "Marico", "Emami"]
SCENARIOS = [("corrected", "day_before_results", 3),
             ("early_deadline", "early_next_quarter", 3),
             ("early_lag4", "early_next_quarter", 4)]


def run(script, env):
    result = subprocess.run([sys.executable, str(ROOT / script)], cwd=ROOT, env=env,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    if result.returncode:
        raise RuntimeError(f"{script} failed:\n{result.stdout}")


def frame(rows, name):
    pd.DataFrame(rows).to_csv(OUT / name, index=False)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    # Explicit settings prevent inherited CLI configuration contaminating this run.
    for key in ("RURAL_DEMO", "RURAL_COMPANY", "RURAL_TARGET", "RURAL_CLEAN_DIR", "RURAL_OUTPUT_DIR"):
        env.pop(key, None)
    run("build_label_inputs.py", env)
    metrics, per_class, confusion, turns, timing = [], [], [], [], []
    for scenario, rule, lag in SCENARIOS:
        print(f"Running {scenario}: {rule}, MGNREGA lag {lag} months", flush=True)
        output = OUT / "runs" / scenario
        clean = ROOT / "data" / "clean_quality" / scenario
        active = dict(env, RURAL_PREDICTION_RULE=rule, RURAL_MGNREGA_LAG=str(lag),
                      RURAL_OUTPUT_DIR=str(output), RURAL_CLEAN_DIR=str(clean))
        for script in ("01_clean_mgnrega.py", "02_clean_rainfall.py"):
            run(script, active)
        targets = [("Market", "market")] + [(c, t) for c in COMPANIES for t in ("own", "market")]
        for company, target in targets:
            tag = company if target == "own" else company + "_market"
            # A later evidence review can make a previously testable target sparse.
            # Do not accidentally score its predictions from an earlier run.
            (output / f"predictions_{tag}.csv").unlink(missing_ok=True)
            settings = dict(active, RURAL_COMPANY=company, RURAL_TARGET=target)
            for script in ("03_labels.py", "04_features.py", "05_predict_evaluate.py"):
                run(script, settings)
            features = pd.read_csv(clean / f"features_{company}.csv")
            evidence = pd.read_csv(ROOT / "data/raw" / f"evidence_{company}.csv")
            for feature in features.itertuples():
                prediction = pd.Timestamp(feature.prediction_date)
                last = pd.Timestamp(feature.mgnrega_data_through)
                release = last + pd.DateOffset(months=lag)
                results_date = pd.Timestamp(evidence.set_index("quarter").loc[feature.quarter, "results_date"])
                before_results = prediction < results_date
                age_ok = release <= prediction
                early_ok = prediction <= pd.Timestamp(feature.quarter_end) + pd.Timedelta(days=7)
                timing.append(dict(scenario=scenario, company=company, target=target, quarter=feature.quarter,
                                   prediction_date=prediction.date(), results_date=results_date.date(),
                                   mgnrega_data_through=last.date(), lag_months=lag,
                                   before_results=before_results, lag_respected=age_ok, early_deadline_met=early_ok))
                if not before_results or not age_ok or (rule == "early_next_quarter" and not early_ok):
                    raise AssertionError(f"Timing failed: {scenario} {tag} {feature.quarter}")
            path = output / f"predictions_{tag}.csv"
            if not path.exists():
                continue  # HUL and Marico own labels are too sparse to fit.
            predictions = pd.read_csv(path).fillna("")
            for evaluation, subset, model_col, common_col in [
                    ("held_out", predictions[predictions["split"] == "test"], "pred_selected", "pred_most_common"),
                    ("walk_forward", predictions[predictions["wf_rule"] != ""], "wf_pred", "wf_most_common")]:
                common = subset[subset["target_label"].isin(LABELS)
                                & subset[model_col].isin(LABELS) & subset["pred_repeat_last"].isin(LABELS)].copy()
                methods = {"MGNREGA": model_col, "Repeat last": "pred_repeat_last", "Most common": common_col}
                common["always_steady"] = "Steady"
                methods["Always steady"] = "always_steady"
                for method, col in methods.items():
                    result = classification_metrics(common["target_label"], common[col])
                    row = dict(scenario=scenario, company=company, target=target, evaluation=evaluation, method=method)
                    metrics.append(dict(row, **{k: v for k, v in result.items() if k != "details"}))
                    per_class.extend(dict(row, **detail) for detail in result["details"])
                    for actual in LABELS:
                        for predicted in LABELS:
                            confusion.append(dict(row, actual=actual, predicted=predicted,
                                count=int(((common["target_label"] == actual) & (common[col] == predicted)).sum())))
                for r in common.itertuples():
                    actual = r.target_label
                    model = getattr(r, model_col)
                    baseline = r.pred_repeat_last
                    turns.append(dict(scenario=scenario, company=company, target=target, evaluation=evaluation,
                                      quarter=r.quarter, actual=actual, prediction=model, baseline=baseline,
                                      actual_changed=actual != baseline, model_called_change=model != baseline,
                                      model_correct=model == actual, baseline_correct=baseline == actual))
        run("07_rank.py", active)
    frame(metrics, "metrics.csv")
    frame(per_class, "per_class.csv")
    frame(confusion, "confusion.csv")
    frame(turns, "turning_points.csv")
    paired = []
    turn_frame = pd.DataFrame(turns)
    for keys, group in turn_frame.groupby(["scenario", "company", "target", "evaluation"]):
        delta = group.model_correct.astype(int) - group.baseline_correct.astype(int)
        remaining = [int(delta.sum() - d) for d in delta]
        paired.append(dict(zip(["scenario", "company", "target", "evaluation"], keys),
                           n=len(group), model_only_correct=int((delta > 0).sum()),
                           baseline_only_correct=int((delta < 0).sum()), same_correctness=int((delta == 0).sum()),
                           net_extra_correct=int(delta.sum()),
                           leave_one_score_out_net_min=min(remaining) if remaining else None,
                           leave_one_score_out_net_max=max(remaining) if remaining else None,
                           note="Fixed predictions; score sensitivity, not model refitting or independent validation"))
    frame(paired, "paired_comparison.csv")
    frame(timing, "timing_checks.csv")
    build_review_and_sensitivity()
    write_report(pd.DataFrame(metrics), pd.DataFrame(turns), pd.DataFrame(timing))
    make_figure(pd.DataFrame(metrics), pd.DataFrame(confusion))
    # Normalise machine-specific paths in generated notes for portable snapshots.
    for path in (OUT / "runs").rglob("*.txt"):
        path.write_text(path.read_text(encoding="utf-8").replace(str(ROOT), "."), encoding="utf-8")
    manifest = []
    for directory in (ROOT / "data/raw", ROOT / "labels"):
        for path in sorted(directory.rglob("*.csv")):
            manifest.append(dict(path=str(path.relative_to(ROOT)), sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
    frame(manifest, "input_manifest.csv")
    print("Done: outputs/quality/REPORT.md", flush=True)


def build_review_and_sensitivity():
    queue, volumes = [], []
    for company in COMPANIES:
        evidence = pd.read_csv(ROOT / "data/raw" / f"evidence_{company}.csv").fillna("")
        final = pd.read_csv(ROOT / "labels" / company.lower() / "labels_final.csv").fillna("").set_index("quarter")
        for r in evidence.itertuples():
            reasons = []
            if r.agreed_label in ("Accelerating", "Slowing"):
                reasons.append("own directional change")
            if r.reader1_label != r.reader2_label:
                reasons.append("reader disagreement")
            if company in ("Marico", "Emami") and r.market_rural_label in LABELS:
                reasons.append("draft market label")
            queue.append(dict(company=company, quarter=r.quarter, priority="HIGH" if reasons else "NORMAL",
                              reasons="; ".join(reasons) or "confirm steady/blank and date", own_label=r.agreed_label,
                              market_label=r.market_rural_label, results_date=r.results_date,
                              own_source=r.own_rural_source, market_source=r.market_rural_source,
                              review_status="PENDING", human_reviewer="", verified_date="", decision="", notes=""))
            note = final.loc[r.quarter, "reconciliation_note"] if r.quarter in final.index else "First-pass evidence"
            volumes.append(dict(company=company, quarter=r.quarter, current_volume_growth_pct=r.volume_growth_pct,
                                source=r.own_rural_source, existing_notes=note,
                                required_basis="organic / like-for-like domestic; mark inclusive exception",
                                verified_basis="", verified_volume_growth_pct="", reviewer="", status="PENDING"))
    frame(queue, "review_queue.csv")
    frame(volumes, "volume_review.csv")
    votes = pd.read_csv(ROOT / "labels/market_wide/market_labels_by_company.csv").fillna("")
    rows = []
    for quarter, group in votes.groupby("quarter", sort=False):
        base, confidence = market_consensus(group["market_label"], tie=C.MARKET_TIE_RULE)
        for drop in COMPANIES:
            label, _ = market_consensus(group.loc[group["company"] != drop, "market_label"], tie=C.MARKET_TIE_RULE)
            rows.append(dict(quarter=quarter, excluded_company=drop, original_label=base,
                             original_confidence=confidence, revised_label=label, changed=label != base,
                             note="Target-label sensitivity only; model not refitted"))
    frame(rows, "label_sensitivity.csv")


def make_figure(metrics, confusion):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 2, figsize=(12, 4.7))
    selected = metrics[(metrics.company == "Market") & (metrics.evaluation == "walk_forward")
                       & metrics.method.isin(["MGNREGA", "Repeat last"])]
    x = np.arange(len(SCENARIOS))
    for shift, method, color in [(-.18, "MGNREGA", "#2563a6"), (.18, "Repeat last", "#94a3b8")]:
        rows = selected[selected.method == method].set_index("scenario").loc[[s[0] for s in SCENARIOS]]
        bars = axes[0].bar(x + shift, rows.accuracy, width=.34, label=method, color=color)
        axes[0].bar_label(bars, labels=[f"{r.correct}/{r.n}" for r in rows.itertuples()], padding=3)
    axes[0].set_xticks(x, ["Corrected dates", "Early deadline", "Early + 4m lag"])
    axes[0].set_ylim(0, 1)
    axes[0].set_ylabel("Share of correct quarterly calls")
    axes[0].set_title("Timing sensitivity: primary market target")
    axes[0].legend(loc="upper right", frameon=False)
    conf = confusion[(confusion.company == "Market") & (confusion.evaluation == "walk_forward")
                     & (confusion.scenario == "corrected") & (confusion.method == "MGNREGA")]
    matrix = conf.pivot(index="actual", columns="predicted", values="count").reindex(index=LABELS, columns=LABELS).values
    axes[1].imshow(matrix, cmap="Blues", vmin=0, vmax=max(int(matrix.max()), 1))
    for i in range(3):
        for j in range(3):
            axes[1].text(j, i, str(matrix[i, j]), ha="center", va="center",
                         color="white" if matrix[i, j] > matrix.max() / 2 else "#0f172a", fontsize=13)
    axes[1].set_xticks(range(3), LABELS, rotation=15)
    axes[1].set_yticks(range(3), LABELS)
    axes[1].set_xlabel("Predicted direction")
    axes[1].set_ylabel("Observed commentary direction")
    axes[1].set_title("Corrected model: what it gets right and wrong")
    fig.suptitle("MGNREGA research audit | 12 walk-forward quarters", fontsize=14, fontweight="bold")
    fig.text(.5, .01, "Same small historical sample; exploratory reanalysis. Source: checked-in inputs and run_quality.py.",
             ha="center", fontsize=9, color="#475569")
    fig.tight_layout(rect=(0, .04, 1, .94))
    fig.savefig(OUT / "quality_summary.png", dpi=160)
    plt.close(fig)


def write_report(metrics, turns, timing):
    primary = metrics[(metrics.company == "Market") & (metrics.evaluation == "walk_forward")]
    lines = ["# Submission quality audit", "",
             "Generated by `python run_quality.py`. This report preserves the team's model and label decisions.",
             "It restores dropped dates, adds timing sensitivity and reports class-level performance.",
             "These checks reuse the original historical sample: they are exploratory, not independent validation.", "",
             "## Main market-wide results", "",
             "| Scenario | Method | Correct / scored | Balanced accuracy | Classes present |",
             "|---|---|---|---|---|"]
    for r in primary.itertuples():
        balanced = f"{r.balanced_accuracy:.1%}" if pd.notna(r.balanced_accuracy) else "undefined"
        lines.append(f"| {r.scenario} | {r.method} | {r.correct}/{r.n} | {balanced} | {r.classes_present} |")
    lines += ["", "Balanced accuracy averages recall across classes actually observed. A single-class test",
              "cannot establish ability to detect acceleration/slowing, even with perfect accuracy.", "",
              "## Timing checks", "",
              f"- Checked {len(timing)} company-target-quarter rows across three scenarios.",
              f"- Before-results failures: {int((~timing.before_results).sum())}.",
              f"- Required-data-age failures: {int((~timing.lag_respected).sum())}.",
              "- `early_deadline` fixes predictions at quarter-end + 7 days, or earlier if results occur sooner.",
              "- `early_lag4` also adds a fourth month of MGNREGA delay as a conservative sensitivity check.",
              "- Restored Marico/Emami dates were checked against transcript openings (AI audit in `data/raw/call_date_audit.csv`).",
              "  24 match call dates; two Emami inputs precede the call by one day, conservatively retained pending results-release verification.",
              "  HUL/Dabur dates and human source sign-off remain open.",
              "- No historical data snapshots exist. Lag checks implement Thurro's guidance, not proof of exact release vintages.",
              "- Rainfall release timestamps and historic availability of supporting disclosures remain unverified.", "",
              "## Turning-point check", ""]
    for scenario, _, _ in SCENARIOS:
        t = turns[(turns.scenario == scenario) & (turns.company == "Market") & (turns.evaluation == "walk_forward")]
        changed = t[t.actual_changed]
        false_calls = t[t.model_called_change & ~t.actual_changed]
        lines.append(f"- {scenario}: {len(changed)} actual changes from the latest prior label; "
                     f"model got {int(changed.model_correct.sum())} right; {len(false_calls)} false change calls.")
    lines += ["", "## Ranking interpretation", "",
              "`rank` preserves the team's display order. `signal_rank` reports genuine ties in model scores.",
              "Fixed exposure shares include later disclosures applied to earlier quarters. The order is a scenario",
              "illustration, not a point-in-time validation of relative company performance or stock returns.",
              "Company-direction accuracy tests a common market call; it does not validate the relative ordering.", "",
              "## Evidence still requiring human work", "",
              "- `review_queue.csv`: all company quarters, prioritising direction changes, disagreements and draft market labels.",
              "- `volume_review.csv`: check organic/like-for-like basis and document inclusive exceptions.",
              "- `label_sensitivity.csv`: leave-one-company-out changes in the consensus target, without model refitting.",
              "- Two independent team-member labels/reviews have not been documented; AI-reader agreement is not human agreement.",
              "- Source-level dates, quote checks, volume basis and human review must not be marked complete by this script.", "",
              "## Reproduction", "",
              "Install `requirements.txt`, run `python -m unittest discover -s tests -v`, then `python run_quality.py`.",
              "No live credentials or API calls are needed to reproduce the checked-in input snapshot.",
              "The original `outputs/` files remain a historical snapshot; corrected and sensitivity runs are under `runs/` here."]
    (OUT / "REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    metadata = dict(python=platform.python_version(), pandas=pd.__version__, numpy=np.__version__,
                    scenarios=SCENARIOS, interpretation="Exploratory reanalysis of existing sample")
    (OUT / "environment.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
