# Alternative tests (10 Nov 2026)

Three extra tests of the MGNREGA → rural FMCG idea. They add to the main pipeline and change none of its files, labels or outputs. They use the same window as the main pipeline (`config.FIRST_QUARTER`–`LAST_QUARTER`, currently Q1 FY24–Q1 FY27).

Run from the repo root (about 1.5 minutes because of the permutation tests):

```bash
python3 alternatives/run_alternatives.py
```

## What's here

| Path | What it is |
|---|---|
| `data/mgnrega_region_quarterly.csv` | Thurro state-level MGNREGA (pulled 10 Nov 2026), summed into North/East/West/South by quarter: persondays and persons demanding work, in lakh. The four regions add up to the national totals in `data/raw/mgnrega_state_monthly.csv`. |
| `data/mgnrega_state_breadth_quarterly.csv` | For each quarter: the share of states (with more than 10 lakh persondays a year earlier) whose persondays rose year on year, and the median state's growth. |
| `run_alternatives.py` | All three tests. |
| `outputs/RESULTS.txt` | Summary of results. The CSVs beside it hold the detail. |

Region mapping: **North** is UP, Rajasthan, Punjab, Haryana, HP, J&K, Ladakh and Uttarakhand. **East** is Bihar, Jharkhand, Odisha, WB, Assam and the North-East. **West** is Maharashtra, Gujarat, MP, Chhattisgarh, Goa and DNH&DD. **South** is AP, Telangana, Karnataka, TN, Kerala, Puducherry, Lakshadweep and A&N. Putting MP and Chhattisgarh in West is our own choice.

## The three tests

**A/B. Numeric target.** The target is each company's reported domestic volume growth, and whether it speeds up or slows down from last quarter. That gives 44 company-quarters: volume growth sped up in 25, slowed in 15 and was unchanged in 4. The market-wide label, by comparison, is Steady in almost every quarter. The signal comes from the calendar quarter before the target quarter, which ends at least 111 days before the results date.
- A: rank correlations, with p-values from within-company shuffles. The persondays change was fixed in advance as the main test, and everything else is exploratory.
- B: walk-forward pooled forecast, comparing MGNREGA plus mean reversion against mean reversion only and against "no change".

**Broader signals.** Persondays, work demanded, work given relative to work demanded, state breadth, the median state's growth, and an Emami-specific signal weighted by its disclosed regional sales split (Annual Report FY19: N 33, E 20, W 28, S 19). No other company has disclosed a regional split in the Thurro corpus, and Thurro's store-location data doesn't cover these four companies. So true company footprints aren't available, and HUL, Dabur and Marico use the national signal.

**C. Turning points.** Using the team's existing walk-forward label backtest (`outputs/quality/turning_points.csv`, corrected scenario), this measures how often a change call by the model was right (precision) and how many real changes it caught (recall).

## Findings (Q1 FY24–Q1 FY27)

- **The numeric target doesn't rescue the signal.** None of the 24 correlation tests reaches p < 0.05. The main test (change in persondays vs change in volume growth) gives rho +0.18 (p = 0.33) before the spending cap.
- **The walk-forward forecast adds nothing reliable.** Adding an MGNREGA feature to mean reversion gives an error of 3.59–3.88 pp against 3.70 pp. Before the cap it's 3.30–3.47 pp against 3.33, and "no change" does best there at 3.18. Direction calls are 20 of 32 against 19 of 32, which is one quarter.
- **The earlier lead fades:** work given relative to work demanded was rho +0.33 (p 0.051) when FY23 was included. In this window it's +0.27 (p 0.15). Re-test it on a longer history (FY15 onward) before saying anything about it.
- **Turning points:** across all company-targets, the label model made 17 change calls and 2 were right (precision 0.12). It caught 2 of 8 real changes (recall 0.25). The market-wide label has no turning points at all in the walk-forward quarters (Q3 FY25–Q1 FY27). "Repeat last quarter" catches 0 by construction.

## Limits

- Volume growth isn't yet on a single like-for-like basis per company (`outputs/quality/volume_review.csv` is still pending). Emami's −16% in Q2 FY26 (the GST transition) and −7% in Q4 FY26 are large one-offs. Rank-based tests limit their influence.
- Two Dabur volume figures in the window are missing (Q2 FY25, Q4 FY25), so Dabur contributes only 8 rows.
- Nielsen rural vs urban growth wasn't turned into a numeric series. Companies quote it on mixed bases (year on year, 2-year and 4-year CAGR), and HUL often shows it only as a chart. That needs a manual pass.
- The 111-day minimum gap meets the 3-month revision rule but not the 4-month delay used as a sensitivity check.
