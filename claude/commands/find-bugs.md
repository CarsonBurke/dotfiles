---
allowed-tools: Task(find-domain-bugs), Read, Write
description: Analyze codebase domains for bugs using parallel Opus subagents, write results to FOUND_ISSUES.md.
---

# Find Bugs

You are a bug-finding coordinator. Your job is to analyze the codebase across multiple domains, surface potential bugs, and write them to `./FOUND_ISSUES.md`.

## Phase 1: Parallel Domain Analysis

Launch one `find-domain-bugs` subagent via the Task tool (`subagent_type=find-domain-bugs`) for **each** domain listed below. Run them all **in parallel** (a single message with multiple Task tool calls).

### Domains

If the user provides domains via `$ARGUMENTS`, use those. Otherwise, auto-discover domains by scanning the project structure:

1. Look for a monorepo layout (e.g. `packages/`, `apps/`, `libs/`, `services/`, `modules/`).
2. If found, treat each immediate subdirectory as a domain.
3. If the project is not a monorepo, split by top-level source directories (e.g. `src/api`, `src/ui`, `src/core`).
4. If the structure is flat or ambiguous, treat the entire `src/` (or project root) as a single domain.

### Agent Prompt

Pass each agent a prompt with the domain and paths:

```
Domain: {domain}
Paths: {paths}
```

The `find-domain-bugs` agent already knows the full bug-hunting workflow. You only need to provide the domain and paths.

## Phase 2: Write FOUND_ISSUES.md

After all subagents complete, gather their results and write `./FOUND_ISSUES.md`.

**IMPORTANT:** The format below is a strict contract. Do NOT deviate from the exact field names, ordering, and markdown structure.

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

Print a summary of how many issues were found per domain and per severity level.

