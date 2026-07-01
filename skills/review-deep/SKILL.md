---
name: review-deep
description: Review current changes, a pull request, or a specified domain with specialist subagents for functionality, code smell, performance, overcomplexity, and better refactor or solution options.
---

# Review Deep

This is a review-only skill. Do not edit files. For automatic changes based on the deep review, use `review-deep-action` instead.

## Intent

Act as a senior reviewer coordinating a deeper-than-normal critique. Use your judgment to decide whether the request calls for reviewing a local diff, a PR-style branch diff, a named path, or a broader domain.
As the parent agent, consider all subagent responses, validate them, and report the findings or recommendations you judge reasonable.

## Delegation

Use specialist subagents when they will materially improve coverage or reduce bias. Usually this means separate lenses for:

- Functionality: whether the code actually satisfies the intended behavior, user workflow, edge cases, integration contracts, tests, and observable outcomes.
- Code smell: maintainability risks, weak boundaries, duplication, poor invariants, awkward APIs, missing tests, and signs that the design is fighting the problem.
- Performance: meaningful algorithmic costs, redundant work, allocation or copy pressure, I/O inefficiency, concurrency bottlenecks, mistakes, and missing benchmarks.
- Overcomplexity: unnecessary branching, avoidable abstractions, fragmented behavior, excessive configuration, and simpler local patterns that would make the system easier to reason about.

Shape the prompts to the task instead of following a template. Give each subagent enough context to be useful, keep its lens distinct, and ask it not to modify files. If the review is small enough that subagents would add noise, handle it yourself.
