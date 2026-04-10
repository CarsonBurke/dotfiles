---
allowed-tools: Bash(gh issue create:*), Bash(gh issue list:*), Bash(gh issue view:*), Bash(gh label create:*), Read, Grep, Glob, Agent
description: Validate bugs from FOUND_ISSUES.md and create GitHub issues for confirmed real bugs.
---

# Issues to GitHub

You are a bug validation coordinator. Your job is to read `./FOUND_ISSUES.md`, spawn agents to validate each issue, and create GitHub issues for confirmed real bugs.

## Phase 1: Parse FOUND_ISSUES.md

Read `./FOUND_ISSUES.md` and parse every issue block. Each issue follows this format:

```markdown
### Issue {n}: {summary}

- **Domain:** {domain}
- **Severity:** {severity}
- **File(s):** `{file}:{line}`
- **Details:** {details}
- **Suggested fix:** {fix}
- **Status:** {status}
```

Collect all issues into a list. **Only process issues whose status is `Pending` or starts with `Validated`.** Skip everything else — any issue with a status like "Created", "Not a bug", "Skipped", "Error", "Don't create", or anything other than `Pending`/`Validated` should be skipped.

## Phase 2: Spawn Validation Agents

For each pending issue, spawn an agent to validate whether it is a real bug and create a GitHub issue if confirmed. Process in batches of **5 parallel agents at a time**. Wait for each batch to complete before starting the next.

**CRITICAL**: You must start 5 **parallel** agents per batch, i.e. starting all of them in the same message.

### Agent Prompt

Each agent receives the issue details and instructions:

```
Validate this bug report and create a GitHub issue if confirmed.

Issue {n}: {summary}

- **Domain:** {domain}
- **Severity:** {severity}
- **File(s):** `{file}:{line}`
- **Details:** {details}
- **Suggested fix:** {fix}

## Validation Steps

1. Read the file(s) listed and confirm the bug exists at or near the specified location.
2. Assess whether this is a real bug (not a false positive, intentional behavior, or already fixed).
3. Check if a GitHub issue already exists for this bug: `gh issue list --search "<summary keywords>" --state open --limit 5`

## If Confirmed

Create a GitHub issue:

gh issue create --title "<concise title>" --body "<body>" --label "<labels>"

Body format:
- **File(s):** `{file}:{line}`
- **Details:** {details}
- **Suggested fix:** {fix}

Return: CONFIRMED — <github issue URL>

## If Not a Bug

Return: REJECTED — <reason>

## If Error

Return: ERROR — <description>
```

### Labels

When passing data to each agent, determine which labels should be applied. The agent always applies `bug`. Also determine a **priority label** based on severity:

| Severity | Label |
|-|-|
| Low | `priority: low` |
| Medium | `priority: medium` |
| High | `priority: high` |
| Critical | `priority: critical` |

Add any applicable **category labels** based on domain/details. Common examples:

| Label | When to apply |
|-|-|
| `ci` | Issue relates to CI/CD workflows |
| `dependencies` | Issue relates to dependency versions or packages |
| `deploy` | Issue relates to deployment or release pipelines |
| `enhancement` | The fix would also improve existing behavior |
| `refactor` | The bug stems from code needing structural refactoring |

Append labels to the agent prompt:

```
- **Labels:** `bug`, `priority: {mapped}`, `{category1}`, ...
```

If no category labels apply, just pass `bug` and the priority label. Instruct the agent to create any missing labels before applying them.

### Handling Errors

After each batch completes, check if **any** agent returned an `ERROR` verdict. If so, **stop immediately** — do not process further batches. Report the error in the final output.

## Phase 3: Update FOUND_ISSUES.md

After all batches complete, update the `**Status:**` field of each processed issue in `FOUND_ISSUES.md`:

- Confirmed: `Created — <issue URL>`
- Rejected: `Not a bug — <reason>`
- Error: `Error — <description>`

## Final Output

Print a summary:

- Total issues processed
- Confirmed bugs (with GitHub issue links)
- Rejected (not real bugs)
- Errors
- Skipped (non-pending status)
