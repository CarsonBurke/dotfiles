---
name: find-domain-bugs
description: Audit one codebase domain or path for concrete bugs without making changes.
---

# Find Domain Bugs

Inspect the assigned scope without editing files or changing anything external, reading callers, dependencies, schemas, and tests elsewhere as far as you need to establish behavior.

A bug here is a reachable input, state, or interleaving that violates the code's expected contract, so establish both. Style, TODOs, refactor opportunities, unsupported hypotheticals, and missing tests without a demonstrated defect don't count. Keep what the repository shows apart from what you infer, and use narrow read-only checks where they help.

For each finding return:

```text
Summary: <one line>
Domain: <assigned domain>
Severity: critical | high | medium | low
Confidence: high | medium
Location: <repo-relative-file:line[, ...]>
Contract: <expected behavior>
Trigger: <reachable input or state>
Evidence: <why the code violates the contract>
Impact: <observable consequence>
Suggested fix: <minimal direction>
```

Use high confidence only when you've verified both the contract and the failing path. Mark credible leads you couldn't resolve as medium so the campaign parent can validate them. If nothing qualifies, return `No validated bugs found.`
