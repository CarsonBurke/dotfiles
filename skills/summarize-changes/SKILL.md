---
name: summarize-changes
description: Summarize repository changes over a user-specified or context-inferred revision or time range, with verified links when available.
---

# Summarize Changes

Remain read-only. Honor an explicit date, revision, branch, PR, or baseline. Otherwise infer the strongest defensible scope from the task context and repository state: prefer a task or pre-push baseline actually recorded in context, then a PR's merge-base with its actual base or a branch merge-base, then the current working-tree delta. Do not reconstruct a supposedly known baseline from reflog, invent a recent-hours window, or substitute a merge-base for a known incremental baseline. Ask only when plausible scopes would materially change the summary.

State the selected repository, range, working-tree layers, and why that scope was chosen. Inspect the log and full diff rather than trusting commit messages. Keep committed, staged, unstaged, and untracked changes distinct. Apply calendar scopes to checked-out history unless the user requests other refs; name the author or committer timestamp, timezone, and boundaries, and treat non-contiguous selected commits as activity rather than claiming a net delta.

Summarize outcomes, important implementation changes, validation, and unresolved risk concisely. Use verified commit, PR, or compare links when available: link one commit to its commit page and a contiguous multi-commit range to the repository compare view only after verifying both endpoints exist in that GitHub repository. Never claim an exact incremental range or test result without evidence.
