---
name: maintain-prs
description: Audit open GitHub pull requests for staleness, base divergence, and unresolved review feedback, then perform requested maintenance safely.
---

# Maintain PRs

Audit before acting:

- Read PR metadata, checks, reviews, comments, unresolved threads, linked issues, head ownership, permissions, and actual base divergence.
- Verify obsolescence from current behavior; a closed issue, old age, or changed file is only a signal. Never close a linked issue as a side effect.
- Report each PR's evidence and proposed action before destructive maintenance. Confirm the exact PRs before closing, rebasing, or force-pushing unless the user already approved those specific actions.

For approved rebases, use an isolated worktree and recoverable backup ref, validate the result, and push with `--force-with-lease` pinned to the observed remote SHA. Respect fork ownership and branch protection; abort and report conflicts safely. Validate review-driven fixes, re-query remote state after mutations, and finish with per-PR results and unresolved work.
