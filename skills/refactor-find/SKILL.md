---
name: refactor-find
description: Identify worthwhile idiomatic refactors in the current or specified folder without making code changes.
---

This is a read-only skill. Do not edit files.

Act as a senior engineer looking for refactors that are worth doing, not a style critic trying to rename everything. Identify messy or brittle solutions, duplicated logic, technical debt, non-idiomatic code, and designs that make the next change harder than it needs to be.

Draw a clear line between:

- Worth refactoring: changes with a payoff in maintainability, correctness, testability, performance, or future feature work. This isn't a high bar, and you may find many things worth refactoring.

Prefer recommendations that fit the repository's existing patterns. Call out when the existing pattern is itself part of the problem.

## Scope And Delegation

Use a reasonably inferred scope (usually the current dir) or if the user specified a scope.

Use subagents when the codebase is large enough that independent domain review will materially improve coverage. Generally use one read-only subagent per domain, such as frontend, backend, data layer, CLI, tests, infrastructure, or package boundaries.

## Review Standard

For each candidate refactor, validate that it is real and worth the cost. A useful finding explains:

- What is awkward, duplicated, brittle, or non-idiomatic.
- Why it matters in this codebase.
- What a better shape would look like.
- The likely effort and risk.
- Whether tests, migration steps, or compatibility constraints matter.

Avoid vague advice like "clean this up" or "make it more modular" unless you can describe the concrete direction.
