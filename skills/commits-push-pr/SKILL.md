---
name: commits-push-pr
description: Commit changes, push the branch, and create or reuse its GitHub pull request.
---

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
