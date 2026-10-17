---
name: maintain-tests
description: Improve a test suite by removing dead tests, fixing brittle tests, and adding meaningful missing coverage.
---

# Maintain Tests

Choose each test's level by what it protects and what a failure would cost. Types make assertions about shape redundant, but not tests of runtime behavior. Remove a test only when it's dead or duplicates other coverage. Brittle tests usually depend on shared state, ordering, time, or randomness, and the fix is removing that dependency rather than adding retries. Change production code only as far as testability needs.
