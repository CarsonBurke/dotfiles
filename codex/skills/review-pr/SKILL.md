---
name: review-pr
description: Review commits in the current branch that are not in main, using the merge-base diff, without making changes.
metadata:
  short-description: Review branch changes against main
---

# Review PR

Use this skill when the user wants a PR-style review of branch changes against `main`.

- Review only commits in the current branch that are not in `main`.
- Use exactly ``git log `git merge-base main HEAD`..HEAD --oneline --no-merges`` to list commits.
- Use exactly ``git diff `git merge-base main HEAD`..HEAD`` to inspect the introduced changes.
- Do not use `$()` command substitution in bash for these commands.
- Prioritize bugs, risks, behavioral regressions, and security issues.
- Do not make unprompted changes.
