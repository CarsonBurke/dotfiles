---
name: fix-frontend
description: Fix frontend UI or browser behavior, including reproduction, implementation, tests, and browser validation.
---

# Fix Frontend

- Reproduce with the `browser` skill in a dedicated work window before editing when feasible; preserve unrelated browser state.
- Trace the cause, make the smallest idiomatic fix, add proportionate regression coverage, and run relevant checks.
- Reload or restart and validate the corrected state plus the nearest plausible regression path. Check affected roles, states, viewports, console, and requests only as relevant to the change.
- Keep production read-only. Confirm before any send, purchase, deletion, permission, or account mutation needed for validation.
- Report the cause, change, tests, browser evidence, and remaining gaps.
