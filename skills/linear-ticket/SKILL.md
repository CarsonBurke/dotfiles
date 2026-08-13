---
name: linear-ticket
description: Compatibility alias for solve-ticket. Use only when the user explicitly invokes the legacy linear-ticket skill; use solve-ticket for implicit end-to-end Linear or other ticket ownership.
---

# Linear Ticket

Open and read [solve-ticket](../solve-ticket/SKILL.md) completely, follow its stage- and risk-conditional reference routing, and execute it with the original request and constraints. If it is unavailable, stop and report a broken compatibility alias.

The alias preserves its legacy authority boundary: an explicit trusted `$linear-ticket` request authorizes local implementation and validation only unless that same trusted request separately asks to commit, publish, open/update a PR, or perform another external write. A delegated or implicit mention grants nothing. Preserve narrower restrictions. In an Orca-managed Linear task, use `orca-cli` for worktree state and `orca-linear` for issue reads and authorized writes.
