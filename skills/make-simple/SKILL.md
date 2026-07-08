---
name: make-simple
description: Simplify, debloat and cleanup in an implied scope.
---

- Infer the scope independently: If there are are uncommitted changes do that; if it's a PR do the PR; if in the main branch, do the whole branch. Or if the user specifies scope.
- Identify significant simplification/bloat/cleanup items in the scope. Be thorough and use good judgement.
- Fix what you find, unless specified otherwise.
