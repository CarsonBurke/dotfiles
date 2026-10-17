---
name: get-merge-ready
description: Get a PR or branch into merge-ready shape a senior would approve.
---

# Get Merge Ready

Bring the PR, or the current branch against its real base, to where a senior reviewer would approve it. Subagents help with partitioning scope, rethinking the design, hunting defects, and the final review.

- Infer intent from the ticket, the PR body, and the diff, and state the scope and exclusions.
- Picture the best implementation of that intent and judge the actual changes against it, which shows both what's missing and what doesn't belong.
- Changes outside the scope either go, when accidental or low value, or move to their own worktree, with a ticket when they're worth tracking.
- Land a better in-scope approach when it's worth the cost, and say why you declined the others.
- Find and fix the bugs and regressions the PR introduces, and changes that are irrational or suboptimal.
- Resolve merge conflicts by rebasing.

When invoked directly, you may commit, but don't push unless asked. A wrapping skill may add pushing or a PR.
