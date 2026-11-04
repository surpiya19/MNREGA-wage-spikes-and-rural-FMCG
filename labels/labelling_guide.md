# Rural Commentary Labelling Guide (v2)

## Task
For each quarter, assign ONE label describing whether the company's management says its OWN rural business is accelerating, steady or slowing versus the PREVIOUS quarter.

- Company: given in your instructions (use its exact Thurro corpus name).
- Quarters: Q1 FY24 (Apr–Jun 2023) through Q2 FY27 (Jul–Sep 2026) = 14 quarters. Q1 FY24 is labelled as the baseline; Q2 FY24 onward (13 quarters) are scored.
- Indian fiscal year: Q1 = Apr–Jun, Q2 = Jul–Sep, Q3 = Oct–Dec, Q4 = Jan–Mar. FY24 Q1 = Apr–Jun 2023.
- Results calls usually happen 4–6 weeks after quarter end (e.g. Q1 FY27 call on 29 July 2026; Q4 FY24 call on 2 May 2024).

## Sources (only what was public by that quarter's results call)
1. Earnings-call transcript (primary): prepared remarks + Q&A. Look for "rural", "villages", "general trade"/"GT", "hinterland", "Bharat".
2. Pre-results quarterly business update (Dabur and Marico post one a few days after quarter end; HUL and Emami usually don't) — counts for the same quarter.
3. Results press release / investor presentation / quarterly information update — use for overall India FMCG volume growth and any rural line in the CEO quote.
Do NOT use later documents (annual report, next quarter's call) to fill in a quarter.

Search the Thurro filings corpus with the `mcp__ThurroAltDataReports__retrieve` tool (load it first with ToolSearch "select:mcp__ThurroAltDataReports__retrieve"). Use mode "focused", companies [<the company's corpus name>], domains ["company"], and the `period` parameter (e.g. "Q1 FY27") to clamp to one quarter. Note: the corpus's period tags are sometimes off by one quarter relative to the document date (e.g. a call held in May 2024 about Jan–Mar 2024 may be tagged Q4 FY24 or Q1 FY25) — always check the document's own date/quarter-ended text and assign it to the quarter it DISCUSSES.

## Labels
| Label | Use when management says or clearly implies… |
|---|---|
| accelerating | its own rural growth is higher / improving / picking up vs last quarter |
| steady | its own rural growth similar to last quarter, or continuing trend with no stated change in pace |
| slowing | its own rural growth lower / moderating / under pressure vs last quarter |
| blank | no comment on its own rural business in any source for that quarter |

Decision rules:
1. A level is not a direction. "Rural outpaces urban" with no change in pace = steady.
2. Numbers beat adjectives. If own rural growth is given for this and last quarter, compare; a change of ≤2 percentage points = steady. (A rural–urban gap in bps is NOT rural growth itself; use it only as supporting evidence.)
3. A narrowing rural–urban gap is slowing only if management says rural itself moderated. If urban improved and rural held, steady.
4. Mixed messages: label what CEO/CFO says about the whole rural business, not one brand or region.
5. Outlook does not count. Label only what happened in the quarter.
6. Unsure between two labels: pick one, set confidence low, explain in notes. Never leave blank because it is hard.
7. "Recovery happening", "continued momentum", "sustaining", "resilient" = steady. Accelerating needs a comparative about rural itself ("faster", "higher than last quarter", "picked up").
8. "Our volume/growth improved, driven by rural" is about overall growth, not rural's own pace; label from what is said about rural itself.
9. If the only own evidence is a change in the rural–urban gap, label steady with low confidence unless management says rural's own pace changed; record the gap in notes.
10. A lagging region (e.g. South India) does not override a statement about the whole business; put it in notes.

## Confidence
Only two values: high or low. High requires the company's own rural numbers for both quarters, or an explicit direction word about its own rural business. Everything else is low.

## Company vs market
- Company data: "our rural grew 8%", "for us rural is 550 bps ahead of urban", "our rural GT grew...".
- Market data: anything citing Nielsen, NIQ, "the category", "FMCG market", "industry" → record in market columns only.
- Ambiguous subject → treat as market, confidence low.
- A rural statement with no "we/our/for us/<company>" subject (opening macro remarks, the demand paragraph of a quarterly update) is market commentary, even when the CEO says it.
- If only market commentary exists for a quarter, company_label = blank, market columns filled. Never copy market direction into company label.

## Output: CSV with exactly these columns
company,quarter,labeller,company_label,confidence,evidence_quote,evidence_link,own_rural_growth_pct,overall_volume_growth_pct,market_rural_figure,market_source,notes,results_date

- evidence_quote: key sentence, under 30 words, from the company's own commentary (paraphrase is fine if you can't get exact words; mark "[paraphrase]").
- evidence_link: link (with #page=) copied exactly from the retrieve result — use the PDF page index in the link, not the printed page number, and copy the filename exactly.
- Pending quarters: if results haven't been announced yet, label from the pre-results update, set confidence low, start notes with "PROVISIONAL" and put the scheduled results date in results_date.
- Quote CSV fields containing commas with double quotes.
