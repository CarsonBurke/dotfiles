---
name: make-better
description: Review changed code for simplicity, performance, and security, then fix all issues found.
---

Review files in the current git diff through three lenses — simplicity, performance, and security — then fix what you find in a single pass. If `$ARGUMENTS` is a path, use that instead of the diff.

Examples: convoluted logic, dead code, redundant computation, bad complexity, unnecessary allocations, injection risks, auth gaps, data exposure — but use good judgement across all three dimensions. Summarize what you changed and why when done.
