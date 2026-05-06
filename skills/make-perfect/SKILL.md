---
name: make-perfect
description: Review changed code with parallel performance, security, and simplicity subagents, then reasonably fix the concerns they raise.
---

# Make Perfect

- Review files in the current git diff (or a provided path).
- Spawn three subagents in parallel:
  - one applying the spirit of `make-fast`
  - one applying the spirit of `make-secure`
  - one applying the spirit of `make-simple`
- Have subagents report findings only, not edit files.
- Consider all reports, validate the concerns, and fix what you judge real and worthwhile. This is an action skill, not a review skill.
- Prefer fixes that improve multiple lenses at once. When recommendations conflict, preserve correctness first, address real security risk before performance or simplification, and avoid churn.
- Run relevant validation when practical.
- Summarize what you changed, which concerns you declined, and what validation you ran.
