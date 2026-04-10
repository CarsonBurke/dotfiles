---
name: make-secure
description: Review changed code for security vulnerabilities and fix them. Operates on the current git diff or a provided path.
---

# Make Secure

Use this skill when the user wants to harden changed code against security vulnerabilities.

- Review files in the current git diff (or a provided path) for security vulnerabilities.
- Fix what you find. This is an action skill, not a review skill.
- Examples: injection, auth gaps, data exposure, unsafe deserialization, path traversal, insecure defaults — but use good judgement.
