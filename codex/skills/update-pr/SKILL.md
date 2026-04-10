---
name: update-pr
description: Update the GitHub pull request title and description for the current branch using the merge-base diff and Conventional Commits format.
---

# Update PR

Use this skill when the user wants to update the title and description of the open PR for the current branch.

- Use exactly ``git diff `git merge-base main HEAD`..HEAD`` to get introduced changes.
- Use exactly ``git log `git merge-base main HEAD`..HEAD --oneline --no-merges`` to list commits.
- Do not use `$()` command substitution in bash for these commands.
- Use `gh pr view --json number,title,body` to get the current PR. Stop if no PR exists.

## Title format

Conventional Commits: `<type>(<optional scope>): <description>`

Types: `feat`, `fix`, `refactor`, `chore`, `docs`, `style`, `perf`, `test`, `revert`. Lowercase, imperative present tense, no trailing period, under 70 chars. Scope optional but encouraged. Append `!` before `:` for breaking changes.

## Description format

- Explain **why**, not what — the diff shows the what.
- Contrast new vs previous behavior when helpful.
- Imperative present tense, a few sentences or short paragraph.
- Bullet list for multiple logical changes.
- No heavy markdown (no headings/tables), inline markdown is fine.
- Include `Fixes MAIN-1234` if the branch name contains a Linear issue ID.

Update with `gh pr edit <number> --title "..." --body "..."`.
