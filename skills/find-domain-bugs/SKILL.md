---
name: find-domain-bugs
description: Perform a focused, read-only, evidence-driven bug audit of one codebase domain or path. Use directly for focused audits or as the worker protocol for find-bugs campaigns.
---

# Find Domain Bugs

Inspect the assigned scope without editing files or changing external state. Read callers, dependencies, schemas, and tests outside it only as needed to establish behavior.

Report actual bugs, not style, TODOs, refactor opportunities, unsupported hypotheticals, or missing tests without a demonstrated defect. Establish both the expected contract and a reachable input, state, or interleaving that violates it. Distinguish repository evidence from inference and use narrow read-only checks when useful.

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

Use high confidence only when the contract and failing path are verified. Mark unresolved credible leads medium confidence so the campaign parent can validate them. If nothing qualifies, return `No validated bugs found.`
