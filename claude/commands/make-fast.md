---
name: make-fast
description: Review changed code for performance issues and optimize it.
---

Review files in the current git diff for performance issues, then fix what you find. If `$ARGUMENTS` is a path, use that instead of the diff.

Examples: redundant computation, bad algorithmic complexity, unnecessary allocations, N+1 queries, missing caching — but use good judgement.
