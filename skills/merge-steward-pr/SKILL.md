---
name: merge-steward-pr
description: Steward a pull request through review, fixes, pushes, and CI, then merge it once ready. Use when asked to take a PR through to merge.
---

# Merge Steward PR

Complete the stewardship workflow below, then merge the PR.

# Steward PR

Take ownership of the PR up to merge readiness. This workflow authorizes fixes, commits, pushes, and PR updates. When invoked directly, stop at merge readiness; a composing skill may add a merge step.

- Work in an existing suitable worktree or create one in a local gitignored `.worktrees/` directory.
- Review the PR against its base, understand its intent, and apply the merge-readiness workflow below. Address substantive review feedback and CI failures. Surface things needing human review without disrupting independent work.
- Be comfortable refactoring, splitting, or closing the PR when superior solutions exist in main or other PRs. Ensure the result integrates well.

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

## Publish and follow through

After the changes are ready, complete the commit, push, and PR workflow below. Follow CI and review comments, address failures and substantive feedback, and repeat affected checks after changes. Do not poll for longer than 30 minutes; report pending checks or unresolved blockers when that limit is reached.

# Commits Push PR

Complete the commit and push workflow below, then create or update the PR.

# Commits Push

Complete the commit workflow below, then push the resulting branch.

# Commits

- Inspect staged, unstaged, and untracked changes. Default to committing all current work, including changes made by other agents; exclude only clearly unrelated, sensitive, local-only, or accidental generated content.
- Treat existing staging as a useful signal, not an authorization boundary. Stage deliberately and inspect each final staged patch.
- Separate independent concerns into idiomatic Conventional Commits. Keep related tests and migrations with their behavior; use short imperative titles and no AI attribution.
- When invoked directly, do not edit files, rewrite history, or push; wrapper skills may add subsequent push or PR actions. Report created commits and anything left uncommitted.

## Push

Verify the branch, remote, upstream, destination ref, and current remote SHA. Push normally when the update is fast-forward.

For a non-fast-forward update, inspect both sides of the divergence and their patch equivalence. An intentionally rewritten, user-owned feature or PR branch may be updated only when its remote-only commits are clearly superseded by the local history. Re-read the remote head immediately before pushing, then use an explicit lease tied to that SHA:

`git push --force-with-lease=refs/heads/<branch>:<remote-sha> <remote> HEAD:refs/heads/<branch>`

Never use bare `--force` or an unqualified lease, overwrite unique remote work, or force-update a default, protected, shared, or ambiguously owned branch. Ask when ownership or rewrite intent is unclear. Verify the resulting remote head and report the before and after SHAs.

## Pull request

Create or reuse the branch's GitHub PR. Explain the motivation and chosen solution, respecting the reader's time and attention. Include examples, snippets, or screenshots when useful, and describe anything that should still be tested before merging.

## Merge after stewardship

- A thorough subagent review must approve merge with no findings.
- It is acceptable to override review requirements.
