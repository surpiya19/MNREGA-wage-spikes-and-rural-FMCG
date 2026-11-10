"""Step 9: one table comparing every target (written by run_everything.py).

Reads outputs/run_summary_<TAG>.json from each 05_predict_evaluate.py run and writes
outputs/summary_all_targets.csv and outputs/summary_all_targets.txt.
"""
import json

import pandas as pd

import config as C

rows = [json.loads(p.read_text()) for p in sorted(C.OUT.glob("run_summary_*.json"))]
s = pd.DataFrame(rows)
s.to_csv(C.OUT / "summary_all_targets.csv", index=False)

lines = [f"ALL TARGETS ({C.FIRST_QUARTER} to {C.LAST_QUARTER}; blanks excluded)", ""]
for r in s.itertuples():
    head = f"{r.tag:16s} usable {r.usable:>2} of {r.quarters:<2}"
    if r.status != "tested":
        lines.append(f"{head}  not testable (too few labelled quarters)")
        continue
    wf = f"walk-forward rule {int(r.wf_rule)}/{int(r.wf_n)} vs repeat {int(r.wf_repeat)}, most common {int(r.wf_most_common)}" if pd.notna(getattr(r, "wf_n", None)) else ""
    lines.append(f"{head}  {r.selected:22s} {r.direction:8s} train {r.train_acc:.0%}  test {int(r.test_correct)}/{int(r.test_n)} "
                 f"vs best baseline {r.best_baseline} {int(r.best_baseline_correct)}/{int(r.test_n)};  {wf}")
t = s[s["status"] == "tested"]
if len(t):
    dirs = t["direction"].value_counts().to_dict()
    lines += ["", f"Direction of the selected MGNREGA rule across tested targets: {dirs}."]
    if len(dirs) > 1:
        lines.append("The rules disagree on whether more MGNREGA work means stronger demand (income) or weaker demand "
                     "(distress), so there is no stable MGNREGA relationship to report.")
    wins = int((t["test_correct"] > t["best_baseline_correct"]).sum())
    lines.append(f"Selected rule beat the best baseline on the held-out test in {wins} of {len(t)} tested targets.")
(C.OUT / "summary_all_targets.txt").write_text("\n".join(lines) + "\n")
print("\n".join(lines))
