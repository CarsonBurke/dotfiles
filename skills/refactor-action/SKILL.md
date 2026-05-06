---
name: refactor-action
description: Implement worthwhile refactors from the current or specified scope, using delegated work and review when appropriate.
---

# Refactor Action

Follow `refactor-find` for scope, delegation, and refactor judgment. The difference is the parent role: after considering and validating the refactor candidates, make or oversee the changes you judge reasonable instead of only reporting them.

Use worktrees where reasonable, generally for changes that aren't small. Use implementation subagents when the work naturally splits by domain, and keep their write scopes clear and separate.

After implementation and where reasonable (usually), have a new set of subagents review. Address material concerns and repeat review until the changes are approved.

Summarize what changed, what was intentionally skipped, and what validation ran.
