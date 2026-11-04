# Emami Limited: rural direction reconciliation (guide v2)

Labellers A and B, Q1 FY24 to Q2 FY27 (14 quarters, 13 scored). Scored with `python3 score_agreement.py labels_A.csv labels_B.csv`.

## Agreement (13 scored quarters, Q2 FY24 to Q2 FY27)

| Metric | Value |
|---|---|
| Percent agreement (4 labels incl. blank) | 10/13 = 76.9% |
| Cohen's kappa (4 labels) | 0.645 (po 0.769, pe 0.349) |
| Linear-weighted kappa, both directional (slowing<steady<accelerating) | 0.417, n = 7 (raw agreement 5/7) |
| Blank agreement | both blank 5; either blank 6; blank disagreements 1 (Q3 FY24) |
| Baseline Q1 FY24 (not scored) | A steady, B blank: disagree |

Distributions: A has 5 steady, 3 accelerating and 5 blank. B has 4 steady, 3 accelerating and 6 blank. Neither labeller used slowing.
Against the final labels: A matches 11/13 and B matches 12/13 on the scored quarters.

## Disagreements and resolution

| Quarter | A | B | Final | Conf. | Reason |
|---|---|---|---|---|---|
| Q1 FY24 (baseline) | steady | blank | blank | n/a | The only rural comment answers a generic "is the worst over for rural demand?" question with no we/our subject, so it is market commentary. "GT has not declined. It is flat" is about the general-trade channel, which covers urban and rural (it was dragged down by Navratna sachets), so it is not a rural statement. |
| Q3 FY24 | steady | blank | blank | n/a | "Quarter 3 saw similar demand trends witnessed in Q2 with lower rural offtakes" is the opening macro-demand sentence and has no own subject. "The rural market is under stress" is also market. A second search found no own-subject rural line. |
| Q4 FY24 | accelerating | steady | steady | low | Mohan Goenka confirms the source ("I am talking about our internal numbers") but describes it in his own words as "some signs of recovery from all corners". Recovery counts as steady under rule 7. "Pickup" was the analyst's paraphrase of an opening remark that only said "rural market is also witnessing a recovery". |
| Q1 FY25 | steady | accelerating | steady | low | "Overall, the uptick is everywhere" has no own subject and is set against the following "for our business" clause, so it is treated as market. The own content is a regional level comparison (North a little ahead, East doing well), which is steady under rules 1 and 10. |

High-confidence checks: Q3 FY25 holds (Mohan Goenka: "at least for us, there has been an improvement in the rural growth", answering a direct question on rural-vs-urban growth over the last quarter or two). Q3 FY26 also holds, on two separate own statements. Manish Gupta said "this would be obviously a better quarter than the previous one... double-digit". Mohan Goenka answered "Yes, Harit. So absolutely" when asked whether rural is seeing an incremental pickup. Only these two quarters are high-confidence in either file; the brief mentioned three, but there is no third.

## Number disagreements resolved

| Quarter | Field | A | B | Final | Basis |
|---|---|---|---|---|---|
| Q1 FY24 | volume | (blank) | 3 | 3 | Domestic volume +3% (opening remarks) |
| Q3 FY24 | volume | -0.9 "consolidated" | -0.9 | -0.9 | Domestic volume (Q&A answer to the domestic-volume question). A's "consolidated" label was wrong |
| Q4 FY24 | own rural | 7 | (blank) | 7 | General trade only, rural (urban GT 8%). Excludes MT, e-com and CSD. No prior-quarter comparator |
| Q2 FY25 | volume | 1.7 | (blank) | 1.7 | Domestic volume, from the performance snapshot |
| Q4 FY25 | volume | 7 | 5 | 7 | Core domestic (+5% includes the strategic investments Helios and Brillare) |

Volume basis by quarter: Q3 FY25, Q4 FY25 and Q1 FY26 (ex-talc/PHP) are core domestic. Q1 FY27 is like-for-like. All other quarters are total domestic. Q4 FY26 is total domestic (-7%); the alternative figure, +7%, is ex-summer.

## Final labels

| Quarter | Label | Conf. |
|---|---|---|
| Q1 FY24 | blank (baseline) | n/a |
| Q2 FY24 | steady | low |
| Q3 FY24 | blank | n/a |
| Q4 FY24 | steady | low |
| Q1 FY25 | steady | low |
| Q2 FY25 | steady | low |
| Q3 FY25 | accelerating | high |
| Q4 FY25 | blank | n/a |
| Q1 FY26 | blank | n/a |
| Q2 FY26 | steady | low |
| Q3 FY26 | accelerating | high |
| Q4 FY26 | blank | n/a |
| Q1 FY27 | blank | n/a |
| Q2 FY27 | blank (PROVISIONAL) | n/a |

## Data gaps
- Emami never gives its own total rural growth figure. The only own number is general-trade-only rural +7% in Q4 FY24, so rule 2 (compare numbers) never applies.
- Emami posts no pre-results quarterly update, so pending quarters cannot be labelled provisionally.
- Q4 FY25, Q1 FY26, Q4 FY26 and Q1 FY27 have no own rural comment (or only market comment). AGM speeches that mention rural (29 Aug 2025, 25 Aug 2026) come after the results calls and are excluded.
- Q2 FY27: board meeting and call on 5 Nov 2026. The call time was revised to 2:30 PM IST by a letter dated 28 Oct 2026. Re-label after the call.
- Q3 FY26 own rural growth is only "double-digit", based on primary sales. Nielsen offtake data was still pending.
- The volume basis switches between total, core and like-for-like domestic, so the column cannot be read as one series.

## Proposed guide fixes (not in v2)
1. **A channel is not rural.** A statement about general trade (GT) on its own is not a rural statement, because GT includes urban GT. Count it only when management ties it to rural ("our rural GT grew..."). This came up in Q1 FY24.
2. **An analyst's comparative does not count unless management adopts it.** If an analyst's question carries a comparative ("the rural pickup", "incremental pickup") and management confirms only the subject or source ("I am talking about our internal numbers") while using its own non-comparative wording ("signs of recovery"), label from management's words. Treat the analyst's comparative as management's only when management explicitly affirms the direction itself ("Yes... absolutely" to "rural is seeing an incremental pickup"). This came up in Q4 FY24 vs Q3 FY26.
3. **Split sentences.** In "Overall X, but for our business Y", label from the own clause Y only. The un-subjected clause X is market (ambiguous subject). This came up in Q1 FY25.
4. **Volume basis.** Record overall_volume_growth_pct on the company's headline like-for-like or core domestic basis when it is disclosed, otherwise total domestic, and always state the basis in the notes. This came up in Q4 FY25 (7 vs 5) and Q3 FY24 (domestic vs consolidated).
