# MGNREGA and rural FMCG demand

## Submission quality work (10 November 2026)

The original analysis and saved `outputs/` are retained as a historical snapshot.
For corrected results, deadline sensitivity, class-level accuracy, genuine ranking
ties and the remaining evidence-review queue, start with
[`docs/SUBMISSION_STATUS.md`](docs/SUBMISSION_STATUS.md) and
[`outputs/quality/REPORT.md`](outputs/quality/REPORT.md).

Reproduce the additive audit with Python 3.10:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m unittest discover -s tests -v
python run_quality.py
```

`run_quality.py` writes to `outputs/quality/` and leaves the original saved outputs
alone. It rebuilds evidence inputs from the existing reconciled label files, retaining
label decisions and restoring dates dropped from the Marico/Emami inputs.
The dated November 2026 update below supersedes older sections such as
"Where we are" and "Still to do". In particular, all four companies are connected,
Emami exposure is 52%, the primary target is market-wide, and Q2 FY27 is excluded.
The later quality report adds further corrections and limitations; no human review
is implied by generated provenance fields.

We're testing whether MGNREGA data (rural job-scheme work), which comes out before company results, can predict what FMCG companies say about rural demand on their next earnings call: is it **accelerating, steady or slowing**?

We look at **HUL** and **Dabur** from Q1 FY23 to Q1 FY27 (17 quarters each), using data from Thurro.

## Update after Thurro's feedback (Nov 2026)

Thurro answered our questions on 5 Nov. What changed:

| Thurro said | What we did |
|---|---|
| Make the **market-wide rural trend** the main target; company labels are a secondary check | New primary test: `--company Market --target market`. Each quarter gets one market-wide label: the most common direction across what HUL, Dabur, Marico and Emami said about the overall rural market (ties count as Steady). See `labels/market_wide/`. |
| Leave **blank quarters out** of scoring and show coverage | Blank (Insufficient) quarters are excluded; every results file now starts with a coverage line, and results are given as "X of Y scorable". |
| **Stop at Q1 FY27** | Q2 FY27 rows dropped from all evidence sheets. |
| Treat **July 2026 as a structural break** | Each quarter is tagged with the MGNREGA regime its data falls in (before the 2025 spending cap / spending cap from Aug 2025 / VB-G RAM G from Jul 2026). With the Q1 FY27 cut-off and the 3-month lag, no post-July-2026 month is used. |
| Deliverable = **code + a CSV of the ranked list and its scoring**, plus a short deck | New `07_rank.py` writes `outputs/ranked_list.csv` and `outputs/ranking_scores.txt`. |

Also added:
- **All four companies** run through the pipeline (`data/raw/evidence_<company>.csv`, built from the second labelling pass by `build_label_inputs.py`). FY24 onward use the second-pass own labels; FY23 keeps the first-pass labels for HUL and Dabur.
- **Walk-forward test:** the rule is refitted before every quarter, using only earlier quarters, so 12 quarters get a true out-of-sample prediction instead of 7. Scored separately before and after the Aug 2025 spending cap.
- **A third MGNREGA signal:** persons *asking* for work (need, rather than what the budget allowed).
- **Company exposure:** `data/raw/company_exposure.csv`, rural share of India sales with sources. HUL 33%, Dabur 47%, Emami 52% (from filings; Emami was previously listed as 33%). Marico 31% is an assumption; no disclosure was found.
- **Human check:** the five non-steady own labels (Dabur Q1 FY24, Q3 FY24, Q4 FY25; Emami Q3 FY25, Q3 FY26) were checked by hand against the transcripts. No changes were needed.

**Thurro's data notes, and why they don't change our numbers:**
- Andhra Pradesh's state series reads zero from Jul 2026. The last MGNREGA month we use is Apr 2026 (Q1 FY27 cut-off plus the 3-month lag), so this doesn't reach our results. Use district totals if the window is ever extended.
- 743 vs 694 districts was a join issue on our side; the true count is 739. Our pipeline uses state totals summed to all-India, so it isn't affected.
- Duplicate district names (Pratapgarh 380 = UP, Bilaspur 248 = Chhattisgarh, Hamirpur 382 = UP vs Hamirpurr 561 = HP): always join rainfall on district ID. Our rainfall input is already aggregated to all-India.
- 60-day farm-season pauses show as zeros, not blanks (after Jun 2026 only, so outside our window).

The earlier "Where we are" section below is kept for history; the tables above replace it.

**Run everything:** `python run_everything.py` (labels, all tests and the ranked list, in order).

### Headline results (Q1 FY23 to Q1 FY27)

| Test | MGNREGA rule | Same as last quarter |
|---|---|---|
| **Market-wide rural trend (primary)**, held-out quarters | 6 of 7 | **7 of 7** |
| Market-wide, walk-forward, all quarters | 7 of 12 | **8 of 12** |
| Market-wide, walk-forward, before the spending cap | 4 of 9 | **5 of 9** |
| Dabur own rural, walk-forward, before the spending cap | **5 of 9** | 4 of 9 |
| HUL's market read, walk-forward, before the spending cap | **6 of 9** | 4 of 9 |
| HUL and Marico own rural | can't test: 2 scorable quarters each | |

- **Main finding:** MGNREGA does not beat "same as last quarter" on the primary target. Since mid-2024, all four companies have described the rural market as steady in almost every quarter, so the baseline is very hard to beat.
- **Some signal before the cap:** the rule beats the baseline on two secondary tests (Dabur's own rural label, and HUL's market read), each on 9 quarters. That is too few to claim, but worth showing as a direction.
- **Ranked list:** the market call is Steady in 9 of 12 quarters, so the ranking is mostly decided by rural share, not MGNREGA. Dropping rural share changes the top company in 8 of 12 quarters. Present it as an exposure ordering with a weak MGNREGA overlay.
- **Market labels for Marico and Emami:** these were drafted from the second pass's market text and need a human review. They are in `labels/market_wide/draft_market_labels_marico_emami.csv`.

## What we're doing

- **Question:** can rural income data released before a company's results show which FMCG companies' rural business is about to pick up or slow down? The data is MGNREGA work and wages, with rainfall and state-level UPI payments as controls.
- **Who it's for:** a buy-side FMCG analyst or fund manager. The end product is a quarterly ranked list of companies with a short rationale for each. A district-level map of rural income supports it.
- **Timing:** the signal for a quarter has to be ready before that quarter's results call, using only data that was public at the time. For example, the Jul–Sep signal is due by early October.
- **What counts as success:** Thurro doesn't expect statistical significance with this little history. Beating two simple baselines is enough: last quarter's commentary carried forward, and the market-wide rural trend.

### Methodology in brief

1. **Target.** Each company-quarter gets a label: management describes its own rural business as accelerating, steady or slowing compared with the previous quarter. The label is left blank when management makes no comment. Overall volume growth is recorded alongside as the hard number. Market-wide rural figures, such as Nielsen's, go in a separate market label, which serves as a secondary target.
2. **Point-in-time data.**
   - **MGNREGA:** month M is used only from M+3, because Thurro overwrites revisions and keeps no snapshots.
   - **Rainfall:** a state-level control, from the daily series that starts in Sep 2022.
   - **UPI (planned):** shares will be recomputed from volumes, because the stored share fields mix units. Results will be shown either from Jun 2025 onwards, or with controls for the months when the series breaks.
3. **Company weights (planned, not yet in `config.py`).** Thurro has no distributor or sales footprint data. We will weight states by each company's stated rural share of sales, taken from its filings (HUL about 33%, Dabur about 46%, Marico about 31%, Emami about 33%), times each state's rural population. We will then check that the ranking holds under equal weights and other weightings.
4. **Signal and test.** Simple threshold rules on the MGNREGA signal are fitted on earlier quarters and tested on later ones against the baselines (see *How the model works*).


## Where we are

We fit simple rules on the earlier quarters, then test them on the most recent quarters against the guess "same as last quarter".

| Test | MGNREGA rule | Same as last quarter |
|---|---|---|
| HUL, overall rural market | 4 of 7 | **5 of 7** |
| Dabur, own rural business | 2 of 6 | **5 of 6** |
| Dabur, overall rural market | 1 of 7 | **6 of 7** |
| HUL, own rural business | can't test: HUL only talked about its own rural trend in 3 quarters | |

So far, MGNREGA hasn't beaten "no change" for either company.

- **2023:** rising MGNREGA work lined up with management saying rural was improving.
- **From Aug 2025:** MGNREGA persondays fell 25–54% year on year, but both companies kept calling rural "steady". We think this is the scheme itself changing rather than a rural slowdown. If so, the recent MGNREGA numbers reflect policy more than demand.
- **Sample size:** it's small, so we're treating this as evidence, not proof.

Full results are in `outputs/results_<company>[_market].txt`, and the charts are in `outputs/`.

## Running it

You need Python 3.9+ with pandas, numpy and matplotlib:

```
pip install pandas numpy matplotlib

