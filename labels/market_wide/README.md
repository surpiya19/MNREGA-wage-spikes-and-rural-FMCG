# Market-wide rural trend labels (primary target)

Thurro asked for the market-wide rural trend to be the main thing we predict.

- `draft_market_labels_marico_emami.csv`: market labels for Marico and Emami (Q1 FY24 to Q1 FY27). Drafted from the `market_rural_figure` text in `labels/<company>/labels_final.csv`, using guide v2's rules. **Needs a human review.** Edit `market_label`, then run `python run_everything.py`.
- `market_labels_by_company.csv` (generated): one market label per company per quarter. HUL and Dabur labels come from the first pass (3 AI readers, majority).
- `market_wide_labels.csv` (generated): the market-wide label for each quarter, taken as the most common direction across companies. Ties, and an Accelerating vs Slowing split, are Insufficient (no consensus) and are left out of scoring. Only quarters from Q1 FY24 are used. Confidence is high when at least 75% of the companies that commented agree.
