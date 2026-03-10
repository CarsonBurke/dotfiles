---
allowed-tools: Task(find-file-bugs), Bash, Read, Write
description: Randomly sample source files and scan each one for bugs using parallel Opus agents, write results to FOUND_ISSUES.md.
---

# Spot Check Bugs

You are a bug-finding coordinator. Your job is to randomly sample source files from the codebase, spawn one `find-file-bugs` agent per file in parallel, and write results to `./FOUND_ISSUES.md`.

## Phase 1: Select Random Files

Use Bash to find and randomly select files. Unless the user provides overrides via `$ARGUMENTS`, use these defaults:

- **Glob**: all `.ts` and `.tsx` files under `packages/`
- **Count**: 10 files

```bash
find packages -type f \( -name "*.ts" -o -name "*.tsx" \) \
  | grep -Ev '(node_modules|/dist/|\.d\.ts$|\.test\.|\.spec\.|__generated__)' \
  | shuf -n 10
```

If `$ARGUMENTS` supplies a glob pattern, a package path, or a count, adjust the command accordingly. For example:
- `packages/w-brazil/src/**/*.ts 5` → restrict the find path to `packages/w-brazil/src` and pick 5 files
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
- For `**Domain:**`, use the package name derived from the file path (e.g. `electron-core` for `packages/electron-core/...`).
- `- **Status:** Pending` MUST be the last field of every issue. Do not use any other initial status value.
- Each issue block MUST be followed by a `---` horizontal rule.
- Do not add extra fields, blank bullets, or sub-bullets within an issue block.

If no bugs are found across all files, write that to the file and stop.

## Final Output

Print a summary listing which files were scanned, how many issues were found per file, and a severity breakdown. Remind the user they can run `/validate-issues` or `/issues-to-github` to process the results.

