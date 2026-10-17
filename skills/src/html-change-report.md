---
name: html-change-report
description: Create a polished, self-contained HTML report of repository changes across a user-specified or context-inferred revision or time range.
---

# HTML Change Report

Create an evidence-grounded account of repository changes, not a decorative changelog. Remain read-only except for the requested report artifact; do not alter source, history, or remotes.

## Establish the scope

- Honor an explicit date, revision, branch, PR, or baseline first. Record exact boundaries, timezone, repository, worktree, and generated time.
- Interpret “changes we just made” or equivalent as the known task/session baseline through the current worktree. Do not attribute pre-existing dirty changes to the task.
- For a branch or PR, compare its actual base merge-base through `HEAD` and report relevant staged, unstaged, and untracked changes separately.
- Use a calendar filter only when the request or conversation supplies a temporal anchor. Choose author or committer time, state that choice with the timezone and inclusive/exclusive boundaries, and filter commits by that field. Treat a non-contiguous calendar selection as chronological activity; do not imply a net delta or diff earliest-to-latest when intervening commits fall outside the window. Present net effect only when a meaningful contiguous baseline and endpoint exist. Uncommitted changes have no reliable historical timestamp.
- If one scope is strongly supported, proceed and disclose the inference. Ask when plausible scopes would produce materially different reports. Never invent a recent-hours window or infer authorship from the current Git identity.
- Choose a unique output name unless the user supplies one, and exclude the report itself from the collected change set.

## Build the evidence

Inspect repository instructions, status, refs, upstream/default branch, commits, and full diffs. Treat Git objects and working-tree content as authoritative; use hosting metadata and ticket or conversation context for verified links and rationale. Read the actual patches rather than relying on commit messages.

Distinguish net effect from chronological activity, and distinguish committed, staged, unstaged, and untracked work. Account for renames, reversions, merges, binaries, submodules, generated files, and shallow history when relevant. Report tests or checks as passed only from direct evidence. Do not expose secrets, credentials, private diff content, or unnecessary personal data.

## Write the report

Start from [assets/report-template.html](assets/report-template.html), adapting or deleting sections rather than preserving irrelevant placeholders. Prefer a single portable HTML file with embedded CSS, semantic structure, accessible contrast and focus states, responsive and print layouts, and useful content without JavaScript. Avoid CDNs and external runtime dependencies.

Prioritize:

- outcome and user-visible effect;
- exact scope and inferred assumptions;
- logical change groups with concise before/after explanations;
- commit timeline and per-file impact when they aid review;
- validation, risks, unresolved items, and follow-ups;
- provenance and verified repository, commit, PR, or ticket links.

Keep raw diffs, large lockfiles, generated noise, and binary details out of the main narrative. Label metrics as net snapshot deltas or chronological activity, keep working-tree layers separate, and never aggregate incompatible counts. Apply context-aware text and attribute escaping. For repository-derived external links, allow only verified `https:` or `http:` targets; omit unsafe or unverified schemes rather than merely HTML-escaping them. Use locally generated relative links only when intentional. Do not leave template tokens in the result.

## Validate and hand off

Reconcile every count, SHA, date, file, and claim against the selected range. Ensure each aggregate characterization holds for every included item; split heterogeneous changes instead of forcing one rationale across them. Validate the artifact in an isolated background browser when tooling is available, without focusing or presenting that window to the user. Inspect desktop and narrow layouts, navigation, overflow, links, console errors, and print readability, then close the validation window. Otherwise perform available structural checks and state the limitation.

Return a clickable absolute path to the report plus the selected scope and any material caveat. Do not open or foreground it for the user unless requested.
