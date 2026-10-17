---
name: linear-ticket
description: Compatibility alias for solve-task. Use only when the user explicitly invokes the legacy linear-ticket skill; use solve-task for normal end-to-end engineering task ownership.
---

# Linear Ticket

Apply the task ownership workflow below with the original request and constraints.

# Solve Task

Own the ticket the way a senior engineer and codeowner would.

- If it doesn't make sense or prescribes a worse solution, edit, close, or supersede it.
- If there's existing work, judge it fresh, since the approach may be wrong or the problem already solved in main or another PR.
- Tickets live in GitHub Issues or Linear, as the repository's instructions imply, and in Issues otherwise. For Linear, use `cagents linear`, which the `cagents` skill covers. If you have instructions but no ticket, make one.
- Work in worktrees; you may already be in the right one.
- Solve it thoroughly and idiomatically and test it, including live testing. Then `commits-push`, and open a PR unless the repository's instructions say otherwise.
