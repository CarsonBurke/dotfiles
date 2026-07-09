---
name: debug-frontend
description: Reproduce and diagnose frontend UI, runtime, and browser behavior without editing source files. Use when the user asks to investigate or explain a frontend problem; use fix-frontend when implementation is requested.
---

# Debug Frontend

- Diagnose only: do not edit tracked files or update snapshots/fixtures.
- Use `browser-harness` to reproduce the issue in a new tab. Keep production read-only and preserve unrelated tabs and state.
- Capture the exact steps, viewport, role/state, visible failure, console/network evidence, and relevant URL/data changes. Inspect code and focused checks to separate the likely cause from alternatives.
- Cover adjacent states only when they can change the diagnosis.
- Report the reproduction, evidence, probable code area/cause, ruled-out hypotheses, and unverified gaps.
