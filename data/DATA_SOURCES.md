# Data in this folder (pulled 23 Oct 2026 from Thurro)

## raw/mgnrega_state_monthly.csv

National monthly MGNREGA series, Apr 2019 – Sep 2026, built by summing all 34 states/UTs. Each row is one month (the `state` column reads "All States (sum)").

| Column | Meaning | Unit |
|---|---|---|
| persondays | Days of work provided | days, single month (checked: not FY-cumulative) |
| households_worked | Households that got work | count |
| avg_wage_paid_inr | Average wage actually paid, weighted by each state's persondays | ₹ per day |
| notified_wage_inr | Notified wage rate, persondays-weighted | ₹ per day |
| persons_demanded | People who asked for work | count |

**Revision rule:** recent months get revised. Per Thurro, use month M only from M+3; the scripts enforce this.

## raw/rainfall_state_daily.csv

National monthly rainfall, Sep 2022 – Sep 2026. It's the sum of IMD daily state rainfall (35–37 states) for each month, and the partial Oct 2026 is excluded. Despite the file name, rows are monthly totals; script 02 detects this.

- Actual and normal both cover only the days that have data, so `actual / normal − 1` is a valid departure.
- Four months are missing more than 5 days: Sep 2022, Oct 2022, May 2024 and Jun 2024.
- All-India departure is normal-weighted across states, not area-weighted.

## raw/evidence_<company>.csv (HUL, Dabur, Marico, Emami, Market)

Built by `build_label_inputs.py`; one row per quarter (Q1 FY23 to Q1 FY27; the analysis uses Q1 FY24 onward):

- **Dates and volumes:** results date (with its source) and reported domestic volume growth.
- **Quotes:** the company's own-rural quote and its market-rural quote, each with a source link.
- **Labels:** `agreed_label` (own rural) and `market_rural_label` (overall rural market). `label_source` records how each label was made: Q1 FY24 onward from the reconciled second pass in `labels/<company>/labels_final.csv`; FY23 (HUL and Dabur only) from the first pass.
- `evidence_Market.csv` is the market-wide consensus across the four companies.

`call_date_audit.csv` records the source check of the restored Marico and Emami results dates (see `docs/DATE_AUDIT.md`). `company_exposure.csv` holds each company's rural share of India sales with sources.

## raw/ai_readers/

First-pass labels (three LLM readers, 2-of-3 majority) with the quote and source behind every label:

- `reader_A/B/C.csv` = HUL
- `dabur_reader_A/B/C.csv` = Dabur

## State-level MGNREGA

`alternatives/data/` holds state-level MGNREGA (pulled 10 Nov 2026) summed into regions, plus a state breadth measure. See `alternatives/README.md`.
