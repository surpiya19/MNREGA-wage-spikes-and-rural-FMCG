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

## raw/evidence_HUL.csv and raw/evidence_Dabur.csv

One row per quarter, Q1 FY23 – Q1 FY27:

- **Dates and volumes:** results date and reported volume growth.
- **Quotes:** the company's own-rural quote and its market-rural quote, each with a source link.
- **Labels:** `reader1_label`, `reader2_label`, `reader3_label` (own rural), `agreed_label` (2-of-3 majority), `market_reader1`–`3` and `market_rural_label` (market majority).

These labels are **AI drafts** (see `label_source`) and need a human spot-check. The HUL sheet also keeps the earlier suggested labels (`suggested_*` columns) for reference.

## raw/ai_readers/

Each AI reader's full output, with the quote and source behind every label:

- `reader_A/B/C.csv` = HUL
- `dabur_reader_A/B/C.csv` = Dabur

## Not included yet

State-by-state files. You only need them if you want exposure-weighted signals (`STATE_WEIGHTS` in config.py); use README prompts A and B to export them.
