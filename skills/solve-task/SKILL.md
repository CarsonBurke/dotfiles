---
name: solve-task
description: Own a concrete engineering task end to end, including tracker setup, re-evaluating existing work, implementation, live testing, review, and context-appropriate delivery. Use when the user asks to solve, finish, or ship a task; not for read-only analysis, planning, status checks, or PR review.
---

# Solve Task

Own the outcome. A ticket, plan, branch, or PR describes the current attempt; none of it makes the approach correct.

## Establish the task

Inspect the repository instructions, worktree, actual base, active task context, and configured trackers before changing code. Resolve two independent policies:

- **Tracker:** Continue an existing or linked ticket without duplicating it. Otherwise follow local tracker instructions; when none exist, default to GitHub Issues for a GitHub repository. Search for a duplicate before creating a concise ticket, assign it to the authenticated user, and link later delivery artifacts.
- **Delivery ceiling:** Determine whether this task ends at commit, push, PR, or merge. Explicit user direction overrides local defaults; otherwise local instructions override the general default of autonomous delivery through merge. Invoking this general workflow does not override a lower local ceiling.

Read an existing ticket with its comments, attachments, linked branches or PRs, CI, reviews, and current implementation. Determine what is already correct, incomplete, stale, or misguided. Turn the requested outcome into acceptance criteria, non-goals, and a reasoned lightweight plan. Keep the plan loose: revise, reorder, replace, or remove steps whenever new evidence changes the best approach.

Ask only when a material product decision cannot be resolved from the request, ticket, repository conventions, or observed behavior.

## Solve the current state

Reproduce defects through the real entrypoint before fixing them. For features, inspect adjacent behavior and every affected contract. Trace the invariant to its durable owner and choose the smallest coherent solution.

Evaluate existing work from first principles rather than merely completing it. Rethink, refactor, or replace the approach when that produces a better result. Address review comments according to their technical merit. Rebase when the branch has diverged and repository policy permits it; preserve unrelated user work and never rewrite ambiguously owned history.

Implement the complete behavior, migrate affected callers, remove obsolete paths, and update tests for changed observable contracts. Keep independent discoveries out of scope unless they are necessary for correctness; record worthwhile follow-ups in the active tracker.

## Test the actual thing

Run focused automated checks, then exercise the affected surface live through the artifact and interface users actually encounter:

- drive web and desktop UI in a real browser or application;
- run and interact with the actual CLI or TUI;
- exercise APIs, workers, integrations, migrations, or packaged builds at their real boundary.

Use available specialized tools, sandboxes, fixtures, or test accounts for critical actions such as deletion, payments, permissions, and external integrations. Do not use production data, real money, or real customer effects as test inputs. A unit test, mock, screenshot, or successful build does not replace live proof of the changed path.

Review the complete base-to-candidate diff. Use self-review when appropriate; obtain human review when repository instructions, branch protection, risk, or ownership require it. Fix valid findings and rerun affected proof.

## Deliver and finish

Continue without pausing at routine delivery boundaries until the resolved ceiling is reached. Use `commits-push` for a coherent task-owned result when publication is authorized. At a PR ceiling, create or update the PR and leave it ready for its required reviewer; at a merge ceiling, continue through CI, actionable feedback, rebasing, required review, and merge. Never exceed the ceiling merely because credentials or tooling permit it, and never bypass required review or protection.

Keep the ticket, branch, PR, CI, and review state linked and current. Resolve the ticket only when its acceptance criteria are satisfied and the authorized delivery is complete; otherwise leave a precise status and next action.

Finish with the outcome, tracker and PR links, commits, automated checks, live scenarios exercised, review state, merge status, and any remaining risk or required human action.
