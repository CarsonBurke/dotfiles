---
name: spot-check-bugs
description: Randomly sample source files, inspect them for actual bugs with parallel subagents, and write the results to FOUND_ISSUES.md.
---

# Spot Check Bugs

Use this skill when the user wants a randomized bug-finding pass over sampled files.

## Workflow

1. Select random files with shell commands. Unless the user overrides it, detect the project's source layout (e.g. `src/`, `packages/`, `apps/`, `libs/`, or project root) and sample 10 source files, excluding `node_modules`, `dist`, `build`, declaration files, tests, specs, and generated files.
2. Spawn one read-only subagent per selected file in parallel. Prefer `explorer` agents.
3. Ask each subagent to inspect only its assigned file and report only confident, actual bugs with:
   - exact file and line numbers
   - one-line summary
   - details
   - severity
   - suggested fix
4. Gather all findings and write them to `./FOUND_ISSUES.md`.

Adapt the sampling command to the detected project layout. For example, in a monorepo with `packages/`:

```bash
find packages -type f \( -name "*.ts" -o -name "*.tsx" \) \
  | grep -Ev '(node_modules|/dist/|\.d\.ts$|\.test\.|\.spec\.|__generated__)' \
  | shuf -n 10
```

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
- Derive `Domain` from the package path when possible.
- Keep the six fields in that exact order.
- Keep `- **Status:** Pending` as the last field.
- Follow every issue block with `---`.
- Do not add extra fields or sub-bullets.

If no bugs are found, write that clearly to the file and stop.

In the final response, list which files were scanned, summarize issues per file and severity, and mention that `FOUND_ISSUES.md` was written.
