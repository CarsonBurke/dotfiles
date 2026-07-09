---
name: commits
description: Create Conventional Commit commit(s) from all current changes, separated by concern, without pushing.
---

# Commits

- Inspect staged, unstaged, and untracked changes. Default to committing all current work, including changes made by other agents; exclude only clearly unrelated, sensitive, local-only, or accidental generated content.
- Treat existing staging as a useful signal, not an authorization boundary. Stage deliberately and inspect each final staged patch.
- Separate independent concerns into idiomatic Conventional Commits. Keep related tests and migrations with their behavior; use short imperative titles and no AI attribution.
- Do not edit files, rewrite history, or push. Report created commits and anything left uncommitted.
