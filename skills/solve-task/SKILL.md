---
name: solve-task
description: Solve, verify, review, and deliver a concrete engineering task. Use when asked to solve, finish, or ship a task; not for planning, status checks, or read-only review.
---

# Solve Task

- Own the result. Re-evaluate the ticket, branch, and PR; the current approach may be wrong.
- Before editing:
  - Read repository instructions, the linked task and comments, current changes, reviews, and CI.
  - Identify every repository and worktree needed.
  - Work only there; move this agent's work if it is elsewhere. For each repository without a relevant worktree, create a non-child, task-named one based on main/default. Use `--worktree no-child --name <task-name> --base-branch <main-or-default>` where supported.
  - Do not start a base agent in a new worktree unless it will take over the complete task.
  - Use `orca-cli` for Orca worktrees and `orca-linear` for Linear tasks.
  - Choose the delivery target from the user's request, then repository rules. Default to verified local changes; remote mutations require authorization.
- Reuse the linked tracker item. Create one only when required and authorized, after checking for duplicates.
- Define acceptance criteria and non-goals. Ask only about an unresolved product decision.
- Reproduce bugs through the real entrypoint. For features, inspect existing behavior and affected contracts.
- Re-evaluate existing work. Fix the source, complete the behavior, migrate callers, remove obsolete paths, and update affected tests and docs.
- Preserve unrelated changes and history.
- Run focused checks and exercise the changed UI, CLI, API, worker, migration, or package at its real boundary. For bugs, repeat the original reproduction.
- Use sandboxes or test accounts for destructive, financial, permissioned, or external verification; never affect production or customers.
- Review the full base-to-candidate diff. For non-trivial changes, get an independent review; fix findings and rerun affected proof.
- Continue to the authorized delivery target. Update or close trackers, PRs, reviews, and CI only within that authorization.
- Return point-form evidence only: outcome, links, checks, live proof, delivery state, and remaining risks.
