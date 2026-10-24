# MGNREGA and rural FMCG demand

We're testing whether MGNREGA data (rural job-scheme work), which comes out before company results, can predict what FMCG companies say about rural demand on their next earnings call: is it **accelerating, steady or slowing**?

We look at **HUL** and **Dabur** from Q1 FY23 to Q1 FY27 (17 quarters each), using data from Thurro.

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
