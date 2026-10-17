---
name: make-simple
description: Simplify and debloat code using refactor-action.
---

# Make Simple

Look first for duplication, dead paths, abstraction nothing needs, and control flow split across more places than it has to be.

# Refactor Action

Recommend a refactor only when it has a concrete payoff, and describe the intended shape, compatibility needs, effort, and risk. Cosmetic churn, speculative abstraction, and vague cleanup advice cost review time and return nothing.

Implement the coherent end state rather than a partial step toward it, preserving behavior and sequencing any compatibility or migration work safely. Don't commit or push unless asked.
