---
name: review-deep
description: Review current changes, a pull request, or a specified domain with specialist subagents for functionality, code smell, performance, overcomplexity, and better refactor or solution options.
---

# Review Deep

Use this skill when the user wants a deep review of current changes, a pull request, or a specified codebase domain, especially when they ask for functionality, code smell, performance, overcomplexity, or better solution analysis.

This is a review-only skill. Do not edit files. If the user wants automatic changes based on the deep review, use `review-deep-action` instead.

## Intent

Act as a senior reviewer coordinating a deeper-than-normal critique. Use your judgment to decide whether the request calls for reviewing a local diff, a PR-style branch diff, a named path, or a broader domain. Prefer the smallest scope that can answer the user's question well, but widen it when surrounding context is necessary to evaluate the design.

The goal is not to enforce a rigid process. The goal is to find the highest-impact issues and better solution directions that a single-pass review would likely miss.

As the parent agent, consider all subagent responses, validate them, and report the findings or recommendations you judge reasonable.

## Delegation

Use specialist subagents when they will materially improve coverage or reduce bias. Usually this means separate lenses for:

- Functionality: whether the code actually satisfies the intended behavior, user workflow, edge cases, integration contracts, tests, and observable outcomes.
- Code smell: maintainability risks, weak boundaries, duplication, poor invariants, awkward APIs, missing tests, and signs that the design is fighting the problem.
- Performance: meaningful algorithmic costs, redundant work, allocation or copy pressure, I/O inefficiency, concurrency bottlenecks, GPU/CPU transfer mistakes, and missing benchmarks.
- Overcomplexity: unnecessary branching, avoidable abstractions, fragmented behavior, excessive configuration, and simpler local patterns that would make the system easier to reason about.

Shape the prompts to the task instead of following a template. Give each subagent enough context to be useful, keep its lens distinct, and ask it not to modify files. If the review is small enough that subagents would add noise, handle it yourself and say so briefly.

## Review Standard

- Prioritize findings that materially affect correctness, learnability, maintainability, runtime cost, or the ability to evolve the system.
- Distinguish real risks from taste. A finding should explain the failure mode, the conditions that make it matter, and why the proposed direction is better.
- Prefer recommendations that fit the repository's existing patterns, unless the current pattern is part of the problem.
- For ML/RL systems, evaluate whether the implementation helps or hurts model performance, learning signal quality, observability, experiment velocity, and reproducibility.
- Be willing to propose a deeper refactor or replacement design when local fixes would preserve the wrong shape.

## Final Response

Use a code-review shape, adapted to what you found:

- Lead with findings, ordered by impact, with file and line references when possible.
- Keep summaries secondary to issues.
- Include open questions or assumptions when they affect confidence.
- Add a concise better refactor or solution section when there is a meaningful design alternative.
- If there are no findings, say that clearly and mention the most relevant residual risk or test gap.
