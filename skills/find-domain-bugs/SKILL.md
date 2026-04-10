---
name: find-domain-bugs
description: Analyze a specific codebase domain or path for actual bugs and return structured findings with file and line references.
---

# Find Domain Bugs

Use this skill when the user wants a focused bug hunt for a specific domain, package, or path.

Look for actual bugs, not style issues, TODOs, or missing tests. Focus on:

- Logic errors, off-by-one errors, and incorrect conditions
- Race conditions, missing awaits, and unhandled promise rejections
- Null or undefined dereferences that are not guarded
- Incorrect error handling
- State management bugs and stale closures
- Data loss or corruption scenarios
- Security issues
- API contract mismatches
- Resource leaks

For each bug found, report:

1. Exact file and line numbers
2. One-line summary
3. Details explaining why it is a bug and what can go wrong
4. Severity: critical, high, medium, or low
5. Suggested fix

If no bugs are found, say so explicitly. Do not fabricate issues. Only report findings you are confident are actual bugs.
