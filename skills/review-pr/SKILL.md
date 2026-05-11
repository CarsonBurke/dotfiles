---
name: review-pr
description: Review commits in the current branch that are not in main, using the merge-base diff, without making changes.
---

# Review PR

- Review only changes in branch against the pr target.
- Use exactly ``git log `git merge-base main HEAD`..HEAD --oneline --no-merges`` to list commits.
- Use exactly ``git diff `git merge-base main HEAD`..HEAD`` to inspect the introduced changes.
- Prioritize bugs, risks, behavioral regressions, and security issues.
- Do not make unprompted changes.
