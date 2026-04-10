---
allowed-tools: Bash(git:*), Bash(gh pr:*), Read, Write, Edit, Glob, Grep, Agent
description: Scan user-facing strings for typos, report or fix them in a single PR.
argument-hint: [--domain <path>] [--dry-run]
---

# Find Typos

You are a typo-finding coordinator. Your job is to scan user-facing strings across the project for typos, report them, and optionally fix them in a single PR.

## Arguments

Parse `$ARGUMENTS` for these flags:

| Flag | Default | Description |
|-|-|-|
| `--domain PATH` | all | Restrict scan to a specific directory or package |
| `--dry-run` | `false` | List typos without fixing; no branch, no PR |

## Phase 1: Discover Scan Targets

If `--domain` is provided, scan only that path.

Otherwise, auto-discover directories to scan:

1. If a monorepo with a `packages/` directory, scan each package separately.
2. If a `src/` directory exists, scan it.
3. Also scan root-level documentation: `README.md`, `CLAUDE.md`, `AGENTS.md`, `CONTRIBUTING.md`, and similar.
4. Skip `node_modules/`, `vendor/`, `dist/`, `build/`, `.git/`, and other generated directories.

## Phase 2: Parallel Typo Scanning

Launch one agent per scan target. Run them all **in parallel** (a single message with multiple agent calls).

### Agent Prompt

Each agent receives the following prompt (fill in domain and paths):

```
You are scanning user-facing strings for typos in "{domain}".

Scan all files under: {paths}
File types to scan: .tsx, .ts, .jsx, .js for code; .md, .mdx for docs

## What to scan

1. **User-facing strings** in component/UI files:
   - JSX text content (`<p>Text here</p>`, `<Button>Label</Button>`)
   - String literals in `placeholder`, `title`, `aria-label`, `alt` attributes
   - Error messages shown to users (e.g. toast notifications, alert dialogs)
   - UI constants and label maps
2. **Documentation files**: scan prose content in .md/.mdx files

## What to look for

- Misspelled words
- Doubled words ("the the")
- Inconsistent capitalization in similar UI contexts
- Common grammar issues in short strings

## What to ignore (false positives)

- Code identifiers, variable names, function names, import paths
- Intentional abbreviations and technical jargon (API, URL, OAuth, SSO, etc.)
- Vendored/third-party code (node_modules/, vendor/, dist/)
- Template literals with complex interpolation
- CSS class names, Tailwind classes
- File paths and URLs

## Output format

Return your findings as a structured list. For each typo found:

- **File:** relative file path
- **Line:** line number
- **Original:** the text containing the typo (quote the relevant fragment)
- **Suggested fix:** the corrected text
- **Confidence:** high or medium

Only report findings you are genuinely confident about. Do NOT fabricate typos. If you find nothing, say "No typos found."

Final response under 2000 characters. List outcomes, not process.
```

## Phase 3: Consolidate Report

After all agents complete, gather their results. Print a summary:

### Summary table

```
| Directory | Typos Found | High | Medium |
|-----------|-------------|------|--------|
| ...       | ...         | ...  | ...    |
| **Total** | **N**       | **N**| **N**  |
```

### Full list

For each typo found, print:

```
**{directory}** — `{file}:{line}`
  Original: "{original text}"
  Fix:      "{suggested fix}"
  Confidence: {high|medium}
```

**If `--dry-run` is set, stop here.** Print the report and exit.

## Phase 4: Fix Typos

For each typo with **high confidence**, apply the fix using the Edit tool. Read the file first, then make the targeted replacement.

Skip anything with medium confidence or where the fix is ambiguous — only fix clear, unambiguous typos.

After applying fixes, run the project's formatter if one exists (check for `format`, `fix`, or `lint:fix` scripts in `package.json`, or a `Makefile`/`justfile` target).

## Phase 5: Create PR

1. Create a branch: `chore/fix-typos`
2. Stage and commit fixes: `chore: fix typos in user-facing strings`
3. Push and open a PR with a summary of all fixes applied

## Final Output

Print a summary of what was done:
- How many typos were found per directory
- How many were fixed (high confidence) vs. skipped (medium confidence)
- The PR URL (if not `--dry-run`)
