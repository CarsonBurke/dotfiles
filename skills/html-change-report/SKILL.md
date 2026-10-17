---
name: html-change-report
description: Create a polished, self-contained HTML report of repository changes across a user-specified or context-inferred revision or time range.
---

# HTML Change Report

The report is an evidence-grounded account of what changed, for someone who wasn't watching. Stay read-only apart from the report itself.

## Scope

- Use the date, revision, branch, PR, or baseline the user gives. Otherwise choose the scope the context best supports: a task or pre-push baseline actually recorded in the conversation, then the merge-base of a PR or branch with its real base, then the working-tree delta.
- "Changes we just made" means the task's baseline through the current worktree, not dirty changes that predate the task.
- Don't reconstruct a baseline from the reflog, invent a recent-hours window, or infer authorship from the current Git identity.
- When one scope is clearly supported, use it, and state the repository, range, and working-tree layers you chose and why. Ask only when plausible scopes would give materially different results.
- Read the log and full diff rather than trusting commit messages, and keep committed, staged, unstaged, and untracked changes distinct.
- Use a calendar window only when the request or conversation anchors one, and then name the timestamp used (author or committer), the timezone, and whether the boundaries are inclusive. When the selected commits aren't contiguous, present them as activity rather than a net change, since diffing the endpoints would include commits outside the window. Filter commits by the chosen timestamp, apply the window to checked-out history unless the user names other refs, and show a net effect only when a meaningful contiguous baseline and endpoint exist. Uncommitted changes have no reliable timestamp.

Record the exact boundaries, repository, worktree, and generation time in the report. Pick a unique output name unless given one, and leave the report itself out of the change set.

## Evidence

Git objects and the working tree are authoritative. Hosting metadata, tickets, and the conversation supply links and rationale. Report a check as passed only from direct evidence, and keep secrets, credentials, and private diff content out.

## Report

Start from [assets/report-template.html](assets/report-template.html), adapting or deleting sections rather than keeping irrelevant placeholders. Make it a single portable file with embedded CSS, accessible contrast and focus states, and responsive and print layouts that work without JavaScript, with no CDNs or external runtime dependencies.

In rough order of priority:

- the outcome and its visible effect;
- the scope and any inferred assumptions;
- logical change groups with brief before-and-after explanations;
- a commit timeline and per-file impact, when they help review;
- validation, risks, unresolved items, and follow-ups;
- provenance, with verified repository, commit, PR, or ticket links.

Raw diffs, large lockfiles, and generated noise stay out of the narrative. Label metrics as net deltas or chronological activity, and don't add up counts that aren't comparable.

Escape repository-derived text for its context. Repository-derived external links may use only verified `https:` or `http:` targets; drop other schemes rather than escaping them. In-page anchors and intentional relative links are fine. Leave no template tokens behind.

## Validate

Reconcile every count, SHA, date, file, and claim against the range, and check that each summary statement holds for every item it covers, splitting groups that don't share one rationale. When tooling allows, check the file in an isolated background browser without focusing it, covering desktop and narrow layouts, navigation, links, overflow, console errors, and print, then close the window. Otherwise run the structural checks you can and say so.

Return a clickable absolute path to the report, the scope, and any material caveat. Don't open the report for the user unless asked.
