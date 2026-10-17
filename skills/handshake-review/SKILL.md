---
name: handshake-review
description: Perform a deep, read-only code review with at least one independent reviewer from a different model or tool.
---

# Handshake Review

Use at least one available independent reviewer from a different model or tool, keep it read-only, and validate its claims yourself. If no cross-model reviewer is available, report that the requested handshake cannot be completed instead of silently performing an ordinary review. The cross-model reviewer is required here, even though it is optional in the shared workflow below.

Do not send non-public code or data to an external service without explicit user authorization. Scope the shared artifact narrowly and exclude secrets, credentials, personal data, and unrelated repository content.

# Review Deep

Remain read-only. Infer the intended scope from the request, conversation, working tree, branch, PR context, and cwd; state any important exclusions.

Use independent read-only reviewers when they materially improve coverage. Cover behavior and integrations, security, meaningful performance, maintainability, tests, and simpler solution options. Give reviewers raw context rather than expected findings. Cross-model review is optional; never send non-public code, secrets, credentials, or personal data to an external service without explicit authorization.

Validate candidate findings against reachable code, contracts, call sites, and tests. Reject speculative, pre-existing, stylistic, or scope-external concerns. Report actionable findings by severity with evidence and precise references, followed by open questions or validation gaps. Say explicitly when none remain.
