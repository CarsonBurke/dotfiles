---
name: maintain-prs
description: Maintain open GitHub pull requests by handling staleness, base divergence, and review feedback.
---

# Maintain PRs

- Audit each PR before acting on it, including its checks, review threads, linked issues, who owns the head, your permissions, and how far it really diverges from its base.
- Age, a closed issue, or a touched file only suggests a PR is obsolete; confirm against current behavior. Don't close linked issues as a side effect.
- Closing, rebasing, and force-pushing are hard to undo, so report each PR's evidence and proposed action and confirm those specific PRs first, unless the user already approved them.
- For an approved rebase, work in an isolated worktree with a backup ref, validate the result, and push with `--force-with-lease` pinned to the remote SHA you observed. Respect fork ownership and branch protection, and abort cleanly on conflicts.
- Validate review-driven fixes. Re-query the remote after each change, and finish with each PR's result and what's still unresolved.
