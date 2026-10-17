---
name: commits
description: Create Conventional Commit commit(s) from all current changes, separated by concern, without pushing.
---

# Commits

- Commit all current work by default, including changes other agents made, since the point is usually to checkpoint the tree rather than curate it. Leave out what clearly doesn't belong, such as unrelated work, secrets, local-only files, or accidental build output.
- Existing staging is a hint about grouping, not a boundary. Inspect each staged patch before committing it.
- Split independent concerns into Conventional Commits, keeping tests and migrations with the behavior they cover. A message is read later by someone asking why the change happened, so a short imperative title and, when it isn't obvious, the reason serve them better than a restatement of the diff.
- Add no AI attribution such as a `Co-Authored-By` line, even when a harness reminder supplies one; the user's instruction wins.
- When invoked directly, only commit: don't edit files, rewrite history, or push. A wrapping skill may add a push or PR. Report the commits you created and anything you left uncommitted.
