---
name: steward-pr
description: Own a pull request through bug review, fixes, pushes, rebases, CI.
---

# Steward PR

Own the PR up to merge readiness, which includes fixing, committing, pushing, and updating it. When invoked directly, stop at merge readiness; a wrapping skill may add the merge.

- Work in an existing suitable worktree or a new one in a local gitignored `.worktrees/`.
- If main or another PR solves the problem better, refactor, split, or close this one, and make sure the result integrates.
- Surface what needs a human without letting it block the rest.

<!-- include: get-merge-ready -->

## Publish and follow through

Once the changes are ready, commit, push, and update the PR as below. Then follow CI and review comments, fix real failures and substantive feedback, and rerun what the fixes affect. Stop polling after 30 minutes and report what's still pending.

<!-- include: commits-push-pr -->
