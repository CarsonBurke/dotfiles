---
name: summarize-changes
description: Summarize repository changes over a user-specified or context-inferred revision or time range, with verified links when available.
---

# Summarize Changes

Stay read-only.

- Use the date, revision, branch, PR, or baseline the user gives. Otherwise choose the scope the context best supports: a task or pre-push baseline actually recorded in the conversation, then the merge-base of a PR or branch with its real base, then the working-tree delta.
- "Changes we just made" means the task's baseline through the current worktree, not dirty changes that predate the task.
- Don't reconstruct a baseline from the reflog, invent a recent-hours window, or infer authorship from the current Git identity.
- When one scope is clearly supported, use it, and state the repository, range, and working-tree layers you chose and why. Ask only when plausible scopes would give materially different results.
- Read the log and full diff rather than trusting commit messages, and keep committed, staged, unstaged, and untracked changes distinct.
- Use a calendar window only when the request or conversation anchors one, and then name the timestamp used (author or committer), the timezone, and whether the boundaries are inclusive. When the selected commits aren't contiguous, present them as activity rather than a net change, since diffing the endpoints would include commits outside the window. Filter commits by the chosen timestamp, apply the window to checked-out history unless the user names other refs, and show a net effect only when a meaningful contiguous baseline and endpoint exist. Uncommitted changes have no reliable timestamp.

Summarize the outcomes, the important implementation changes, validation, and unresolved risk. Use verified commit, PR, or compare links: a single commit to its commit page, and a contiguous range to a compare view only after verifying both ends exist in that GitHub repository. Never claim an exact incremental range or a test result without evidence.
