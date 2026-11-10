# Submission status and contribution

## Scope and attribution

This contribution extends Supriya's original data, labelling and analysis and Hadley's
6 November integration of Thurro's feedback. It retains their model family, label
decisions, raw employment/rainfall observations and historical saved outputs.
The baseline reviewed is commit `2d419451569867e548de6997f7448d1afbcbb7f7`.

Sponsor clarification sequence (provided to the team; original correspondence is not republished here):

1. Original brief: use district MGNREGA wage spikes to anticipate a company's rural acceleration.
2. First Q&A: label own-company rural direction; use overall volume as supporting evidence;
   separate market commentary; compare with simple baselines; serve buy-side analysts.
3. Later Q&A: primary target becomes market-wide rural trend, own labels secondary;
   exclude blanks and show coverage; stop at Q1 FY27; deliver code, ranked CSV and scoring.
   Prefer consistent organic/like-for-like domestic volume per company, marking exceptions.

## Completed in this contribution

- Reproduced the existing end-to-end pipeline locally before making changes.
- Restored 26 dropped results dates (13 each for Marico and Emami) using agreement
  between the original A/B reader files. An AI audit checked all 26 against original
  transcript openings: 24 match, and two Emami dates precede the call by one day.
  Those earlier dates remain conservative inputs pending results-release verification.
  Evidence URLs and document fingerprints are in `data/raw/call_date_audit.csv`.
- Corrected trailing punctuation breaking two Marico transcript URLs, after successfully
  opening the corrected addresses. Original individual-reader files are retained.
- Made each company's reconciled file authoritative, so editing `labels_final.csv`
  actually reaches the pipeline instead of silently using a stale combined copy.
- Preserved label decisions, added date provenance and retained complete reconciliation
  notes. Summary text is explicitly identified as a summary, not an exact quotation.
- Removed generated claims that draft market labels were already human-reviewed.
- Added a conservative early-next-quarter deadline (quarter-end + 7 days, capped before
  results) and an additional four-month data-delay sensitivity. Original default remains available.
- Rejects missing dates for before-results predictions rather than silently inventing dates.
- Added reproducible quality runs with isolated outputs, input fingerprints and pinned dependencies.
- Added accuracy, balanced accuracy, per-class precision/recall, confusion counts,
  turning-point records and an always-Steady comparison on common evaluation quarters.
- Added a leave-one-company-out sensitivity of the *target labels*, without claiming it
  is a refitted predictive backtest.
- Retained the original display ranking and added `signal_rank` so score ties remain visible.
  Fixed-exposure rankings are explicitly marked as scenarios, not historical investable rankings.
- Added a complete human-review queue and a volume-comparability worksheet.
- Added automated tests and a GitHub workflow that reproduces and uploads the quality outputs.

## How to read the results

Start with `outputs/quality/REPORT.md`, then `metrics.csv` and `turning_points.csv`.
`runs/corrected/` uses restored dates and the original before-results convention.
`runs/early_deadline/` uses the stricter deadline. `runs/early_lag4/` adds a fourth month of lag.
Each contains text results, predictions and a ranked list. No new model was selected using
the sensitivity results. All checks reuse the original sample and remain exploratory.

Important boundaries:

- The market target is a management-commentary consensus, not independently measured rural sales.
- A target that stays Steady is easy to predict without providing advance warning of changes.
- Geography is national in the checked-in data; company-specific state footprints are not established.
- Fixed rural shares include later disclosures and an assumed Marico share. Direction scoring
  does not validate the relative ordering of companies or investment returns.
- Programme-break explanations originate in sponsor feedback; they are not causal findings from this model.
- Thurro's three-month delay is an approximation in the absence of stored historical snapshots.

## Remaining before declaring the research complete

| Work | Status | Concrete next action |
|---|---|---|
| Draft market labels | Open | Human-review Marico/Emami source passages; record decisions in review queue and source label files |
| Independent team-member review | Open | Two people review labels independently; calculate agreement before reconciliation |
| Source dates and quotation accuracy | Open | Verify against dated calls/documents, prioritising restored dates and directional changes |
| Volume consistency | Open | Complete `volume_review.csv`; choose one organic/like-for-like basis per company and mark exceptions |
| Exact public availability | Open | Check business-update dates and rainfall release timing; retain the early-deadline result as sensitivity |
| Company ranking validation | Limited | Present as exposure scenario unless point-in-time footprints and a relative-performance target are established |
| District map | Optional supporting visual | Build only with documented district joins, zero handling and coverage; not required to run current model |
| UPI | Optional extension | Exclude unless a stable-window test adds credible evidence; do not rush it into the headline result |
| Deck | Outside current coding scope | Use the verified findings and limitations if preparing one later |

No script can provide genuine independent human sign-off. Pending review must remain
visible in the submission; do not change it to complete based on AI agreement alone.

## Minimal final checks

1. Run the tests and `python run_quality.py` in a fresh environment.
2. Complete the prioritised evidence review; make actual label changes in the source files,
   not only in the generated review worksheet. The generated queue resets on every run,
   so save completed human reviews separately (for example `labels/human_reviews.csv`).
3. Rerun after corrections and update the final narrative from the resulting numbers.
4. Present coverage, baseline comparisons and weak-signal limitations alongside the ranking.

## Additional research worth pursuing only after verification

The best focused extension is separating demand for programme work from work supplied
under programme constraints. A handful of predefined timing windows could be tested,
with a full experiment log. Avoid a large model search on the same tiny history.
Rural share multiplied by the same state population weights does not create distinctive
normalised company footprints; geographic differentiation needs additional company evidence.
