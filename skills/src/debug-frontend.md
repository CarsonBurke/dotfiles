---
name: debug-frontend
description: Diagnose frontend UI and browser behavior through reproduction, browser evidence, code inspection, and focused checks without changing source files.
---

# Debug Frontend

- Diagnose only, without editing tracked files or updating snapshots or fixtures.
- Reproduce the issue through the `browser` skill in a dedicated window, keeping production read-only and leaving the user's other browser state alone.
- Record the steps, viewport, role or state, the visible failure, and the console, network, and URL or data evidence that goes with it.
- Read the code and run focused checks to separate the likely cause from the alternatives. Look at adjacent states only when they could change the diagnosis.
- Report the reproduction, the probable cause and where it lives, what you ruled out, and what you couldn't verify.
