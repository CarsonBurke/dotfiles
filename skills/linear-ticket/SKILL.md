---
name: linear-ticket
description: Work a Linear ticket end to end, using Linear MCP to read the ticket and a dedicated git worktree when appropriate.
---

# Linear Ticket

Use this skill when the user provides a Linear ticket and wants implementation work done.

- Use Linear MCP to fetch the ticket details.
- Do not modify or create tickets unless the user explicitly asks.
- Prefer independence; ask clarifying questions only when necessary.
- Use a dedicated git worktree for each ticket when working in a git repo and not already in a ticket worktree.
- Derive the branch name from the Linear issue identifier and title slug when practical.
- If already inside the correct worktree, proceed there instead of creating another one.
