---
name: make-perfect
description: Review changed code with parallel performance, security, and simplicity subagents, then reasonably fix the concerns they raise.
---

# Make Perfect

- Review files in the current git diff (or a provided path).
- Spawn three read-only subagents in parallel doing:
  - `make-fast`
  - `make-secure`
  - `make-simple`
- Have subagents report findings, their task is read only
- Consider all reports, validate the concerns, and fix what you judge real and worthwhile. This is an action skill, not a review skill.
- Prefer fixes that improve multiple lenses at once. When recommendations conflict, preserve correctness first, address real security risk before performance or simplification, and avoid churn.
- Run relevant validation when practical.
- Summarize what you changed, which concerns you declined, and what validation you ran.
