---
name: update-pr
description: Update the GitHub pull request title and description for the current branch by diffing against the merge-base (not the main branch tip).
---

Update the title and description of the open GitHub PR for the current branch.

Do NOT use dollar-parenthesis command substitution in bash, use backtick command substitution instead.

Use exactly "git diff `git merge-base main HEAD`..HEAD" to get the changes introduced in this branch.
Use exactly "git log `git merge-base main HEAD`..HEAD --oneline --no-merges" to list the commits.

Use `gh pr view --json number,title,body` to get the current PR. If no PR exists, stop and tell the user.

## Title

Use Conventional Commits format: `<type>(<optional scope>): <description>`

Types: feat, fix, refactor, chore, docs, style, perf, test, revert.

Rules:
- Lowercase type and description, imperative present tense ("add", not "added")
- No trailing period, under 70 characters
- Scope is optional but encouraged when change is specific to a package/area
- Append `!` before the colon for breaking changes

## Description

- Explain **why** the change was made, not just what — the diff shows the "what"
- Contrast new vs previous behavior when it aids understanding
- Imperative present tense, simple and direct — a few sentences or short paragraph
- Use a bullet list if there are multiple logical changes
- No heavy markdown structure (no `## Headings`), but inline markdown is fine
- If the branch name contains a Linear issue ID (e.g. `MAIN-1234`), include `Fixes MAIN-1234` at the end

Update the PR with `gh pr edit <number> --title "..." --body "..."`.
