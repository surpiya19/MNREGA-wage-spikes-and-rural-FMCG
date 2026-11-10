# MGNREGA and rural FMCG demand

Can MGNREGA data (India's rural employment scheme), which is published before company results, tell us what FMCG companies will say about rural demand on their next earnings call: is it **accelerating, steady or slowing**?

We test this for **HUL, Dabur, Marico and Emami** from **Q1 FY24 to Q1 FY27** (13 quarters), using MGNREGA, rainfall and company filings from Thurro. The audience is a buy-side FMCG analyst; the deliverable is a quarterly ranked list of companies with its scoring, plus the code to rebuild it.

## Main finding

MGNREGA does not beat simple baselines.

| Test (Q1 FY24 to Q1 FY27) | MGNREGA rule | Same as last quarter |
|---|---|---|
| **Market-wide rural trend (primary)**, held-out quarters | 1 of 5 | **5 of 5** |
| Market-wide, walk-forward (refit every quarter) | 4 of 7 | **7 of 7** |
| Market-wide, walk-forward, before the Aug 2025 spending cap | 2 of 4 | **4 of 4** |
| Dabur own rural, walk-forward, before the cap | **4 of 5** | 3 of 5 (most common label also 4 of 5) |
| HUL's read of the market, walk-forward, before the cap | 2 of 5 | 2 of 5 |
| HUL, Marico and Emami own rural | not testable: 2, 2 and 7 usable quarters | |

- **No target was beaten.** Across the six testable targets, the selected MGNREGA rule never beat the best baseline on held-out quarters (`outputs/summary_all_targets.txt`).
- **No stable direction.** The fitted rules disagree on what more MGNREGA work means: 4 read it as distress, 2 as stronger demand.
- **The target barely moves.** Every walk-forward quarter of the market-wide label (Q3 FY25 to Q1 FY27) is Steady, so "same as last quarter" is perfect and there are no turning points to catch.
- **Policy, not demand, from Aug 2025.** Persondays fell 25–54% year on year after the spending cap, ahead of MGNREGA's replacement by VB-G RAM G in Jul 2026, while companies kept calling rural steady.
- **A numeric target doesn't change this.** Using reported volume growth instead of labels, and state-level MGNREGA signals, none of 24 correlation tests reaches p < 0.05 and the forecast doesn't improve on mean reversion (`alternatives/`).
- **Ranked list:** the market call is right in 4 of 7 quarters (baseline 7 of 7), and dropping the rural-share weights changes the top company in 5 of 7 quarters. It is an exposure ordering with a weak MGNREGA overlay, not an investable signal.

With this few quarters, one quarter can change any comparison, so results are reported as counts.

## Quick start

Python 3.10, from the repo root:

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

python run_everything.py                      # labels -> all nine backtests -> ranked list -> summary
python run_quality.py                         # timing checks, sensitivity runs, class-level metrics
python -m unittest discover -s tests -v       # tests
python alternatives/run_alternatives.py       # numeric-target and state-level tests (~1.5 min)
```

One target at a time: `python run_all.py --from 3 --company Dabur --target market` (`--from 3` skips data cleaning; `--target own` or `market`; `--company Market` is the market-wide consensus). `python run_all.py --demo` runs on fake data to check the setup.

## Method

**Targets.** For each company-quarter we label what management said about rural demand compared with the previous quarter:
- *Own rural:* the company's own rural business.
- *Market:* the overall rural market (Nielsen, sector commentary).
- *Market-wide (primary target, at Thurro's request):* the most common market direction across the four companies. Ties and Accelerating-vs-Slowing splits have no consensus and are left out of scoring (`MARKET_TIE_RULE` in `config.py`; `RURAL_MARKET_TIE=Steady` restores the earlier convention).

Each label is Accelerating, Steady, Slowing or Insufficient (no relevant comment). Insufficient quarters are excluded from scoring and coverage is reported in every results file.

**Labelling.** Labels follow a written guide (`labels/labelling_guide.md`, v2). Key rules: a remark is "own" only if the company is the subject; a level ("rural ahead of urban") is not a direction; numbers beat adjectives and a change of 2 points or less is steady; outlook statements don't count. Each company was labelled by two independent LLM-assisted labellers, agreement was scored before reconciliation (Cohen's kappa 0.54–0.72, except Marico at 0.15 because almost every label is blank), and every disagreement was then reconciled against the source with a written reason. The non-steady own labels were checked by hand against the transcripts. Market labels for Marico and Emami are drafts that still need a human review (`labels/market_wide/`). Details: `labels/labelling_results_summary.md`.

**Window.** Q1 FY24 to Q1 FY27 (`FIRST_QUARTER`, `LAST_QUARTER`). FY23 labels exist only from a first pass (three readers, majority vote, no reconciliation), so FY23 is excluded. Q2 FY27 is excluded per Thurro.

**Point-in-time data.**
- Prediction date: the day before results. A stricter early-deadline variant (quarter-end + 7 days) and a 4-month MGNREGA delay are run as sensitivity checks (`outputs/quality/`).
- MGNREGA month M is used only from M+3, because recent months are revised and no historical snapshots exist.
- Results dates are sourced per company; 26 Marico and Emami dates were restored and checked against the transcripts (`docs/DATE_AUDIT.md`).

**Signals.** Change in year-on-year growth of MGNREGA persondays, a proxy wage bill (persondays × average wage paid) and persons demanding work; monsoon rainfall departure as a comparison. Each quarter is tagged with its MGNREGA regime: before the spending cap, spending cap (from Aug 2025), VB-G RAM G (from Jul 2026, outside the window after the lag).

**Rules and testing.** Threshold rules (above a cut-off = Accelerating, below = Slowing) are fitted in both directions, since more MGNREGA work could mean income or distress. Two tests: a 60/40 train/test split, and a walk-forward test that refits before every quarter. A rule needs at least 6 training and 2 test quarters (`MIN_TRAIN_QUARTERS`). Baselines on the same quarters: same as last quarter, most common label, always Steady, and (own-rural only) the previous call's market comment.

**Ranked list.** `07_rank.py` ranks the four companies each quarter by the market call times each company's rural share of India sales (HUL 33%, Dabur 47%, Emami 52% from filings; Marico 31% is an assumption), with an equal-weights check.

## Alternative tests (`alternatives/`)

- **Numeric target:** reported domestic volume growth and whether it speeds up or slows down (44 company-quarters).
- **State-level signals:** regional MGNREGA, the share of states with persondays up year on year, the median state, work given relative to work demanded, and an Emami signal weighted by its disclosed regional sales split. Other companies don't disclose regional splits.
- **Turning points:** the label model caught 2 of 8 real changes, and 2 of its 17 change calls were right.

The closest thing to a lead is work given relative to work demanded (rho +0.27, p 0.15 before the cap), worth re-testing on a longer history. See `alternatives/README.md`.

## Repo layout

| Path | What it is |
|---|---|
| `config.py` | Settings: window, company, target, lags, tie rule, train/test split |
| `run_everything.py` / `run_all.py` | Full rebuild / one company-target |
| `01`–`02_clean_*.py` | Clean MGNREGA and rainfall |
| `build_label_inputs.py` | Builds `data/raw/evidence_<company>.csv` and the market-wide labels from `labels/` |
| `03_labels.py` | Label summary and agreement |
| `04_features.py` | Point-in-time MGNREGA and rainfall signals |
| `05_predict_evaluate.py` | Fits rules, tests against baselines, walk-forward test |
| `06_charts.py`, `07_rank.py`, `08_summary.py` | Charts, ranked list and scoring, all-target summary |
| `run_quality.py`, `quality_core.py`, `tests/` | Timing checks, sensitivity runs, metrics and tests (also run by `.github/workflows/quality.yml`) |
| `labels/` | Labelling guide, both labellers' files, reconciled labels and reports per company |
| `data/raw/` | MGNREGA, rainfall, evidence sheets, exposure and date audit (`data/DATA_SOURCES.md`) |
| `alternatives/` | Numeric-target and state-level tests |
| `outputs/` | Results, predictions, charts, `ranked_list.csv`, `ranking_scores.txt`, `summary_all_targets.txt` |
| `outputs/quality/` | `REPORT.md`, metrics, turning points, review queues |
| `docs/` | Submission status and date audit |

## Thurro data notes

- Andhra Pradesh's state series reads zero from Jul 2026; the last MGNREGA month used is Apr 2026, so results are unaffected.
- District counts (743 vs 694; true 739) and duplicate district names only matter for district joins; the pipeline uses state totals.
- 60-day farm-season pauses show as zeros after Jun 2026, outside the window.

## Limitations and open work

- **Small sample:** 5–8 scored quarters per test.
- **Human review is still pending** for the Marico and Emami market labels, and independent review by two team members hasn't been recorded (`outputs/quality/review_queue.csv`).
- **Volume growth** isn't yet on one like-for-like basis per company (`outputs/quality/volume_review.csv`).
- **Nielsen rural vs urban growth** is quoted on mixed bases and wasn't turned into a numeric series.
- **No historical snapshots:** the 3-month MGNREGA lag approximates what was known at the time.
- **Wage bill is a proxy:** there's no direct wage-payment series.
- **Not used:** UPI and district-level weighting.
- **Older agreement scripts:** the per-company `labels/<company>/score_agreement.py` scripts score Q2 FY24 to Q2 FY27; the figures quoted above come from the pipeline window.
