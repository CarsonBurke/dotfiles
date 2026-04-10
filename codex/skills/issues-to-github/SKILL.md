---
name: issues-to-github
description: Validate bugs from FOUND_ISSUES.md and create GitHub issues for confirmed real bugs.
---

# Issues to GitHub

Read `./FOUND_ISSUES.md`, validate each bug report, and create GitHub issues for confirmed real bugs.

## Workflow

### Phase 1: Parse FOUND_ISSUES.md

Read `./FOUND_ISSUES.md` and parse every issue block matching this format:

```markdown
### Issue {n}: {summary}

- **Domain:** {domain}
- **Severity:** {severity}
- **File(s):** `{file}:{line}`
- **Details:** {details}
- **Suggested fix:** {fix}
- **Status:** {status}
```

Only process issues with status `Pending` or starting with `Validated`. Skip all others.

### Phase 2: Validate and Create Issues

Process in batches of 5 parallel agents. Each agent:

1. Reads the file(s) listed and confirms the bug exists.
2. Checks for existing GitHub issues: `gh issue list --search "<keywords>" --state open --limit 5`
3. If confirmed: creates a GitHub issue with appropriate labels (`bug`, priority label, optional category labels). Returns `CONFIRMED — <url>`.
4. If not a bug: returns `REJECTED — <reason>`.

Priority labels based on severity: `priority: low`, `priority: medium`, `priority: high`, `priority: critical`.

Stop immediately if any agent returns `ERROR`.

### Phase 3: Update FOUND_ISSUES.md

Update each processed issue's `**Status:**` field:
- Confirmed: `Created — <issue URL>`
- Rejected: `Not a bug — <reason>`
- Error: `Error — <description>`

### Final Output

Summary: total processed, confirmed (with links), rejected, errors, skipped.
