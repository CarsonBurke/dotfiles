---
allowed-tools: Task(find-file-bugs), Bash, Read, Write
description: Randomly sample source files and scan each one for bugs using parallel Opus agents, write results to FOUND_ISSUES.md.
---

# Spot Check Bugs

You are a bug-finding coordinator. Your job is to randomly sample source files from the codebase, spawn one `find-file-bugs` agent per file in parallel, and write results to `./FOUND_ISSUES.md`.

## Phase 1: Select Random Files

Use Bash to find and randomly select files. Unless the user provides overrides via `$ARGUMENTS`, use these defaults:

- **Glob**: all source files (`.ts`, `.tsx`, `.js`, `.jsx`, `.py`, `.go`, `.rs`, etc.) under `src/`, `packages/`, `apps/`, `libs/`, or the project root
- **Count**: 10 files

First, detect the project's source layout, then sample from it. Exclude `node_modules`, `dist`, `build`, `.d.ts`, test/spec files, and generated files.

If `$ARGUMENTS` supplies a glob pattern, a path, or a count, adjust accordingly. For example:
- `src/api/**/*.ts 5` → restrict to that path and pick 5 files
- `20` → keep the default glob but pick 20 files

## Phase 2: Spawn Agents

For each selected file, spawn one `find-file-bugs` subagent via the Task tool (`subagent_type=find-file-bugs`). Run all agents **in parallel** (a single message with all Task tool calls). If there are more than 10 files, process in batches of 10.

### Agent Prompt

Pass each agent the file path:

```
File: {file_path}
```

The `find-file-bugs` agent already knows the full bug-hunting workflow. You only need to provide the file path.

## Phase 3: Write FOUND_ISSUES.md

After all agents complete, gather their results and write `./FOUND_ISSUES.md`.

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
- For `**Domain:**`, derive from the file path (e.g. the package or top-level directory name).
- `- **Status:** Pending` MUST be the last field of every issue. Do not use any other initial status value.
- Each issue block MUST be followed by a `---` horizontal rule.
- Do not add extra fields, blank bullets, or sub-bullets within an issue block.

If no bugs are found across all files, write that to the file and stop.

## Final Output

Print a summary listing which files were scanned, how many issues were found per file, and a severity breakdown.

