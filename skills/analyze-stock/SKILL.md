---
name: analyze-stock
description: Analyze a public stock using IBKR data, current sources, valuation context, and portfolio exposure.
---

# Analyze Stock

- Pin down the exact instrument first: ticker, exchange, currency, security type, and IBKR contract, telling apart share classes, ADRs, and dual listings.
- Timestamp the analysis and its data cutoff, say whether quotes are live, delayed, or prior close, and compare performance with a relevant market or sector benchmark.
- Use IBKR for the contract, quotes, bars, news, and any position context the user asks for. For fundamentals and events, prefer regulatory filings and investor-relations material, using the `browser` skill for current research and citing dated sources.
- Keep reported facts, consensus or management forecasts, and your own inference visibly apart, and flag data that is stale, conflicting, missing, or in mismatched currencies.
- Cover price and volume behavior, financial quality, leverage and dilution, valuation, catalysts, controversy, the bull and bear cases, risks, and what evidence would invalidate them, without false precision.
- Positions, cost basis, orders, and account identifiers are private. Include only the exposure context requested, and never account identifiers or unrelated holdings.
- End with the cutoff, the material uncertainty, and sources for time-sensitive claims.
