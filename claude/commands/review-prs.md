---
allowed-tools: Bash(gh pr list:*), Bash(gh pr view:*), Bash(gh pr close:*), Bash(gh issue view:*), Bash(gh issue close:*), Bash(gh issue comment:*), Bash(git fetch:*), Bash(git log:*), Bash(git worktree:*), Bash(git rebase:*), Bash(git push:*), Bash(git merge-base:*), Bash(git rev-parse:*), Bash(git branch:*), Bash(git status:*), Read, Grep, Glob, Agent
description: Review open PRs — close stale ones, rebase, and address review comments.
argument-hint: [--dry-run] [--pr NUMBER]
---

# Review PRs

You are a PR maintenance coordinator. Your job is to review all open PRs, close stale ones where the linked issue is already fixed, rebase outdated branches, and address review feedback.

## Arguments

- `--dry-run` — Report what would be done without taking any action
- `--pr NUMBER` — Process only one specific PR

User arguments: $ARGUMENTS

## Phase 1: Discover PRs

Fetch latest from origin first:

```bash
git fetch origin
```

Determine the default branch:

```bash
gh repo view --json defaultBranchRef --jq '.defaultBranchRef.name'
```

Then discover open PRs:

```bash
gh pr list --state open --json number,title,headBranch,url,reviewDecision,body,createdAt --limit 100
```

If `--pr NUMBER` was provided, filter to only that PR number.

For each PR, extract a linked issue number if one exists:

1. If `headBranch` matches `fix/<digits>-<slug>` (e.g. `fix/123-null-pointer-in-login`), extract the digits after `fix/`.
2. Otherwise, scan the PR body for `fixes #<number>`, `closes #<number>`, or `resolves #<number>` (case-insensitive).
3. If neither yields an issue number, the PR has no linked issue.

If no matching PRs are found, report that and stop.

Print the list of discovered PRs before proceeding, noting any linked issue numbers.

## Phase 2: Process Each PR

Process each PR sequentially. For each PR, run **Steps A -> B -> C** in order. Steps short-circuit only when the PR is closed (Step A).

### Step A: Check if PR is Stale (Bug Already Fixed)

**Skip this step entirely if the PR has no linked issue.**

1. Fetch the linked issue:

```bash
gh issue view <issue-number> --json body,state,title
```

2. **If the issue is already closed** -> close the PR with a comment and move to the next PR:

```bash
gh pr close <pr-number> --comment "Closing — linked issue #<issue-number> is already closed.

---
_Automated by \`/review-prs\`_"
```

3. **If the issue is open**, check if the relevant files changed on the default branch since the PR was created. Get the PR's changed files:

```bash
gh pr view <pr-number> --json files --jq '.files[].path'
```

4. Check if those files changed on the default branch since the PR was created:

```bash
git log origin/<default-branch> --since="<pr-createdAt>" --oneline -- "<file>"
```

5. **If files changed** -> the underlying code has been modified since this PR was created. Spawn an agent to check whether the bug described in the linked issue still exists in the current default branch. Pass it the issue number, title, body, and the relevant file paths.

6. **If the agent determines the bug is resolved** -> close both PR and issue:

```bash
gh issue close <issue-number> --comment "Closing — this bug appears to be resolved in the current codebase.

---
_Automated by \`/review-prs\`_"

gh pr close <pr-number> --comment "Closing — the bug reported in #<issue-number> has been resolved.

---
_Automated by \`/review-prs\`_"
```

Move to the next PR.

7. If the agent determines the bug still exists, or the files haven't changed, continue to Step B.

**In `--dry-run` mode**: Report what would happen but don't close anything or spawn agents.

### Step B: Rebase on Default Branch If Needed

1. Check if the branch is up to date:

```bash
git merge-base --is-ancestor origin/<default-branch> origin/<branch>
```

Exit code 0 means no rebase needed. Exit code 1 means rebasing is required.

2. **If rebase is needed**, create a backup branch first:

```bash
git branch backup/<branch>-pre-rebase origin/<branch>
git push origin backup/<branch>-pre-rebase
```

3. Then perform the rebase in a temporary worktree:

```bash
git worktree add /tmp/pr-rebase-<branch> origin/<branch>
cd /tmp/pr-rebase-<branch>
git rebase origin/<default-branch>
```

4. **If rebase is clean** (exit code 0):

```bash
git push --force-with-lease origin <branch>
cd -
git worktree remove /tmp/pr-rebase-<branch>
```

5. **If rebase has conflicts** (exit code non-zero):

```bash
git rebase --abort
cd -
git worktree remove /tmp/pr-rebase-<branch> --force
```

Flag this PR as `REBASE_CONFLICT` in the summary. Continue to next PR (skip Step C since the branch is in a bad state).

**In `--dry-run` mode**: Report whether rebase is needed but don't perform it.

### Step C: Address Review Comments If Any

1. Check the PR's review status:

```bash
gh pr view <number> --json reviewDecision,reviews,comments
```

2. **If `reviewDecision` is `CHANGES_REQUESTED` or there are unresolved review comments**:

   **If the PR has a linked issue:**
   - Spawn an agent to read the review comments, check out the branch in a worktree, apply fixes, and push.

   **If the PR has no linked issue:**
   - Report the review comments in the summary so the author can address them.
   - Include the reviewer name, comment body, and file/line for each unresolved comment.

3. **If `reviewDecision` is `APPROVED` with no outstanding comments** -> skip, the PR is clean.

4. **If there are no reviews at all** -> skip, nothing to address.

**In `--dry-run` mode**: Report what reviews exist but don't take action.

## Phase 3: Summary Report

After processing all PRs, print a structured markdown summary:

```
## PR Review Summary

**Total PRs found:** N

### Closed (stale)
- #XX — linked to issue #YY (reason)

### Rebased
- #XX — `branch-name` (backup: `backup/branch-name-pre-rebase`)

### Rebase Conflicts (manual intervention needed)
- #XX — `branch-name`

### Reviews Addressed
- #XX — fixes applied and pushed

### Reviews Pending (no linked issue)
- #XX — `branch-name` by @author
  - reviewer @name: "comment summary" (file:line)

### Skipped (clean)
- #XX — no action needed
```

If `--dry-run` was used, prefix the summary with: **DRY RUN — no actions were taken.**
