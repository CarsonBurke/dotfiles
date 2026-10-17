---
name: make-perfect
description: Deeply review and improve current changes, a pull request, or a codebase domain.
---

# Make Perfect

# Review Deep Action

Infer the scope from the request and the state of the repository, and mention exclusions that matter. Review by the standards below, then fix the findings worth fixing.

Independent read-only reviewers help when the scope is large or has distinct concerns, such as security or performance alongside behavior. Give them the raw context rather than what you expect them to find, or they'll tend to confirm it. A cross-model reviewer is optional. Non-public code, secrets, credentials, and personal data go to an external service only with explicit authorization.

Beyond correctness, ask whether a simpler solution exists.

Check each candidate finding against the code that reaches it, its callers and contracts, and the tests before reporting it. Drop what's speculative, stylistic, or outside the requested scope, and when reviewing a change, what predates it, since noise makes the real findings easier to skim past. Report findings by severity with evidence and file references, then open questions and anything you couldn't validate. When none remain, say so plainly.

## Implement findings

Preserve unrelated changes and public behavior unless the request says otherwise. Run the affected checks, inspect the final diff, and after non-trivial work use `sub-review-changes`. Report what you changed, which findings you declined, validation, and residual risk. Don't commit or push unless asked.
