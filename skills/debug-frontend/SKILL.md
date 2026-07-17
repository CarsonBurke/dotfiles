---
name: debug-frontend
description: Diagnose frontend UI and browser behavior through reproduction, browser evidence, code inspection, and focused checks without changing source files.
---

# Debug Frontend

- Diagnose only: do not edit tracked files or update snapshots/fixtures.
- Use the `browser` skill to reproduce the issue in a dedicated work window. Keep production read-only and preserve unrelated browser state.
- Capture the exact steps, viewport, role/state, visible failure, console/network evidence, and relevant URL/data changes. Inspect code and focused checks to separate the likely cause from alternatives.
- Cover adjacent states only when they can change the diagnosis.
- Report the reproduction, evidence, probable code area/cause, ruled-out hypotheses, and unverified gaps.
