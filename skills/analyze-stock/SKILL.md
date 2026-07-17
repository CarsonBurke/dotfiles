---
name: analyze-stock
description: Analyze a public stock using IBKR data, current sources, valuation context, and portfolio exposure.
---

# Analyze Stock

- Resolve the exact instrument: company, ticker, exchange, currency, security type, and IBKR contract. Disambiguate share classes, ADRs, and dual listings.
- Timestamp the analysis and data cutoff. Distinguish live, delayed, and prior-close quotes; compare performance with a relevant market or sector benchmark.
- Use IBKR for contract, quote, bars, news, and requested position context. Prefer regulator filings and company investor-relations material for fundamentals/events; use the `browser` skill for current research when needed and cite dated sources.
- Separate reported facts, consensus/management forecasts, and inference. Flag stale, conflicting, missing, or currency-incompatible data.
- Cover material price/volume behavior, financial quality, leverage/dilution, valuation, catalysts, controversy, bull/bear cases, risks, and invalidating evidence without false precision.
- Treat positions, cost basis, orders, and account identifiers as private. Include only requested exposure context, never account identifiers or unrelated holdings.
- End with the cutoff, material uncertainty, and sources for time-sensitive claims.