python run_all.py                                     # HUL, own rural business (runs every step)
python run_all.py --from 3 --target market            # HUL, overall rural market
python run_all.py --from 3 --company Dabur            # Dabur, own rural business
python run_all.py --from 3 --company Dabur --target market
```

- `--from 3` skips the data cleaning, which only needs to run once.
- `--target market` switches from the company's own rural business to its view of the overall rural market.
- `--company Dabur` switches company. Both companies share the MGNREGA and rainfall data.
- Output files are named by company and target (e.g. `results_Dabur_market.txt`), so runs don't overwrite each other.
- `python run_all.py --demo` runs everything on fake data to check your setup. Don't use those numbers anywhere.

## What's in the repo

| Path | What it is |
|---|---|
| `config.py` | Settings: company, target, MGNREGA lag, train/test split |
| `run_all.py` | Runs all the steps in order |
| `01_clean_mgnrega.py` | Cleans the MGNREGA data |
| `02_clean_rainfall.py` | Cleans the rainfall data |
| `03_labels.py` | Reads the labels and checks how often the readers agreed |
| `04_features.py` | Builds the MGNREGA and rainfall signals known on each prediction date |
| `05_predict_evaluate.py` | Fits the rules and tests them against the baselines |
| `06_charts.py` | Makes the charts |
| `data/raw/` | MGNREGA, rainfall, and the evidence sheets (`evidence_HUL.csv`, `evidence_Dabur.csv`) with quotes, sources and labels |
| `data/raw/ai_readers/` | Each reader's labels with the quote and source behind them |
| `data/clean/` | Rebuilt by `run_all.py` (not tracked in git) |
| `outputs/` | Results, predictions and charts |
| `labels/` | Second labelling pass for all four companies (HUL, Dabur, Marico, Emami): two labellers, a reconciler and agreement scores. Not yet read by the pipeline |

## How we labelled the quarters

For each quarter, we labelled what management said compared with the previous quarter:
- **Own label:** about the company's own rural business.
- **Market label:** about the overall rural market (Nielsen data, rural demand, monsoon).

Each label is Accelerating, Steady, Slowing or Insufficient. If a company only talked about the market, its own label stays Insufficient.

We used three AI readers to draft the labels. Each one read every transcript separately, along with filings and press coverage, and we took the 2-of-3 majority.

| | HUL | Dabur |
|---|---|---|
| Agreement between readers (own rural) | 94%, kappa 0.81 | 88%, kappa 0.80 |
| Quarters with a usable own-rural label | 3 | 16 |

We're spot-checking these by hand, starting with the quarters where the readers disagreed or the transcript couldn't be read:

- **HUL:**
  - Q2 FY24 and Q4 FY26 (own label).
  - Q3 FY26 (market label).
  - Q1 FY23, Q3 FY23, Q4 FY23 and Q1 FY25, where the transcripts weren't readable.
- **Dabur own label:** Q3 FY23, Q4 FY23, Q2 FY24 and Q4 FY25.
- **Dabur market label:** Q3 FY23, Q2 FY24, Q1 FY25, Q3 FY25 and Q1 FY27.

To change a label, edit `agreed_label` or `market_rural_label` in the evidence sheet, save it as CSV, and rerun with `--from 3`.

## Second labelling pass: all four companies (`labels/`)

We also labelled **HUL, Dabur, Marico and Emami** for Q1 FY24 to Q2 FY27 (14 quarters each), using the filings in the Thurro corpus. Each company had two labellers working independently from a written guide (`labels/labelling_guide.md`). A third reconciler then checked every disagreement against the source. Thurro asked for two readers and an agreement score, so this pass follows that setup. The pass above took a three-reader majority instead.

**How the labelling works:**
- **Sources:** each quarter's earnings-call transcript is the main source. The investor presentation, the quarterly update and any pre-results business update are also used. Only documents public by that quarter's results call count.
- **Company or market:** a rural remark counts as the company's own only if it is about the company, with "we", "our", "for us" or the company's name as the subject. Remarks citing Nielsen, "the category" or "the industry", and opening remarks about the economy, go in the market columns.
- **Decision rules:**
  - A level is not a direction: "rural ahead of urban" on its own is steady.
  - Numbers beat adjectives, and a change of 2 percentage points or less is steady.
  - "Resilient", "sustaining" and "recovery continuing" mean steady. Accelerating needs a comparison, such as "faster" or "picked up".
  - Outlook statements don't count.
  - A comment about one brand or one region doesn't override what is said about the whole business.
- **Confidence:** high only when the company gives its own rural numbers, or explicitly says which way its own rural business moved. Otherwise low.
- **Process:**
  1. We piloted the guide on Dabur and revised it (v2).
  2. Two labellers then worked on each company without seeing each other's labels.
  3. Agreement was scored before reconciling: percent agreement, Cohen's kappa, and weighted kappa on the rows where both labellers gave a direction. The target was a kappa of 0.6 or higher.
  4. The reconciler re-read the source for every disagreement and wrote down the reason for each final label.

| Company | Agreement | Cohen's kappa | Final labels (13 scored quarters) |
|---|---|---|---|
| Dabur | 85% | 0.60 | 11 steady, 1 accelerating, 1 slowing |
| HUL | 92% | 0.72 | 11 blank, 2 steady |
| Marico | 77% | 0.20 | 11 blank, 2 steady |
| Emami | 77% | 0.65 | 6 blank, 5 steady, 2 accelerating |
| All four | 83% | 0.71 | |

- **"Blank"** here means the same as "Insufficient" above: management made no comment about the company's own rural business.
- **HUL and Marico** almost never talk about their own rural trend. In 11 of 13 quarters, their rural comments are about the market or Nielsen data.
- **Dabur** comments every quarter, but nearly always calls rural steady.
- **Emami** is the only company whose label changes direction.
- **Company totals:** Marico's low kappa comes from having so few labels, not from many disagreements.
- **Overall:** labels about each company's own rural business give us too few changes to test against on their own, so the market label, or overall volume growth, may need to be the main target.

**Files:**
- `labels/<company>/labels_A.csv` and `labels_B.csv`: the two labellers.
- `labels/<company>/labels_final.csv`: the reconciled labels, with the reason for each decision.
- `labels/<company>/reconciliation_report.md`: the disagreements, data gaps and suggested changes to the guide.
- `labels/rural_labels_all_companies.csv`: all four companies in one file.

To check the agreement scores, run `python labels/<company>/score_agreement.py labels/<company>/labels_A.csv labels/<company>/labels_B.csv`.

**Still to do:**
- Re-label Q2 FY27 once the transcripts are filed (HUL and Marico have reported; Dabur and Emami report on 5 Nov).
- Copy these labels into the `data/raw/evidence_<company>.csv` sheets so the pipeline can use them.

## How the model works

- **Prediction date:** the day before results.
- **MGNREGA lag:** we only use a month's MGNREGA data once it's 3 months old, because recent months get revised.
- **Signals:** the change in year-on-year growth of MGNREGA persondays, and of a proxy wage bill (persondays × average wage). Year-on-year growth removes the seasonality.
- **Rainfall:** the monsoon (Jun–Sep) departure from normal, either this monsoon so far or the last completed one. Our rainfall data starts in Sep 2022, so the first full monsoon is 2023.
- **Rule:** above a cut-off means Accelerating, below a cut-off means Slowing, and in between means Steady. We try both directions, because more MGNREGA work could mean rural distress or more rural income.
- **Train/test:** we pick the cut-offs on the first 60% of labelled quarters and test on the rest. The headline rule is always an MGNREGA rule. Rainfall rules are shown for comparison.
- **Baselines** (scored on the same quarters):
  - same as last quarter
  - follow the previous call's market comment (own-rural test only)
  - the most common label

## Caveats

- The wage bill is a proxy; there's no direct wage-payment series.
- Persondays fell sharply from Aug 2025, which looks like a policy change, so the latest quarters partly test the policy rather than rural demand.
- We only have 6–7 test quarters, so a single quarter can change the conclusion.
- About 10 quarters are used for training, and only 6 of them have rainfall data.

## Data

See `data/DATA_SOURCES.md`.
- **MGNREGA and rainfall:** from Thurro (MGNREGA MIS and IMD).
- **Quotes:** from company filings on NSE/BSE plus press coverage, with links in the evidence sheets.

If the column names in a new data export are different, update `MGNREGA_COLUMNS` / `RAIN_COLUMNS` in `config.py` instead of renaming the file. State-level weights (e.g. weighting Dabur towards the North) can go in `STATE_WEIGHTS` in `config.py`; we haven't used them yet.
