---
name: find-typos
description: Scan user-facing strings for typos, report or fix them in a single PR.
---

# Find Typos

Scan user-facing strings across the project for typos, report them, and optionally fix them in a single PR.

## Arguments

- `--domain PATH` — Restrict scan to a specific directory or package (default: all)
- `--dry-run` — List typos without fixing; no branch, no PR

## Workflow

### Phase 1: Discover Scan Targets

If `--domain` is provided, scan only that path. Otherwise auto-discover:
- Monorepo with `packages/`: scan each package separately.
- `src/` directory: scan it.
- Root-level docs: `README.md`, `CLAUDE.md`, `AGENTS.md`, `CONTRIBUTING.md`.
- Skip `node_modules/`, `vendor/`, `dist/`, `build/`, `.git/`.

### Phase 2: Parallel Scanning

Launch one agent per scan target in parallel. Each agent scans for:
- Misspelled words in JSX text, placeholders, titles, aria-labels, alt text, error messages, UI constants
- Doubled words ("the the"), inconsistent capitalization, grammar issues
- Documentation prose in .md/.mdx files

Ignoring: code identifiers, abbreviations, jargon, vendored code, template literals, CSS classes, URLs.

Output per finding: file, line, original text, suggested fix, confidence (high/medium).

### Phase 3: Report

Print a summary table (directory, typos found, high, medium) and full list of findings.

**If `--dry-run`: stop here.**

### Phase 4: Fix

Apply high-confidence fixes only using targeted edits. Run the project's formatter if available.

### Phase 5: PR

Create branch `chore/fix-typos`, commit, push, and open a PR with a summary of fixes.
