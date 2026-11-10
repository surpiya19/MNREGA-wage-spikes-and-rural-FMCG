"""Rebuild everything after the Thurro feedback (Nov 2026), in one go.

  python run_everything.py          # labels -> all tests -> ranked list
  python run_everything.py --skip-clean   # skip MGNREGA/rainfall cleaning (faster)

Order:
  1. build_label_inputs.py   evidence sheets for HUL, Dabur, Marico, Emami + market-wide labels
  2. run_all.py              PRIMARY: market-wide rural trend (--company Market --target market)
  3. run_all.py              SECONDARY: each company's own rural label, and each company's market read
  4. 07_rank.py              ranked list of companies per quarter + its scoring
"""
import subprocess
import sys

skip = "--skip-clean" in sys.argv
py = sys.executable


def run(args):
    print(f"\n### {' '.join(args)}")
    r = subprocess.run([py] + args)
    if r.returncode != 0:
        sys.exit(f"Stopped at: {' '.join(args)}")


run(["build_label_inputs.py"])
run(["run_all.py", "--from", "3" if skip else "1", "--company", "Market", "--target", "market"])
for co in ["HUL", "Dabur", "Marico", "Emami"]:
    for t in ["own", "market"]:
        run(["run_all.py", "--from", "3", "--company", co, "--target", t])
run(["07_rank.py"])
run(["08_summary.py"])
print("\nDone. Headline results: outputs/results_Market_market.txt and outputs/ranking_scores.txt")
