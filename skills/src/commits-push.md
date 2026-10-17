---
name: commits-push
description: Create Conventional Commit commit(s) from all current changes, separated by concern, then push them.
---

# Commits Push

Commit as below, then push the branch.

<!-- include: commits -->

## Push

Before pushing, confirm the branch, remote, upstream, destination ref, and current remote SHA. A fast-forward push needs nothing more.

A non-fast-forward push overwrites remote history. Do it only on a branch the user owns and intentionally rewrote, after inspecting both sides of the divergence and their patch equivalence shows the remote-only commits are superseded by local ones. Re-read the remote head immediately before pushing and pin the lease to it, so work that landed in between is refused rather than lost:

`git push --force-with-lease=refs/heads/<branch>:<remote-sha> <remote> HEAD:refs/heads/<branch>`

Never use a bare `--force` or an unpinned lease, which give no such guarantee, and never overwrite unique remote work. Default, protected, and shared branches aren't yours to rewrite; ask when ownership or intent is unclear. Afterward, confirm the remote head and report the before and after SHAs.
