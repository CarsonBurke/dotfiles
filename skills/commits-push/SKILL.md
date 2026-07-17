---
name: commits-push
description: Create Conventional Commit commit(s) from all current changes, separated by concern, then push them.
---

# Commits Push

Follow `commits`, then verify the branch, remote, upstream, destination ref, and current remote SHA. Push normally when the update is fast-forward.

For a non-fast-forward update, inspect both sides of the divergence and their patch equivalence. An intentionally rewritten, user-owned feature or PR branch may be updated only when its remote-only commits are clearly superseded by the local history. Re-read the remote head immediately before pushing, then use an explicit lease tied to that SHA:

`git push --force-with-lease=refs/heads/<branch>:<remote-sha> <remote> HEAD:refs/heads/<branch>`

Never use bare `--force` or an unqualified lease, overwrite unique remote work, or force-update a default, protected, shared, or ambiguously owned branch. Ask when ownership or rewrite intent is unclear. Verify the resulting remote head and report the before and after SHAs.
