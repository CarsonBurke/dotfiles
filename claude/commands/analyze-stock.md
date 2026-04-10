---
name: analyze-stock
description: Analyze a stock using IBKR MCP news, price data, and contract info.
---

Analyze the given stock ticker over the specified timeframe (default: last month). If the ibkr MCP server is not reachable, start it with `ibkr-mcp`.

## Data gathering

1. Use ibkr MCP tools for news headlines, historical price bars, contract details, and current position.
2. If IBKR news is thin or stale, supplement with web search for recent news, analyst coverage, and controversy.

## Analysis

Present a concise analysis covering:

- **Price action** — trend, support/resistance, notable moves
- **Sentiment** — overall market sentiment from news and analyst tone (bullish/bearish/mixed), with evidence
- **Controversy & risk** — lawsuits, regulatory issues, executive departures, short seller reports, accounting concerns, or other red flags discovered via news
- **Key events** — earnings, product launches, analyst upgrades/downgrades, insider activity
- **Bull/bear case** — concise arguments for each side
- **Current exposure** — position size and P&L if held

$ARGUMENTS
