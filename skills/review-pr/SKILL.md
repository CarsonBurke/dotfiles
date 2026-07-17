---
name: review-pr
description: Review a pull request or the current branch against its actual base without making changes.
---

# Review PR

Remain read-only.

- For a PR, resolve its actual `baseRefName` and remote `headRefOid`; review the merge-base diff through that remote head, not local `HEAD`.
- For a deliberately local branch review, use local `HEAD` against the repository's actual default or requested base. Disclose unpushed or divergent commits.
- Validate findings against surrounding code, contracts, and tests. Report only introduced, actionable correctness, regression, security, compatibility, performance, or coverage issues with severity and precise references.
