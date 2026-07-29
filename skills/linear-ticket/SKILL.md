---
name: linear-ticket
description: Implement a Linear ticket end to end in a dedicated worktree.
---

- You may already be in the worktree, and it may already have some work done on it.
- Read the ticket; it may be a customer complaint or a schema for implmeneting a change or feature. Infer the goal and fulfill it idiomatically and fully.
- Do not PR unless asked.
- Reuse the correct Ticket worktree when present; do not nest worktrees. In Orca-managed contexts use `orca-cli`. Otherwise inspect status, branches, and worktrees before creating a dedicated branch/worktree from the actual base.
