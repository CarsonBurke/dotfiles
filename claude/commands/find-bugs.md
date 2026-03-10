---
allowed-tools: Task(find-domain-bugs), Read, Write
description: Analyze codebase domains for bugs using parallel Opus subagents, write results to FOUND_ISSUES.md.
---

# Find Bugs

You are a bug-finding coordinator. Your job is to analyze the codebase across multiple domains, surface potential bugs, and write them to `./FOUND_ISSUES.md`.

## Phase 1: Parallel Domain Analysis

Launch one `find-domain-bugs` subagent via the Task tool (`subagent_type=find-domain-bugs`) for **each** domain listed below. Run them all **in parallel** (a single message with multiple Task tool calls).

### Domains

Use the following default domains unless the user provides overrides via `$ARGUMENTS`:

1. **electron-core** — `packages/electron-core` (main process backend logic)
2. **electron-client** — `packages/electron-client` (renderer SPA, React components)
3. **claws** — `packages/claws` and `packages/claws-shared` (data broker integrations)
4. **axes** — `packages/axes` (service integrations)
5. **web** — `packages/web` (marketing/checkout/account site)
6. **common business logic** - `packages/common`
7. **common & schemas** — `packages/public-schemas`, `packages/private-schemas`, `packages/electron-client-common`
8. **backend service** — `packages/w-brazil` (cloudflare worker)
9. **workflow library** - `packages/workflow`
10. **shared ui** - `packages/ui`
11. **extension** — `packages/extension`
12. **migration library** — `packages/drifti`
13. **otel library** — `packages/otel`
14. **electron-bootstrap** — `packages/electron-bootstrap` (loads electron-core, critical for launching the app)

### Agent Prompt

Pass each agent a prompt with the domain and paths:

```
Domain: {domain}
Paths: {paths}
```

The `find-domain-bugs` agent already knows the full bug-hunting workflow. You only need to provide the domain and paths.

## Phase 2: Write FOUND_ISSUES.md

After all subagents complete, gather their results and write `./FOUND_ISSUES.md`.

**IMPORTANT:** The format below is a strict contract. Downstream tooling (`/issues-to-github` and `scripts/change-issue-status.ts`) parses this file with regex and depends on the exact field names, ordering, and markdown structure. Do NOT deviate from it.

### File structure

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

### Format rules

- `{n}` is a sequential integer starting at 1, with no gaps.
- Each issue heading MUST be `### Issue {n}: {summary}` — the number and colon are required.
- Each issue MUST have exactly the six bullet fields shown above, in that exact order, with those exact bold labels.
- `- **Status:** Pending` MUST be the last field of every issue. Do not use any other initial status value.
- Each issue block MUST be followed by a `---` horizontal rule.
- Do not add extra fields, blank bullets, or sub-bullets within an issue block.

If no bugs are found across all domains, write that to the file and stop.

## Final Output

Print a summary of how many issues were found per domain and per severity level. Remind the user they can run `/issues-to-github` to validate and create GitHub issues from the results.

