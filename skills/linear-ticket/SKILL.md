---
name: linear-ticket
description: Compatibility alias for solve-task. Use only when the user explicitly invokes the legacy linear-ticket skill; use solve-task for normal end-to-end engineering task ownership.
---

# Linear Ticket

Use [solve-task](../solve-task/SKILL.md) with the original request and constraints. If it is unavailable, stop and report a broken compatibility alias.

In an Orca-managed Linear task, use `orca-cli` for worktree state and `orca-linear` for issue reads and authorized writes. Otherwise follow the tracker and delivery workflow selected by `solve-task`.
