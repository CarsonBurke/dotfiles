---
name: get-merge-ready
description: Get a PR or branch into merge-ready shape a senior would approve.
---

# Get Merge Ready

Bring the PR (or current branch vs its real base) to a senior-approvable state. You may want to use subagents to help with scope partition, design rethink, defect hunting, and final review.

- Infer intent from ticket, PR body, and base…head diff; state scope and exclusions.
- Predict what the optimal implementation of the goal of this PR is. Use that to evaluate its actual changes.
- Partition changes into core, justified adjacent, out-of-scope, and noise.
- For out-of-scope: delete if accidental or low value; extract real follow-up to new worktree(s) (and ticket/issue where reasonable); keep justification concise.
- Rethink the chosen solutions. Land better in-scope approaches when worth the cost; decline the rest with reason.
- Find and idiomatically resolve introduced bugs, regressions, as well as irrational and suboptimal changes.
- if there are merge conflicts, resolve them with rebase.

When invoked directly, you may commit, but do not push unless requested. A composing skill may authorize subsequent push or PR actions.
