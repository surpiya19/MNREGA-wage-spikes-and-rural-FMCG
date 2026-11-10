# Rural commentary labels: results (Q1 FY24–Q1 FY27)

Each company was labelled by two independent agent labellers using guide v2. A third agent then reconciled each company's two sets against the sources.

**Window (updated 9 Nov 2026).** Agreement is now scored on the same 13 quarters the backtest uses: Q1 FY24 to Q1 FY27. Earlier versions scored Q2 FY24 to Q2 FY27. Q2 FY27 is left out because the analysis stops at Q1 FY27 (Thurro: "Q1FY27 is fine"), and because Dabur's and Emami's Q2 FY27 calls were not out when it was first labelled. The FY23 quarters for HUL and Dabur come from the first pass (3 AI readers, majority, no reconciliation) and are left out of the scoring and the backtest.

## Agreement (13 scored quarters per company, Q1 FY24–Q1 FY27)
| Company | Agreement | Cohen's kappa | Final labels |
|---|---|---|---|
| Dabur | 11/13 (84.6%) | 0.68 | 10 steady, 2 accelerating, 1 slowing |
| HUL | 12/13 (92.3%) | 0.72 | 11 blank, 2 steady |
| Marico | 9/13 (69.2%) | 0.15 | 11 blank, 2 steady |
| Emami | 9/13 (69.2%) | 0.54 | 6 blank, 5 steady, 2 accelerating |
| Pooled (52) | 41/52 (78.8%) | 0.66 | — |

Notes:
- Marico's kappa is low despite 69% agreement because both labellers mostly chose blank. On the few quarters with a direction, they barely agreed beyond chance.
- The pooled kappa is higher than three of the four company figures because pooling mixes companies with different label patterns. Don't quote it as overall reliability.

## Key finding
HUL and Marico almost never describe their own rural business: in 11 of 13 quarters every rural remark is Nielsen or sector commentary. Dabur's own rural label is mostly steady (10 of 13), with direction changes in three quarters (accelerating in Q1 FY24 and Q3 FY24, slowing in Q4 FY25). Emami's label changes between steady and accelerating but is blank in 6 of 13 quarters. Labels about the companies' own rural business are therefore too sparse and flat to be the main backtest target on their own.

## Backtest status (re-run 9 Nov 2026; outputs/summary_all_targets.txt)
- Own-rural targets for HUL, Marico and Emami can't be tested: they have too few labelled quarters to train a rule (at least 6) and still test on 2.
- In the six targets that could be tested, the selected MGNREGA rule never beat the best baseline on the held-out quarters.
- The fitted rules disagree on what more MGNREGA work means: 4 read it as distress, 2 as stronger demand.
- Market-wide labels: a tied company vote is now treated as no consensus and left out of scoring. It used to count as Steady. Only Q1 FY24 is a tie, but the market-wide label is Steady for every quarter from Q2 FY25, so "same as last quarter" is hard to beat.

## Open items
- Q2 FY27 transcripts are now filed for all four companies (HUL 28 Oct, Marico 2 Nov, Dabur and Emami 5 Nov). Re-label Q2 FY27 from them before extending the window.
- Market labels for HUL and Dabur are still first-pass for every quarter. Re-label them with two labellers and a reconciler, as was done for the own-rural labels.
- Add the reconcilers' new rule fixes to the guide (v3): ambiguous "we" in Q&A, data-source possessives, multi-quarter comparisons, GT is not rural, analyst wording needs management agreement, split sentences, volume basis.
- The per-company `score_agreement.py` scripts still score the old window (Q2 FY24–Q2 FY27). The figures above come from the pipeline (03_labels.py) and were checked independently.
