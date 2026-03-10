---
name: commits-push-pr
description: Create Conventional Commit commit(s) from the current diff, separated by concern, push them, and create a PR.
metadata:
  short-description: Commit, push, and open a PR
---

# Commits Push PR

Use this skill when the user wants commits, a push, and a PR.

- Create idiomatic Conventional Commit commit(s) from the current diff.
- Separate unrelated concerns into separate commits.
- Prefer no commit body, or a very short one only when needed.
- Do not add AI co-author lines.
- Push when done.
- Create a PR in the same style.
- Prefer no PR description, or a very short one only when needed.
