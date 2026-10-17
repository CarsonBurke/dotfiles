---
name: validate-frontend
description: Validate frontend changes in a real browser without editing source files or production data.
---

# Validate Frontend

- Validate only: do not edit source or update snapshots/fixtures.
- Infer affected scenarios from the change, then use the `browser` skill in a dedicated work window to exercise them and the nearest plausible regression path.
- Verify visible output, interaction, relevant URL/data state, console/network health, and affected viewport or role/state variants.
- Keep production read-only; use a test environment or report the blocker when validation would mutate data or perform a consequential action.
- Report exact scenarios and pass/fail evidence, separating implementation recommendations from validation results.
