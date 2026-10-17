---
name: handshake-review
description: Perform a deep, read-only code review with at least one independent reviewer from a different model or tool.
---

# Handshake Review

The point is a second opinion from a different model or tool, so at least one reviewer must be one, even though the shared standards below treat that as optional. If none is available, say the handshake can't be done rather than quietly running an ordinary review. Keep it read-only and validate its claims yourself.

Sending non-public code to an external service needs the user's explicit authorization. Share only the scope under review, without secrets, credentials, or personal data.

# Review Deep

Stay read-only. Infer the scope from the request and the state of the repository, and mention exclusions that matter.

Independent read-only reviewers help when the scope is large or has distinct concerns, such as security or performance alongside behavior. Give them the raw context rather than what you expect them to find, or they'll tend to confirm it. A cross-model reviewer is optional. Non-public code, secrets, credentials, and personal data go to an external service only with explicit authorization.

Beyond correctness, ask whether a simpler solution exists.

Check each candidate finding against the code that reaches it, its callers and contracts, and the tests before reporting it. Drop what's speculative, stylistic, or outside the requested scope, and when reviewing a change, what predates it, since noise makes the real findings easier to skim past. Report findings by severity with evidence and file references, then open questions and anything you couldn't validate. When none remain, say so plainly.
