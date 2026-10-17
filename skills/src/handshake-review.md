---
name: handshake-review
description: Perform a deep, read-only code review with at least one independent reviewer from a different model or tool.
---

# Handshake Review

Use at least one available independent reviewer from a different model or tool, keep it read-only, and validate its claims yourself. If no cross-model reviewer is available, report that the requested handshake cannot be completed instead of silently performing an ordinary review. The cross-model reviewer is required here, even though it is optional in the shared workflow below.

Do not send non-public code or data to an external service without explicit user authorization. Scope the shared artifact narrowly and exclude secrets, credentials, personal data, and unrelated repository content.

<!-- include: review-deep -->
