---
name: pr-report
description: Use when asked for a PR report, an HTML review handoff, a before/after walkthrough, a visual comparison, or an evidence pack for a pull request, merge request, branch, or proposed change set. Not for hunting defects, approving, updating the PR description, or a chronological change report.
---

# PR Report

An evidence pack that helps a reviewer understand and verify a change. Stay read-only except for the report and temporary capture artifacts, so no approving, commenting, pushing, or editing source. Use `review-deep` for readiness or defect hunting, `commits-push-pr` for the PR's description, and `html-change-report` for a general timeline.

## Change set

- Use the PR or MR, branch, base, or range the user gives, and otherwise the current branch's PR if there is one.
- For a hosted PR, compare the merge-base with its actual base through the current remote head SHA, not local `HEAD`. Re-read the remote head before final validation so the evidence isn't stale.
- Cover the hosted change only, mentioning divergent local commits and uncommitted files rather than including them unless asked.
- Record the repository, PR link, full base and head SHAs, generation time, and any inferred scope. When the report spans several revisions, show each full SHA at least once; abbreviations are fine elsewhere.
- Read the full patch and the code around it. Commit messages, tickets, and reviews are supporting context, not evidence.

## Evidence

Organize by outcome or reviewer question rather than by file, and give each material claim the smallest evidence that actually proves it:

| Change | Preferred evidence |
| --- | --- |
| Rendered UI, layout, theming, interaction | Matched before/after screenshots or short state sequence |
| Backend logic, algorithms, error handling | Focused escaped code excerpts plus a test, trace, or worked example |
| API, schema, serialization, compatibility | Before/after types or payload shapes, compatibility table, representative sanitized request/response |
| Database or migration | Schema/query excerpt, migration direction, invariants, and rollback or compatibility evidence |
| CLI, build, CI, configuration | Focused config/code excerpt and relevant command output |
| Performance | Comparable benchmark results with method, workload, and uncertainty |
| Security, privacy, or authorization | Sanitized data-flow or boundary explanation and focused enforcement code/tests |
| Refactor intended to preserve behavior | Before/after implementation excerpt plus parity tests or a pixel/result equality check |

- Before choosing evidence, list every material rendered UI change from the base to the final included candidate and map each to matched screenshots or an explicit gap. In grouped scopes, a semantic (non-visual) local overlay doesn't erase a visual change already in the hosted patch.
- Don't force screenshots onto non-visual changes or use them as decoration.
- Screenshots prove what's visible, not cursor size, hit targets, focus order, timing, or accessibility semantics. Use DOM inspection or tests for those and say what a screenshot can't show.
- Keep code excerpts reviewable, usually 8 to 30 lines, each labeled with path, revision, and purpose, and prefer a before/after pair to a raw diff.
- Never splice noncontiguous source into what reads as one excerpt. Use separate panels or an explicit omission marker with source ranges, and resume at a complete syntax boundary.
- Include a compact coverage matrix mapping every material changed behavior to its evidence or an explicit gap, so strong evidence for one path doesn't imply coverage of the rest.
- Every aggregate count must be derivable from named evidence rows or artifacts, so don't mix ticket, review, test, and correction counts into an unsupported completeness claim.
- Sanitize secrets, user content, private URLs, and incidental local identity such as usernames in absolute paths.

## Screenshots

- Render the base and the final included candidate from isolated worktrees with the same harness, state, inputs, viewport, scale, theme, locale, and lockfile, without switching or cleaning the user's checkout. Pin committed sources to full SHAs. When included uncommitted changes affect a capture, also record the pinned `HEAD`, a checksum of the exact binary-capable overlay patch, and the included files so the state is reproducible.
- For grouped scopes, compare the common base with each material final candidate, not only the last local overlay.
- Serve them from separate ports or static builds and check which revision each page actually shows, since a shared dev server or hot reload can make both sides render the same source. Bind ports strictly where possible and confirm provenance from process output or a revision marker rather than TCP readiness, since another process may already own the port.
- Record the exact source-state identifier, viewport, scale, theme, locale, fixture, and interaction state for each capture, and match the content framing as well as the viewport so fixed headers or different page heights don't skew the comparison.
- Prefer an existing Storybook, example, or test surface to launching Electron or another heavy client. Keep any screenshot-only harness temporary and out of the source diff unless the user authorizes adding it.
- Capture each changed visual state, including theme, responsive, RTL, hover, focus, disabled, loading, or error states when the patch touches them.
- Make transitions deterministic with an explicit interaction and matched animation time, and keep enough metadata to support any timing claim.
- A pixel-identical result is good evidence when the change is meant to preserve appearance, as long as the report says why there's no visible delta.
- Use a dedicated background browser window, never focus it, and close the targets you created.

## Build

Use the structured renderer unless the report needs a layout it can't express. Read `references/specification.md`, copy `assets/spec.example.json` to a temporary file, fill in only verified evidence, and run:

```bash
scripts/render_report.py SPEC.json REPORT.html --asset-root PATH
```

The renderer escapes repository-derived content, validates link schemes, and embeds local screenshots. If you edit `assets/report-template.html` directly instead, embed images afterward with `scripts/embed_local_images.py SOURCE OUTPUT`.

The report usually holds the outcome and exact scope, a short summary for the reviewer, one evidence section per logical change group, the coverage matrix, validation results, known risks and open questions, and verified provenance links. It should be one portable HTML file with embedded CSS and no runtime dependencies, readable in print, with descriptive alt text on screenshots and before and after labels that don't rely on color alone. Honor an explicit output path; otherwise use an existing ignored report directory or a unique temporary path rather than the source tree.

## Validate

- Reconcile every SHA, count, path, snippet, label, and test result against the diff and artifacts, and check that every embedded image matches its source artifact.
- Check for leftover template tokens, missing or duplicated evidence, external assets, unsafe links, embedded sensitive data, and a heading outline that skips levels.
- Open the file in an isolated background browser at desktop and narrow widths and in print emulation, checking assets, anchors, overflow, focus visibility, and page breaks. Confirm it still works after the temporary capture assets are deleted.
- When subagents are available, have an independent reviewer audit the report against the raw change scope, without your suspicions, for accuracy, omissions, and misleading evidence.

Report checks as passed only from direct current evidence. A clean report isn't an approval and mustn't hide known issues, blockers, or validation gaps. Return one clickable absolute path, the base and head scope, and material caveats, and don't open the report unless asked.
