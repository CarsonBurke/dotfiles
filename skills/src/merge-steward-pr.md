---
name: merge-steward-pr
description: Steward a pull request through review, fixes, pushes, and CI, then merge it once ready. Use when asked to take a PR through to merge.
---

# Merge Steward PR

Steward the PR as below, then merge it.

<!-- include: steward-pr -->

## Merge after stewardship

The merge gate is a thorough subagent review of the final head that approves with no findings. That review stands in for human approval, so overriding the repository's review requirements to merge is fine. Merge with `gh pr merge --match-head-commit` pinned to the current head SHA that review approved, so nothing lands unreviewed.
