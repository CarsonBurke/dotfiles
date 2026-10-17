---
name: make-simple
description: Simplify and debloat code using refactor-action.
---

# Make Simple

Prioritize removal of duplication, dead paths, accidental abstraction, and fragmented control flow. Avoid cosmetic churn and speculative frameworks.

# Refactor Action

Recommend only refactors with a concrete payoff and explain the intended shape, compatibility needs, effort, and risk. Exclude cosmetic churn, speculative abstraction, and vague cleanup advice.

Implement the coherent end state while preserving behavior and sequencing any compatibility or migration work safely. Do not commit or push unless requested.
