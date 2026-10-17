---
name: pr-report
description: Create a reviewer-oriented, self-contained HTML evidence report for a pull request, merge request, branch, or proposed change set, choosing matched screenshots, focused code or schema excerpts, API/CLI examples, tests, migrations, or benchmarks according to the changes. Use when the user asks for a PR report, HTML review handoff, before/after change walkthrough, visual comparison, or evidence pack; do not use for a defect-hunting review, approval decision, PR-description update, or generic chronological change report.
---

# PR Report

Produce an evidence pack that helps a reviewer understand and verify the change. Remain read-only except for the requested report and temporary capture artifacts; never approve, comment, push, or modify source as part of this skill. Use `review-pr` for readiness or defect hunting, `update-pr` for published metadata, and `html-change-report` for a general timeline or inventory.

## Establish the exact change set

1. Honor an explicit PR/MR, branch, base, or revision range. Otherwise resolve the current branch's PR/MR when one exists.
2. For a hosted PR/MR, compare its actual base merge-base through the current remote head SHA, not local `HEAD`. Re-read the remote head immediately before final validation and regenerate stale evidence if it moved.
3. Default to the hosted change only. Disclose and exclude divergent local commits and staged, unstaged, or untracked files unless the user explicitly includes them.
4. Record repository, PR/MR link, base and head SHAs, generated time and timezone, worktree state, and any inferred scope.
5. Read the full patch and relevant surrounding code. Use commit messages, ticket text, reviews, and checks only as supporting context.

## Choose evidence by claim

Group the report by outcomes or reviewer questions, not by filename. Give each material claim the smallest evidence that can actually prove it.

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

- Do not force screenshots onto non-visual changes or use them as decoration.
- Do not claim a screenshot proves cursor size, hit targets, focus order, timing, accessibility semantics, or other invisible behavior. Use DOM inspection or tests and state the limitation.
- Keep code excerpts narrow enough to review, usually 8–30 lines. Label each with path, revision, and purpose; prefer a readable before/after pair over a raw full diff.
- Include a compact coverage matrix mapping every material changed behavior or state to its evidence or an explicit gap. Do not let attractive evidence for one path imply coverage of all paths.
- Use tables only for real mappings or comparisons. Keep large diffs, generated files, lockfiles, and noisy logs out of the main narrative.
- Sanitize secrets, credentials, user content, identifiers, URLs containing private data, authenticated content, and incidental local identity such as usernames in absolute paths before embedding it.

## Capture UI evidence

When screenshots are material:

1. Render the base and head revisions in isolated exact-revision worktrees with the same harness, state, inputs, viewport, device scale, theme, locale, direction, and dependency lockfile for each revision. Never switch or clean the user's checkout.
2. Prefer an existing Storybook/example/test surface. Do not add source stories or fixtures merely to capture evidence unless the user separately authorizes that change; keep screenshot-only harnesses temporary and outside the report's source diff. Do not launch Electron or another heavyweight client when a smaller faithful surface exists.
3. Exercise every changed visual component or state, including dark/light, responsive, RTL, hover, focus, disabled, loading, error, or animation states only when relevant to the patch.
4. For transitions, make the capture deterministic: use an explicit interaction, controlled duration, and matched animation time. Retain enough capture metadata to substantiate any timing claim.
5. Treat a pixel-identical result as useful regression evidence when the implementation is intended to preserve appearance; explain why there is no visible delta.
6. Validate the rendered DOM and computed state when the visual alone cannot prove the claim.

Run base and head from separate ports or static builds and verify which revision each rendered page serves. Do not let a shared dev server, stale bundle, symlink, or hot reload make both sides render the same source.

Use a dedicated background browser window, never focus it, and close the exact targets created for the report.

## Build the HTML

Prefer the structured renderer for normal reports. Read `references/specification.md`, copy `assets/spec.example.json` to a temporary file, populate only verified evidence, then run:

```bash
scripts/render_report.py SPEC.json REPORT.html --asset-root PATH
```

The renderer HTML-escapes repository-derived content, validates link schemes, creates variable-length evidence and coverage sections, and embeds local screenshot assets. Edit `assets/report-template.html` directly only when the report needs a layout the renderer cannot express. The report should normally contain:

- outcome and exact scope;
- a short reviewer-oriented summary;
- one comparison/evidence section per logical change group;
- a compact evidence coverage matrix with explicit omissions;
- validation results and their direct evidence;
- known risks, observed issues, unresolved questions, and follow-ups;
- provenance with verified repository, PR/MR, commit, ticket, and check links.

Use semantic HTML, embedded CSS, accessible contrast and focus states, responsive layouts, and print styles. Prefer no JavaScript. Make before/after labels explicit rather than relying on color. For evidence:

- use `<figure>` and descriptive `alt` text for screenshots;
- use `<pre><code>` with escaped source for code excerpts;
- use tables for payloads, schemas, compatibility, or measured comparisons;
- use open `<details>` only when supplemental evidence should remain visible in print.

Create a single portable HTML file. Keep external URLs as verified hyperlinks only—never runtime dependencies. The structured renderer embeds local images automatically; after a manual template edit, run `scripts/embed_local_images.py SOURCE OUTPUT`. Honor an explicit output path; otherwise prefer an existing repository-approved ignored report directory, and fall back to a unique temporary path rather than polluting source.

## Validate and hand off

Before returning the report:

1. Reconcile every SHA, count, path, snippet, screenshot label, test result, and claim against the raw diff and artifacts.
2. Confirm there are no template tokens, missing or duplicated evidence items, external runtime assets, unsafe links, or accidentally embedded sensitive data.
3. Validate the standalone file in an isolated background browser at desktop and narrow widths. Check loaded assets, anchor navigation, horizontal overflow, focus visibility, and representative evidence sections.
4. Emulate print media and verify contrast, page breaks, table/code overflow, and visibility of supplemental evidence.
5. Confirm code blocks and tables do not overflow, every embedded image matches its source artifact, and the standalone report still works after temporary capture assets are removed.
6. When subagents are available, give an independent reviewer the report and raw change scope—not suspected answers—and have it audit accuracy, omissions, accessibility, and misleading evidence.
7. Report checks as passed only from direct current evidence. A green report is not a PR approval and must not conceal known issues, blockers, or validation gaps.

Return one clickable absolute path to the HTML, the selected base/head scope, and only material caveats. Do not open or foreground the report unless the user requests it.
