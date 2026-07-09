---
name: fix-frontend
description: Reproduce, implement, test, and browser-validate fixes for frontend UI and behavior. Use when the user asks to repair an observed frontend problem.
---

# Fix Frontend

- Reproduce with `browser-harness` before editing when feasible; open a new tab and preserve unrelated browser state.
- Trace the cause, make the smallest idiomatic fix, add proportionate regression coverage, and run relevant checks.
- Reload or restart and validate the corrected state plus the nearest plausible regression path. Check affected roles, states, viewports, console, and requests only as relevant to the change.
- Keep production read-only. Confirm before any send, purchase, deletion, permission, or account mutation needed for validation.
- Report the cause, change, tests, browser evidence, and remaining gaps.
