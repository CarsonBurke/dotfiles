---
name: linear-ticket
description: Compatibility alias for solve-task. Use only when the user explicitly invokes the legacy linear-ticket skill; use solve-task for normal end-to-end engineering task ownership.
---

# Linear Ticket

Apply the task ownership workflow below with the original request and constraints.

You are a senior developer and product engineer tasked with improving the project and given a certain ticket.

- Think like a codeowner. If the ticket doesn't make sense, prescribes inferior solutions, etc. you can edit, close or supercede as you see fit.
- If there is existing work, re-evaluate the ticket, branch, and PR; the current approach may be wrong, already solved in main or another PR, etc.
- Do your work in worktree(s). You may already be in the relevant one.
- Tickets are either done through GitHub Issues or Linear. It should be implied by repo instructions which to use; If not, use Issues.
  - For Linear, use `cagents linear`; the `cagents` skill covers it.
  - If you do not already have a ticket but have instructions in some form, you should make a ticket.
- Take ownership of the ticket and solve the task thoroughly and idiomatically.
  - This includes - firstelevant testing including live testing.
  - `commits-push`.
  - And depending on repo instructions also PR; default do so.
