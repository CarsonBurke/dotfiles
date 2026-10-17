---
name: review-deep-action
description: Deeply review and improve current changes, a pull request, or a codebase domain.
---

# Review Deep Action

Infer the intended scope from the request, conversation, working tree, branch, PR context, and cwd; state any important exclusions. Review using the judgment and evidence standards below, then fix validated, worthwhile findings.

Use independent read-only reviewers when they materially improve coverage. Cover behavior and integrations, security, meaningful performance, maintainability, tests, and simpler solution options. Give reviewers raw context rather than expected findings. Cross-model review is optional; never send non-public code, secrets, credentials, or personal data to an external service without explicit authorization.

Validate candidate findings against reachable code, contracts, call sites, and tests. Reject speculative, pre-existing, stylistic, or scope-external concerns. Report actionable findings by severity with evidence and precise references, followed by open questions or validation gaps. Say explicitly when none remain.

## Implement findings

Preserve unrelated changes and public behavior unless the request says otherwise. Run affected checks, inspect the final diff, and use `sub-review-changes` after non-trivial work. Report changes, declined findings, validation, and residual risk. Do not commit or push unless requested.
