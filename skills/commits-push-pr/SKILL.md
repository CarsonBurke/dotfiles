---
name: commits-push-pr
description: Commit changes, push the branch, and create or reuse its GitHub pull request.
---

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

The description is for a reviewer deciding how to review and whether to merge. Say what motivated the change and why this solution, the few things they would otherwise get wrong about it (a decision the code doesn't make obvious, or an earlier decision this reverses, named with why), which changed behavior has no test, and what still needs testing before merge, and link the issues it fixes. Leave out what the diff, tests, CI, and the repository's bots already show, including an inventory of what each part of the change does. Say what you verified, not each step; results someone asks for go in a reply to them, and review findings get answered in their threads. When the PR changes, update the description as much as it needs, up to a full rewrite. Keep any section the repository requires and anything useful a person wrote. `writing-copy` applies.
