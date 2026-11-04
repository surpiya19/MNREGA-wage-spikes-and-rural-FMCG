# Reconciliation report: Dabur India own-rural direction pilot (Q1 FY24 to Q2 FY27)

Inputs: `labelling_guide.md`, `labels_A.csv`, `labels_B.csv`. Outputs: `labels_final.csv`, `score_agreement.py`.

## 1. Agreement (13 scored quarters, Q2 FY24 to Q2 FY27)

Output of `python3 score_agreement.py`:

| Metric | Value |
|---|---|
| Percent agreement (4 labels) | 11/13 = 84.6% |
| Cohen's kappa (4 labels) | 0.600 (po 0.846, pe 0.615) |
| Linear-weighted kappa (both directional, n=13) | 0.629 |
| Blank agreement | 0 both-blank, 0 blank disagreements (neither labeller used blank) |
| Distribution A | steady 10, accelerating 2, slowing 1 |
| Distribution B | steady 10, accelerating 1, slowing 2 |

Kappa is held down by the heavy skew toward "steady" (pe = 0.615). Raw agreement is high, but with this skew one extra disagreement would cut kappa sharply.

## 2. Disagreements and close calls

| Quarter | A | B | Final | Reason |
|---|---|---|---|---|
| Q2 FY24 | steady | slowing | **steady** (low) | The only own-rural statement is "we have seen our trajectory also in rural kind of sustaining" (call p.10). "Deficient monsoon impacted rural consumption" has no own subject, so it counts as market. "Rural lags urban" is a level (rule 1), and South India is one region (rule 4). |
| Q1 FY25 | accelerating | steady | **steady** (low) | "For past 3 quarters, we have seen our rural recovery happen" describes a continuing trend. "Sequential recovery in volume growth, driven by rural" is about overall volume, and "volume will increase on back of rural inching up for us" is outlook (rule 5). |
| Q1 FY24 (baseline, close call) | accelerating | accelerating | accelerating (low) | Not scored. Own rural is 8% vs category 4%, but no prior own figure is in scope. |
| Q1 FY26 (close call) | steady | steady | steady (low) | Management calls rural "continued its growth momentum". The return to growth after the Q4 FY25 primary decline could point to accelerating, but there is no own % and no stated change in pace. |
| Q1 FY27 (close call) | steady | steady | steady (low) | The own GT rural lead widened from 300 to 550 bps, but a gap is supporting evidence only (rule 2). The update says rural and urban are "sustaining their growth trend". |

Number conflicts I checked against the source:
- **Q3 FY25 volume**: A had 1.5, B had 1.2. Final is **1.2**. The investor presentation says "1.2% India FMCG Volume growth" (incl. Badshah), and the CFO repeats it in the call Q&A. A's 1.5 has no source I could find.
- **Q2 FY26 volume**: A had 2, B blank. Final is **2**. The investor presentation says "2% India Volume Growth", with India FMCG excluding Badshah (DABURIN_30102025163547_Investorcomm.pdf#page=8).
- **Q4 FY24 link**: A gave #page=18 and B gave #page=17. The "our rural has grown by 8%" quote is on PDF page 18 (printed p.17), so A's link is correct.
- **Q3 FY25 link**: B's filename `DABUR_04022025...` does not match the file I retrieved. The final uses the retrieved `DABURIN_04022025185044_Transcript.pdf#page=18`.

## 3. Final labels

| Quarter | Final | Conf |
|---|---|---|
| Q1 FY24 | accelerating (baseline) | low |
| Q2 FY24 | steady | low |
| Q3 FY24 | accelerating | high |
| Q4 FY24 | steady | high |
| Q1 FY25 | steady | low |
| Q2 FY25 | steady | low |
| Q3 FY25 | steady | low |
| Q4 FY25 | slowing | low |
| Q1 FY26 | steady | low |
| Q2 FY26 | steady | high |
| Q3 FY26 | steady | high |
| Q4 FY26 | steady | low |
| Q1 FY27 | steady | low |
| Q2 FY27 | steady (provisional) | low |

How "medium" was converted: a label became high when it rests on company-stated numbers (Q4 FY24) or on explicit own direction words: "bounce back for Dabur" (Q3 FY24), "sustaining growth for the company" (Q2 FY26), "continues its consistent performance" (Q3 FY26). Every other medium became low.

## 4. Guide fixes (one line each)

1. **Unattributed rural statements** (cause of Q2 FY24, and the source of A's Q1 FY25 "picking up"): "A rural statement with no 'we/our/for us/Dabur' subject (opening macro remarks, quarterly-update demand paragraph) is market, even when the speaker is the CEO."
2. **Overall volume/business attributed to rural** (cause of Q1 FY25): "'Our volume/growth improved, driven by rural' is not a statement about rural's own pace; label it from what is said about rural itself."
3. **Recovery or continuation wording** (cause of Q1 FY25 and the Q1 FY24/Q1 FY26 close calls): "'Recovery happening', 'continued momentum', 'sustaining' and 'resilient' = steady; accelerating needs a comparative ('faster', 'higher than last quarter', 'picked up')."
4. **Regional comments** (rule 4 detail for Q2 FY24): "A region lagging (e.g. South) does not override a whole-business statement; use it only as notes."
5. **Gap-only quarters** (Q1 FY27): "If the only own evidence is a change in the rural–urban gap, label steady/low unless management states rural's own pace changed; record the gap in notes."
6. **Confidence scale**: "Only high or low; high requires own numbers for both quarters or an explicit own direction word" (both labellers used "medium").
7. **Links**: "evidence_link must be the PDF page index from the retrieve result, not the printed page number, and the filename must be copied exactly."
8. **Pending quarters**: "If the results call or press release has not happened yet, label from the pre-results update, set confidence low and mark PROVISIONAL with the scheduled date in results_date."

## 5. Data gaps

- **Q2 FY27**: only the 6 Oct 2026 pre-results update exists. The analyst meet is scheduled for 5 Nov 2026, and there is no transcript, results press release or volume figure yet, so the label must be redone after results.
- **Pre-results update bodies not retrieved** (B saw only the cover letters): Q2 FY24 (6 Oct 2023), Q2 FY25 (1 Oct 2024), Q3 FY25 (3 Jan 2025), Q4 FY25 (2 Apr 2025).
- **Overall volume missing** for the quarter: Q4 FY24 (only FY24 at 5.5% incl. Badshah), Q2 FY25 (none disclosed because of the GT inventory correction; secondary sales +2.3%), Q4 FY25, Q2 FY27.
- **Volume basis is inconsistent**: some quarters include Badshah (Q2 FY24 at 3% organic vs 5.8% incl.; Q3 FY24 6% incl.; Q3 FY25 1.2% incl.), while Q2 FY26 excludes it. Treat the series as not strictly comparable.
- **Own rural % given in only 5 quarters**: Q1 FY24 8, Q3 FY24 6-6.5, Q4 FY24 8, Q3 FY25 2, Q2 FY26 ~7 (GT rural). In the other quarters rule 2 cannot be applied.
- **Corpus period tags are off by one quarter**: the Q1 FY27 call (29 Jul 2026) is tagged Q4 FY26, and several transcripts are filed days after the call date.
