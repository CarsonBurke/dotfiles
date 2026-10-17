---
name: fix-frontend
description: Fix browser-based UI or UX, including reproduction, implementation, tests, and browser validation.
---

# Fix Frontend

- Reproduce through the `browser` skill in a dedicated window before editing when you can, leaving the user's other browser state alone.
- Trace the cause, fix it idiomatically at the cause, no broader than it needs to be, add regression coverage in proportion to it, and run the relevant checks.
- Reload or restart and confirm the fixed state and the nearest path the fix could break, checking roles, viewports, console, and requests as far as the change touches them.
- Production stays read-only, and anything that sends, purchases, deletes, or changes permissions or accounts needs confirmation first, even for validation.
- Report the cause, the change, tests, browser evidence, and remaining gaps.
