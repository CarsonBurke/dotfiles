---
name: review-deep-action
description: Deeply review and improve current changes, a pull request, or a codebase domain.
---

# Review Deep Action

Infer the intended scope from the request, conversation, working tree, branch, PR context, and cwd; state any important exclusions. Review using the judgment and evidence standards below, then fix validated, worthwhile findings.

<!-- include: parts/review-standards -->

## Implement findings

Preserve unrelated changes and public behavior unless the request says otherwise. Run affected checks, inspect the final diff, and use `sub-review-changes` after non-trivial work. Report changes, declined findings, validation, and residual risk. Do not commit or push unless requested.
