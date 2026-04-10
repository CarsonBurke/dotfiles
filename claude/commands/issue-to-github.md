---
allowed-tools: Bash(gh issue create:*), Bash(gh issue list:*), Bash(gh label create:*), Read, Grep, Glob
description: Create a GitHub issue from a described problem or infer one from context.
argument-hint: [description of the problem]
---

# Issue to GitHub

You create a single GitHub issue from either an explicit problem description or by inferring the problem from surrounding context (recent errors, code smells, failing tests, etc.).

## Input

User arguments: $ARGUMENTS

- If arguments describe a problem, use that as the basis.
- If arguments are empty or vague, infer the problem from context: check recent terminal output, open files, git diff, or the current conversation for clues about what's wrong.

## Steps

### 1. Understand the Problem

Gather enough context to write a clear issue:

- **What** is broken or missing
- **Where** in the codebase (file paths, line numbers)
- **How** to reproduce or observe it (if applicable)
- **Why** it matters (impact, severity)

If the problem references specific files, read them to confirm the issue and get exact locations.

### 2. Check for Duplicates

```bash
gh issue list --search "<keywords>" --state open --limit 10
```

If a matching open issue already exists, report it to the user and stop.

### 3. Determine Labels

Always apply `bug` if it's a defect, or `enhancement` if it's a feature gap.

Pick a priority label based on severity:

| Severity | Label |
|-|-|
| Low | `priority: low` |
| Medium | `priority: medium` |
| High | `priority: high` |
| Critical | `priority: critical` |

Create any labels that don't already exist before applying them.

### 4. Create the Issue

```bash
gh issue create \
  --title "<concise title>" \
  --body "<body>" \
  --label "<label1>,<label2>"
```

Body format:

```markdown
## Description

<Clear description of the problem>

## Location

- **File(s):** `<file>:<line>`

## Steps to Reproduce

<If applicable>

## Expected vs Actual Behavior

<What should happen vs what happens>

## Suggested Fix

<If you have one>
```

Omit sections that don't apply (e.g. skip "Steps to Reproduce" for code-level bugs that are obvious from the file).

### 5. Output

Print the created issue URL and a one-line summary.
