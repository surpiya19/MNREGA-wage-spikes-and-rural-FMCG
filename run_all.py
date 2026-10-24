"""Run the steps in order.

  python run_all.py            # real data in data/raw/
  python run_all.py --demo     # fake data, to test the pipeline
  python run_all.py --from 4   # re-run from step 4 onward (e.g. after relabelling)
  python run_all.py --from 3 --target market   # predict the market-rural label instead
  python run_all.py --from 3 --company Dabur   # run for Dabur (uses data/raw/evidence_Dabur.csv)
"""
import argparse
import os
import subprocess
import sys

STEPS = ["01_clean_mgnrega.py", "02_clean_rainfall.py", "03_labels.py",
         "04_features.py", "05_predict_evaluate.py", "06_charts.py"]

ap = argparse.ArgumentParser()
ap.add_argument("--demo", action="store_true")
ap.add_argument("--from", dest="start", type=int, default=1)
ap.add_argument("--target", choices=["own", "market"], default=None)
ap.add_argument("--company", default=None, help="e.g. HUL or Dabur (default: COMPANY in config.py)")
a = ap.parse_args()

env = dict(os.environ)
if a.target:
    env["RURAL_TARGET"] = a.target
if a.company:
    env["RURAL_COMPANY"] = a.company
here = os.path.dirname(os.path.abspath(__file__))
if a.demo:
    env["RURAL_DEMO"] = "1"
    subprocess.run([sys.executable, "00_make_demo_data.py"], cwd=here, env=env, check=True)

for step in STEPS[a.start - 1:]:
    print(f"\n{'=' * 70}\n{step}\n{'=' * 70}")
    r = subprocess.run([sys.executable, step], cwd=here, env=env)
    if r.returncode != 0:
        sys.exit(f"Stopped at {step}. Fix the message above, then run again with --from {STEPS.index(step) + 1}.")
