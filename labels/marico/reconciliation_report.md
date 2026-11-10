# Marico Limited: reconciliation report (rural direction, Q1 FY24 to Q2 FY27)

Guide: `labels/labelling_guide.md` (v2). Inputs: `labels_A.csv`, `labels_B.csv`. Output: `labels_final.csv`.
Scoring: `python3 labels/marico/score_agreement.py labels/marico/labels_A.csv labels/marico/labels_B.csv`

## 1. Agreement (13 scored quarters, Q2 FY24 to Q2 FY27)

| Metric | Value |
|---|---|
| Percent agreement (4 labels incl. blank) | 10/13 = 76.9% |
| Cohen's kappa (4 labels) | 0.204 (po 0.769, pe 0.710) |
| Linear-weighted kappa (both gave a direction) | 0.000, n = 1. A single pair is too few to interpret |
| Blank agreement | both blank 10; either blank 12; blank-vs-direction disagreements 2 |
| Baseline Q1 FY24 (not scored) | A blank, B steady |

Label distribution: A has 12 blank and 1 slowing. B has 10 blank, 2 steady and 1 accelerating.
Raw agreement is high only because most quarters are blank. Kappa is low because the labellers never agreed on a direction.

## 2. Disagreements and resolution

| Quarter | A | B | Final | Conf. | Reason |
|---|---|---|---|---|---|
| Q2 FY24 | slowing | steady | **steady** | high | The analyst first asked about *Marico's* low-single-digit GT decline, then asked "is GT growth worse off in rural India versus the last quarter?" The CEO answered "No, not really... similar kind of a level. If you look at our volumes, they are broadly similar." That is an own no-change answer to a question that compares with last quarter. "We had a very bad August" (p.10) answers a question on "rural economy and rural pickup from the FMCG perspective". It repeats the prepared-remarks sentiment paragraph ("noticeable drop in overall sentiment, especially in rural"), so it is market. |
| Q4 FY24 | blank | accelerating | **blank** | n/a | The analyst asked for Marico's rural vs urban "take" for FY25. The answer "We are definitely seeing some rural uptick... while urban has moderated" uses "we" as an observer of rural/urban demand. It cites no own metric and repeats the info update's sector line ("we did witness an uptick in rural sentiment towards the end of the quarter"). The rest of the answer is outlook. The alternative label is accelerating/low. |
| Q3 FY25 | blank | steady | **steady** | low | The analyst asked whether rural was 2x urban "in this category for you" (Parachute). The CEO replied: "for the FMCG sector, specifically for us it's been more or less in line." This is an explicit own statement, but it is a level (rural roughly equal to urban) with no change in pace (rule 1). Confidence is low because the question was brand-scoped. |
| Q1 FY24 (baseline) | blank | steady | **blank** | n/a | "Muted rural sentiment" is given only as a cause of weak core volumes. It is a sentiment remark, not a statement about own rural pace. |

Agreed rows re-checked:
- **Q1 FY25:** "signs in the rural to etch up" comes in a VAHO bottom-of-pyramid answer that ends "the category will show higher growth". That is category and outlook, so the agreed blank stands.

**Final 14 labels:**
- **Q1 FY24 to Q4 FY27 overall:** 2 steady and 12 blank.
- **Steady:** Q2 FY24 (high) and Q3 FY25 (low).
- **Blank:** Q1 FY24, Q3 FY24, Q4 FY24, Q1 FY25, Q2 FY25, Q4 FY25, Q1 FY26, Q2 FY26, Q3 FY26, Q4 FY26, Q1 FY27 and Q2 FY27.

Against the final labels, A matches 11/13 scored quarters and B matches 12/13.

## 3. Data gaps

- **Own rural growth is no longer reported.** Through about FY21–FY22, Marico's Information Updates had a "Markets/Distribution Channels" section giving its own urban and rural GT growth. Examples: Q4 FY21 "urban and rural growing by 23% and 42% in volume terms"; Q3 FY21 "urban and rural markets up by 10% and 24%"; Q2 FY22 "rural outpaces urban". None of the 14 study quarters keeps that split. The FY24–FY27 updates give only channel growth (GT / MT / e-com, e.g. Q2 FY24 "General Trade declined in low single digits"). Their rural lines are Nielsen sector slides or demand paragraphs. So `own_rural_growth_pct` is empty for every quarter, and rule 2 (numbers beat adjectives) can never apply to Marico.
- **Q2 FY27 is labelled without the call.** Results came out on 2 Nov 2026, but the call transcript is not yet in the corpus, so the label rests on the pre-update and the information update only. Re-check it once the transcript is filed.
- **Period tags are off by one quarter.** Several pre-updates are tagged one quarter late in the corpus (Q2 FY25, Q3 FY25, Q4 FY25 pre-updates). The labellers handled this correctly.
- **Later documents were excluded.** The 25 Aug 2026 AGM (Q1 FY27) and the FY26 annual report come after the relevant calls, so they were not used.

## 4. Proposed guide fixes (not in v2)

1. **Observer-"we" in Q&A.** "We are seeing / we witnessed / we had" followed by a market noun (rural, demand, sentiment, consumption) counts as market commentary unless one of these holds:
   - (a) the same or the next sentence ties it to an own metric: "our volumes", "our GT", "our rural sales", or a named Marico brand or channel; or
   - (b) the speaker explicitly contrasts the sector with the company ("for the sector... for us").

   An analyst asking "for Marico" is not enough by itself. If the wording restates that quarter's sector or demand paragraph in the info update, it is market.
2. **Read the question thread, not just the sentence.** If the question that follows up (or the question itself) is about the company's own channel (e.g. "our GT decline") and asks for a comparison with last quarter, treat a "no / similar / no movement" answer as an explicit own direction (steady). It qualifies for high confidence.
3. **Own rural statement in a brand-scoped answer.** If the only own rural statement comes in an answer to a single-brand question, still label it (do not leave it blank), with confidence low. Rule 4 decides between conflicting statements; it does not turn brand-scoped own evidence into blank.
4. **Scoring note.** If fewer than 2 rows have a direction from both labellers, report the weighted kappa as not interpretable (the script now prints this).
