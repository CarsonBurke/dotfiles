---
name: commits-push-pr
description: Commit all current changes, push the branch, and create or reuse its GitHub pull request.
---

# Commits Push PR

1. Follow `commits`, but check GitHub before pushing. Reuse an open PR and stop on a closed or merged PR unless the user wants a new branch or PR.
2. Use an existing PR's actual base; otherwise use the repository default branch. Inspect that diff, the PR template, and known validation.
3. Follow the safe push steps from `commits-push`.
4. When creating a PR, preserve required template sections and pass title, body, head, and base as data in a temporary JSON request to `gh api --input`. Never interpolate generated text into a shell command.
5. Verify and report the PR URL, head/base, and commit range.
