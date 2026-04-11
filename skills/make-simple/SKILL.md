---
name: make-simple
description: Review changed code for unnecessary complexity and simplify it. Operates on the current git diff or a provided path.
---

# Make Simple

Use this skill when the user wants to reduce complexity in changed code.

- Review files in the current git diff (or a provided path) for unnecessary complexity.
- Fix what you find. This is an action skill, not a review skill.
- Examples: convoluted conditionals, excessive nesting, over-abstraction, dead code paths, unclear data flow — but use good judgement.
- After making your changes, spawn a subagent to review. Address reasonable concerns and follow up as necessary.
