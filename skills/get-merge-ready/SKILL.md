---
name: get-merge-ready
description: Get a PR or branch into merge-ready shape a senior would approve.
---

# Get Merge Ready

Bring the PR (or current branch vs its real base) to a senior-approvable state. Use independent subagents liberally for scope partition, design rethink, defect hunting, and final review.

1. Infer intent from ticket, PR body, and base…head diff; state scope and exclusions.
2. Partition changes into core, justified adjacent, out-of-scope, and noise.
3. For out-of-scope: delete if accidental or low value; extract real follow-up to a dedicated worktree (and ticket/issue only when authorized); keep only with a short justification.
4. Rethink the chosen solutions. Land better in-scope approaches when worth the cost; decline the rest with reason.
5. Find and fix introduced bugs, regressions, and bad changes. Validate against contracts, call sites, and tests.
6. Run affected checks; use `sub-review-changes` after non-trivial edits.
7. Report readiness verdict, extractions, declined work, validation, and residual risk.

Do not merge. Do not commit, push, force-push, or create remote tickets unless requested. Prefer the PR head or existing ticket worktree; never thrash unrelated local state.
