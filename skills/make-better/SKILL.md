---
name: make-better
description: Review changed code for simplicity, performance, and security in a single pass, then fix all issues found. Operates on the current git diff or a provided path.
---

# Make Better

Use this skill when the user wants a holistic improvement pass over changed code.

- Review files in the current git diff (or a provided path) through three lenses — simplicity, performance, and security — in a single pass.
- Fix what you find. This is an action skill, not a review skill.
- Examples: convoluted logic, dead code, redundant computation, bad complexity, unnecessary allocations, injection risks, auth gaps, data exposure — but use good judgement across all three dimensions.
- After making your changes, spawn a subagent to review. Address reasonable concerns and follow up as necessary.
- Summarize what you changed and why when done.
