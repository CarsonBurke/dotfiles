---
name: handshake-review
description: Deprecated wrapper for review-deep's explicit cross-model mode. Use only when the user invokes handshake-review by name; do not trigger from ordinary review requests.
---

# Handshake Review

Follow `review-deep` in cross-model mode. Use at least one available independent reviewer from a different model or tool, keep it read-only, and validate its claims yourself. If no cross-model reviewer is available, report that the requested handshake cannot be completed instead of silently performing an ordinary review.

Do not send non-public code or data to an external service without explicit user authorization. Scope the shared artifact narrowly and exclude secrets, credentials, personal data, and unrelated repository content.
