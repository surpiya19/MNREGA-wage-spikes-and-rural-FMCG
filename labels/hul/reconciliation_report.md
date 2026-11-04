# HUL (Hindustan Unilever Limited) — reconciliation report

Guide: `labelling_guide.md` v2. Inputs: `labels_A.csv`, `labels_B.csv`. Output: `labels_final.csv`.
Scored with `hul/score_agreement.py hul/labels_A.csv hul/labels_B.csv` (13 scored quarters, Q2 FY24 – Q2 FY27; Q1 FY24 is the baseline).

## Agreement (pre-reconciliation)

| Metric | Value |
|---|---|
| Percent agreement (4 labels incl. blank) | 12/13 = 92.3% |
| Cohen's kappa (4 labels) | 0.717 (po 0.923, pe 0.728) |
| Linear-weighted kappa, both directional | 0.000, n = 2 (degenerate: B gave "steady" both times, so there is no variance on B's side. Do not read it as a meaningful figure.) |
| Blank agreement | both blank 11; either blank 11; blank disagreements 0 |
| Baseline Q1 FY24 | both blank |

Distributions: A = 11 blank, 1 steady, 1 accelerating; B = 11 blank, 2 steady.

## Disagreements

| Quarter | A | B | Final | Conf. | Reason |
|---|---|---|---|---|---|
| Q1 FY27 | accelerating | steady | steady | low | The analyst asked how rural did "this quarter". The CEO answered "rural and urban growth for us... continue to be strong" (rule 7 = steady). "In the last few quarters, we have seen a step-up in our rural growth" compares across several quarters and is not tied to Q4 FY26, which had said rural ≈ urban. |

There were no number disagreements. UVG matched in all 14 quarters, and own_rural_growth_pct was blank everywhere because HUL never gave an own rural growth figure. The only differences between the files were in evidence links and market-column text: Q4 FY25 (p18 vs p3), Q1 FY26 (p33 vs p4), Q4 FY26 (NSE vs BSE copy), Q2 FY27 (p2 vs p18), and Q1 FY27 market column (A filled, B empty). The final file uses the link I checked against a retrieve result.

## Source re-checks
- **Q4 FY26** (non-blank): the quote is confirmed on the BSE copy at p20 (`55988411-…pdf#page=20`). It is a direct reply to "have you seen rural demand for you still faster than urban?". It is a level statement, so steady, and low confidence.
- **Q1 FY27** (non-blank, disagreement): the quote is confirmed on the NSE transcript at p14. CFO p5: GT distribution grew, "led out of small towns and rural".
- **Q1 FY26** (blank spot-check): the CFO's line "basis Nielsen data and our own internal read we have seen an uptick in rural" (p33) answers a question about *industry* trends. He goes straight on to urban plus e-commerce market data and "uptick in the latest quarter market numbers" (p34). "Our own internal read" names HUL's data source, not its rural business, so this is **market** and the quarter stays blank.
- **Q3 FY25** (blank spot-check): "rural is stronger" (p23) refers to the consumer base. "Go where the growth is… parts of rural" (p32) is strategy. All statements about rural pace are market data (Nielsen MAT). Blank confirmed.
- **Q4 FY25** (extra check): "resilient growth in rural where we have a higher market share" (p18) is market growth plus HUL's share level, said inside an outlook remark. Blank confirmed.

## Data gaps
1. **Q1 FY25**: in the corpus, the JQ'24 earnings-call transcript (filed 29-Jul-2024) returns only its cover letter (I re-checked). This label comes from the presentation and press release alone.
2. **Q2 FY27**: the SQ'26 call transcript (call held 28-Oct-2026) is not in the corpus yet. Only the audio/video notice is there. Results are out, so the label is not provisional. Re-label once the transcript is filed.
3. HUL never gives an own rural growth %. As a result, high confidence is almost impossible under the guide's confidence rule, and every directional label here is low.

## Proposed guide fixes (not already in v2)
1. **Subject inherited from the question.** If an analyst asks explicitly about the company's own business ("for you", "your rural"), and management answers without moving to the market, the answer counts as company commentary. If management does move to the market, it counts as market. (Q4 FY26)
2. **A data-source possessive is not an own subject.** "Our internal read / our data / our tracking shows rural picked up" describes the source of the evidence. It counts as own only if the thing measured is the company's own sales. (Q1 FY26)
3. **Comparison window.** A comparison over several quarters or a year ("step-up over the last few quarters", "vs last year") does not make a quarter *accelerating*. Label from what is said about the current quarter versus the previous one. If the only comparison covers a longer window, use low confidence and record it in the notes. (Q1 FY27)
4. **Confidence on blank rows.** Blank rows take confidence "n/a". Labeller A wrote "low" and labeller B left the field empty. Add this to the Output section.
