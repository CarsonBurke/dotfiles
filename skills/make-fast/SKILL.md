---
name: make-fast
description: Review changed code for performance issues and optimize it. Operates on the current git diff or a provided path.
---

# Make Fast

Use this skill when the user wants to optimize changed code for performance.

- Review files in the current git diff (or a provided path) for performance issues.
- Fix what you find. This is an action skill, not a review skill.
- Examples: redundant computation, bad algorithmic complexity, unnecessary allocations, N+1 queries, missing caching — but use good judgement.
- After making your changes, spawn a subagent to review. Address reasonable concerns and follow up as necessary.
