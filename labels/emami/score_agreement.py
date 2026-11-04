#!/usr/bin/env python3
"""Inter-annotator agreement for the Emami rural-direction pilot.

Usage: python3 score_agreement.py labels_A.csv labels_B.csv

Scores the 13 quarters Q2 FY24..Q2 FY27 (Q1 FY24 is baseline only).
Outputs: percent agreement, Cohen's kappa (4 labels incl. blank),
linear-weighted kappa on rows where both gave a direction, blank agreement.
"""
import csv
import sys
from collections import Counter

LABELS = ["accelerating", "steady", "slowing", "blank"]
ORD = {"slowing": 0, "steady": 1, "accelerating": 2}
BASELINE = "Q1 FY24"


def load(path):
    out = {}
    with open(path, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            lab = (r["company_label"] or "").strip().lower() or "blank"
            out[r["quarter"].strip()] = lab
    return out


def cohen_kappa(a, b, cats):
    n = len(a)
    po = sum(x == y for x, y in zip(a, b)) / n
    ca, cb = Counter(a), Counter(b)
    pe = sum((ca[c] / n) * (cb[c] / n) for c in cats)
    return po, pe, (po - pe) / (1 - pe) if pe < 1 else float("nan")


def weighted_kappa(a, b, k=3):
    n = len(a)
    if n == 0:
        return float("nan")
    w = lambda i, j: abs(i - j) / (k - 1)  # linear disagreement weight
    obs = sum(w(x, y) for x, y in zip(a, b)) / n
    ca, cb = Counter(a), Counter(b)
    exp = sum(w(i, j) * (ca[i] / n) * (cb[j] / n) for i in range(k) for j in range(k))
    return 1 - obs / exp if exp > 0 else float("nan")


def fmt(x):
    return "undefined (expected disagreement = 0)" if x != x else f"{x:.3f}"


def main():
    if len(sys.argv) != 3:
        sys.exit("usage: score_agreement.py labels_A.csv labels_B.csv")
    A = load(sys.argv[1])
    B = load(sys.argv[2])
    order = list(A.keys())
    assert set(order) == set(B.keys()), "quarter sets differ"
    scored = [q for q in order if q != BASELINE]
    assert len(scored) == 13, scored
    a = [A[q] for q in scored]
    b = [B[q] for q in scored]

    print("Quarter-by-quarter (scored):")
    for q, x, y in zip(scored, a, b):
        print(f"  {q:8s} A={x:12s} B={y:12s} {'agree' if x == y else 'DISAGREE'}")
    print(f"  (baseline {BASELINE}: A={A[BASELINE]}, B={B[BASELINE]})")

    po, pe, k = cohen_kappa(a, b, LABELS)
    agree = sum(x == y for x, y in zip(a, b))
    print(f"\nN scored quarters: {len(scored)}")
    print(f"Percent agreement: {agree}/{len(scored)} = {po:.1%}")
    print(f"Cohen's kappa (4 labels): po={po:.3f} pe={pe:.3f} kappa={fmt(k)}")

    dir_rows = [(ORD[x], ORD[y]) for x, y in zip(a, b) if x != "blank" and y != "blank"]
    wk = weighted_kappa([r[0] for r in dir_rows], [r[1] for r in dir_rows])
    dagree = sum(x == y for x, y in dir_rows)
    print(f"Linear-weighted kappa (both directional, n={len(dir_rows)}, "
          f"raw agree {dagree}/{len(dir_rows)}): {fmt(wk)}")

    both_blank = sum(x == "blank" and y == "blank" for x, y in zip(a, b))
    any_blank = sum(x == "blank" or y == "blank" for x, y in zip(a, b))
    print(f"Blank agreement: both blank={both_blank}, either blank={any_blank}, "
          f"blank disagreements={any_blank - both_blank}")

    print("\nLabel distribution A:", dict(Counter(a)))
    print("Label distribution B:", dict(Counter(b)))
    print("Disagreements:", [q for q, x, y in zip(scored, a, b) if x != y])


if __name__ == "__main__":
    main()
