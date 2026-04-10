---
name: find-bugs
description: Analyze multiple codebase domains for bugs using parallel subagents, then write the results to FOUND_ISSUES.md.
---

# Find Bugs

Use this skill when the user wants a broad bug sweep across multiple codebase domains.

## Workflow

1. Launch one read-only subagent per domain in parallel. Prefer `explorer` agents for this.
2. Pass each subagent:

```text
Domain: {domain}
Paths: {paths}
```

3. Ask each subagent to inspect only its assigned paths and report only confident, actual bugs with:
   - exact file and line numbers
   - one-line summary
   - details
   - severity
   - suggested fix
4. Gather all findings and write them to `./FOUND_ISSUES.md`.

If the user provides domains, use those. Otherwise, auto-discover domains by scanning the project structure:

1. Look for a monorepo layout (e.g. `packages/`, `apps/`, `libs/`, `services/`, `modules/`).
2. If found, treat each immediate subdirectory as a domain.
3. If the project is not a monorepo, split by top-level source directories (e.g. `src/api`, `src/ui`, `src/core`).
4. If the structure is flat or ambiguous, treat the entire `src/` (or project root) as a single domain.

## FOUND_ISSUES.md Format

Write the file in exactly this structure:

```markdown
# Found Issues

_Generated on {date}_

## Summary

- **Total issues found:** {count}
- **Critical:** {count} | **High:** {count} | **Medium:** {count} | **Low:** {count}

---

## Issues

### Issue {n}: {summary}

- **Domain:** {domain}
- **Severity:** {severity}
- **File(s):** `{file}:{line}`
- **Details:** {details}
- **Suggested fix:** {fix}
- **Status:** Pending

---
```

Rules:

- Number issues sequentially starting at 1.
- Keep the six fields in that exact order.
- Keep `- **Status:** Pending` as the last field.
- Follow every issue block with `---`.
- Do not add extra fields or sub-bullets.

If no bugs are found, write that clearly to the file and stop.

In the final response, summarize issue counts by domain and severity and mention that `FOUND_ISSUES.md` was written.
