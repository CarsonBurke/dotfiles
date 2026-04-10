---
name: review-prs
description: Review open PRs — close stale ones, rebase outdated branches, and address review comments.
---

# Review PRs

Review all open PRs, close stale ones where the linked issue is already fixed, rebase outdated branches, and address review feedback.

## Arguments

- `--dry-run` — Report what would be done without taking any action
- `--pr NUMBER` — Process only one specific PR

## Workflow

### Phase 1: Discover PRs

1. `git fetch origin`
2. Determine the default branch: `gh repo view --json defaultBranchRef --jq '.defaultBranchRef.name'`
3. `gh pr list --state open --json number,title,headBranch,url,reviewDecision,body,createdAt --limit 100`
4. For each PR, extract a linked issue number from the branch name (`fix/<digits>-<slug>`) or body (`fixes #N`, `closes #N`, `resolves #N`).
5. Print the discovered PR list before proceeding.

### Phase 2: Process Each PR (Steps A -> B -> C)

**Step A — Check if stale** (skip if no linked issue):
- If linked issue is closed -> close the PR with a comment.
- If linked issue is open, check if its relevant files changed on the default branch since PR creation. If so, verify whether the bug still exists. If resolved -> close both.

**Step B — Rebase if needed:**
- `git merge-base --is-ancestor origin/<default-branch> origin/<branch>` to check.
- If rebase needed: create `backup/<branch>-pre-rebase`, rebase in a temp worktree, force-push with lease.
- If conflicts: abort, flag as `REBASE_CONFLICT`, skip Step C.

**Step C — Address review comments:**
- If changes requested: spawn an agent to apply fixes and push, or report comments for PRs without a linked issue.
- If approved or no reviews: skip.

**`--dry-run`**: Report only, take no actions.

### Phase 3: Summary Report

Print a markdown summary with sections: Closed (stale), Rebased, Rebase Conflicts, Reviews Addressed, Reviews Pending, Skipped.
