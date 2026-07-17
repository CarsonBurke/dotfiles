---
name: review-deep
description: Perform a comprehensive, multi-perspective, read-only review of current changes, a pull request, or a codebase domain.
---

# Review Deep

Remain read-only. Infer the intended scope from the request, conversation, working tree, branch, PR context, and cwd; state any important exclusions.

Use independent read-only reviewers when they materially improve coverage. Cover behavior and integrations, security, meaningful performance, maintainability, tests, and simpler solution options. Give reviewers raw context rather than expected findings. Cross-model review is optional; never send non-public code, secrets, credentials, or personal data to an external service without explicit authorization.

Validate candidate findings against reachable code, contracts, call sites, and tests. Reject speculative, pre-existing, stylistic, or scope-external concerns. Report actionable findings by severity with evidence and precise references, followed by open questions or validation gaps. Say explicitly when none remain.
