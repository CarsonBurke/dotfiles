---
name: debug-frontend
description: Diagnose frontend UI or browser behavior without changing source files. Use fix-frontend when a fix is requested.
---

# Debug Frontend

- Diagnose only: do not edit tracked files or update snapshots/fixtures.
- Use `browser-harness` to reproduce the issue in a dedicated work window. Keep production read-only and preserve unrelated browser state.
- Capture the exact steps, viewport, role/state, visible failure, console/network evidence, and relevant URL/data changes. Inspect code and focused checks to separate the likely cause from alternatives.
- Cover adjacent states only when they can change the diagnosis.
- Report the reproduction, evidence, probable code area/cause, ruled-out hypotheses, and unverified gaps.
