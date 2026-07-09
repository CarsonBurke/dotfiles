---
name: summarize-pushed-pr-changes
description: Summarize newly pushed PR commits from a known pre-push head SHA through the current remote head with exact GitHub links.
---

# Summarize Pushed PR Changes

Remain read-only. Require a known full pre-push SHA for each PR; never substitute the PR merge base. Verify it is an ancestor of the current remote `headRefOid`, then summarize only that log and diff. If the SHA is unknown or invalid, say an exact incremental summary is unavailable.

Return one row per PR:

| PR | Reason | Incremental changes | Exact diff |
| --- | --- | --- | --- |

Link one new commit to its PR commit page and multiple commits to the repository's verified `/compare/<OLD>..<NEW>` view. Mention deferred items only when they belong to the exact range.
