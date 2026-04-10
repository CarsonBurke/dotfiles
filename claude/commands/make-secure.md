---
name: make-secure
description: Review changed code for security vulnerabilities and fix them.
---

Review files in the current git diff for security vulnerabilities, then fix what you find. If `$ARGUMENTS` is a path, use that instead of the diff.

Examples: injection, auth gaps, data exposure, unsafe deserialization, path traversal, insecure defaults — but use good judgement.
