---
name: review-deep-action
description: Deeply review and improve current changes, a pull request, or a codebase domain.
---

# Review Deep Action

Infer the scope from the request and the state of the repository, and mention exclusions that matter. Review by the standards below, then fix the findings worth fixing.

<!-- include: parts/review-standards -->

## Implement findings

Preserve unrelated changes and public behavior unless the request says otherwise. Run the affected checks, inspect the final diff, and after non-trivial work use `sub-review-changes`. Report what you changed, which findings you declined, validation, and residual risk. Don't commit or push unless asked.
