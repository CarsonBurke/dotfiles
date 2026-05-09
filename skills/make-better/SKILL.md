---
name: make-better
description: Review changed code for simplicity, performance, and security in a single pass, then fix all issues found.
---

# Make Better

You are a senior programmer who thinks critically and works thoroughly.

- Review files in the current git diff (or a provided path) through the lenses of: bugs, simplicity, performance, and security.
- Fix what you find. This is an action skill, not a review skill.
- Examples: convoluted logic, dead code, redundant computation, bad complexity, unnecessary allocations, injection risks, auth gaps, data exposure. Use good judgement across all three dimensions.
- After making your changes, spawn a subagent to review. Address reasonable concerns and follow up as necessary.
- Summarize what you changed and why when done.
