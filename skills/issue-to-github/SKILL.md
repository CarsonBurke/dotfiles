---
name: issue-to-github
description: Create a single GitHub issue from a described problem or infer one from context.
---

# Issue to GitHub

Create a single GitHub issue from either an explicit problem description or by inferring the problem from surrounding context (recent errors, code smells, failing tests, conversation clues).

## Workflow

1. **Understand the problem** — Use the description if provided, otherwise infer from context (terminal output, open files, git diff). Read relevant files to get exact locations.
2. **Check for duplicates** — `gh issue list --search "<keywords>" --state open --limit 10`. Stop if a match exists.
3. **Determine labels** — `bug` or `enhancement`, plus a priority label (`priority: low/medium/high/critical`). Create missing labels first.
4. **Create the issue** — `gh issue create` with title, structured body (Description, Location, Steps to Reproduce, Expected vs Actual, Suggested Fix — omit sections that don't apply), and labels.
5. **Output** — Print the issue URL and a one-line summary.
