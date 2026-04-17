---
name: tend-tests
description: Steward a test suite — remove dead tests, update outdated ones, fix stateful or non-idiomatic ones. Operates on the current git diff or a provided path.
---

# Tend Tests

Use this skill when the user wants their tests reviewed and improved, not just added to.

- Review tests in the current git diff (or a provided path). Treat the test suite as code that needs maintenance, not a write-once artifact.
- Fix what you find. This is an action skill, not a review skill.
- Check each test for:
  - **Relevance** — delete tests for removed or superseded code, duplicated coverage, and tautological assertions.
  - **Correctness** — update tests whose expectations have drifted from current behavior. A test that passes by accident is worse than a failing one.
  - **Statelessness** — isolate tests that depend on shared state, execution order, global singletons, or leaked side effects. Each test should pass alone and in any order.
  - **Idiomaticity** — refactor ad-hoc patterns into the framework's conventions (setup/teardown, matchers, fixtures, parameterization). Match the surrounding test style.
  - **Signal** — remove tests that only assert mocks were called, over-mock the system under test, or would pass regardless of the production code's behavior.
- Prefer deleting a weak test over keeping it — useless tests create false confidence and slow the suite.
- When improving a test, preserve (or sharpen) what it actually verifies. Don't weaken assertions just to make the test simpler.
- Run the affected test suite after your changes and confirm it passes.
- Spawn a subagent to review. Address reasonable concerns and follow up as necessary.
- Summarize what was removed, updated, and improved, and why.
