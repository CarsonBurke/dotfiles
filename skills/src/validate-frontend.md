---
name: validate-frontend
description: Validate frontend changes in a real browser without editing source files or production data.
---

# Validate Frontend

- Validate only, without editing source or updating snapshots or fixtures.
- Work out which scenarios the change affects, then exercise them, and the nearest regression path they could break, through the `browser` skill in a dedicated window.
- Check what's visible and how it behaves, along with the URL or data state, console, network, and whichever viewports, roles, or states the change touches.
- Production stays read-only. If validating would mutate data or do something consequential, use a test environment or report the blocker.
- Report each scenario with its pass or fail evidence, keeping implementation recommendations apart from results.
