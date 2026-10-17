---
name: steward-pr
description: Own a pull request through bug review, fixes, pushes, rebases, CI.
---

# Steward PR

Take ownership of the PR up to merge readiness. This workflow authorizes fixes, commits, pushes, and PR updates. When invoked directly, stop at merge readiness; a composing skill may add a merge step.

- Work in an existing suitable worktree or create one in a local gitignored `.worktrees/` directory.
- Review the PR against its base, understand its intent, and apply the merge-readiness workflow below. Address substantive review feedback and CI failures. Surface things needing human review without disrupting independent work.
- Be comfortable refactoring, splitting, or closing the PR when superior solutions exist in main or other PRs. Ensure the result integrates well.

<!-- include: get-merge-ready -->

## Publish and follow through

After the changes are ready, complete the commit, push, and PR workflow below. Follow CI and review comments, address failures and substantive feedback, and repeat affected checks after changes. Do not poll for longer than 30 minutes; report pending checks or unresolved blockers when that limit is reached.

<!-- include: commits-push-pr -->
