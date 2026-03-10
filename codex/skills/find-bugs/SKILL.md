---
name: find-bugs
description: Analyze multiple codebase domains for bugs using parallel subagents, then write the results to FOUND_ISSUES.md.
metadata:
  short-description: Parallel bug hunt across domains
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

Use these default domains unless the user provides overrides:

1. electron-core: `packages/electron-core`
2. electron-client: `packages/electron-client`
3. claws: `packages/claws` and `packages/claws-shared`
4. axes: `packages/axes`
5. web: `packages/web`
6. common business logic: `packages/common`
7. common and schemas: `packages/public-schemas`, `packages/private-schemas`, `packages/electron-client-common`
8. backend service: `packages/w-brazil`
9. workflow library: `packages/workflow`
10. shared ui: `packages/ui`
11. extension: `packages/extension`
12. migration library: `packages/drifti`
13. otel library: `packages/otel`
14. electron-bootstrap: `packages/electron-bootstrap`

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
