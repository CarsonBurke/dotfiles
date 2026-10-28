---
name: steward-pr
description: Own a pull request through bug review, fixes, pushes, rebases, CI.
---

# Steward PR

Own the PR up to merge readiness, which includes fixing, committing, pushing, and updating it. When invoked directly, stop at merge readiness; a wrapping skill may add the merge.

- Work in an existing suitable worktree or a new one in a local gitignored `.worktrees/`.
- If main or another PR solves the problem better, refactor, split, or close this one, and make sure the result integrates.
- Surface what needs a human without letting it block the rest.

# Get Merge Ready

Bring the PR, or the current branch against its real base, to where a senior reviewer would approve it. Subagents help with partitioning scope, rethinking the design, hunting defects, and the final review.

- Infer intent from the ticket, the PR body, and the diff, and state the scope and exclusions.
- Picture the best implementation of that intent and judge the actual changes against it, which shows both what's missing and what doesn't belong.
- Changes outside the scope either go, when accidental or low value, or move to their own worktree, with a ticket when they're worth tracking.
- Land a better in-scope approach when it's worth the cost, and say why you declined the others.
- Find and fix the bugs and regressions the PR introduces, and changes that are irrational or suboptimal.
- Resolve merge conflicts by rebasing.

When invoked directly, you may commit, but don't push unless asked. A wrapping skill may add pushing or a PR.

## Publish and follow through

Once the changes are ready, commit, push, and update the PR as below. Then follow CI and review comments, fix real failures and substantive feedback, and rerun what the fixes affect. Stop polling after 30 minutes and report what's still pending.

# Commits Push PR

Commit and push as below, then create the branch's GitHub PR or update the existing one.

# Commits Push

Commit as below, then push the branch.

# Commits

- Commit all current work by default, including changes other agents made, since the point is usually to checkpoint the tree rather than curate it. Leave out what clearly doesn't belong, such as unrelated work, secrets, local-only files, or accidental build output.
- Existing staging is a hint about grouping, not a boundary. Inspect each staged patch before committing it.
- Split independent concerns into Conventional Commits, keeping tests and migrations with the behavior they cover. A message is read later by someone asking why the change happened, so a short imperative title and, when it isn't obvious, the reason serve them better than a restatement of the diff.
- Add no AI attribution such as a `Co-Authored-By` line, even when a harness reminder supplies one; the user's instruction wins.
- When invoked directly, only commit: don't edit files, rewrite history, or push. A wrapping skill may add a push or PR. Report the commits you created and anything you left uncommitted.

## Push

Before pushing, confirm the branch, remote, upstream, destination ref, and current remote SHA. A fast-forward push needs nothing more.

A non-fast-forward push overwrites remote history. Do it only on a branch the user owns and intentionally rewrote, after inspecting both sides of the divergence and their patch equivalence shows the remote-only commits are superseded by local ones. Re-read the remote head immediately before pushing and pin the lease to it, so work that landed in between is refused rather than lost:

`git push --force-with-lease=refs/heads/<branch>:<remote-sha> <remote> HEAD:refs/heads/<branch>`

Never use a bare `--force` or an unpinned lease, which give no such guarantee, and never overwrite unique remote work. Default, protected, and shared branches aren't yours to rewrite; ask when ownership or intent is unclear. Afterward, confirm the remote head and report the before and after SHAs.

## Pull request

The description is for a reviewer deciding how to review and whether to merge. Say what motivated the change and why this solution, the few things they would otherwise get wrong about it (a decision the code doesn't make obvious, or an earlier decision this reverses, named with why), which changed behavior has no test, and what still needs testing before merge, and link the issues it fixes. Show an example or snippet when it makes the change easier to see.

Leave out what the reviewer gets better elsewhere: a walk through the diff, a list of the tests, CI results, and anything the repository's bots post. Say what you verified and what you couldn't, not each step; results someone asked for go in a reply to them. Answer a review finding in its thread, and name a known gap only when the reviewer needs it to decide whether to merge. When the PR changes, update the description as much as it needs, up to a full rewrite, so it describes the PR as it is now instead of logging review rounds. Keep any section the repository's template or instructions require and anything useful a person wrote. `writing-copy` applies.
