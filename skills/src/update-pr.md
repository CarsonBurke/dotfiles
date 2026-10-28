---
name: update-pr
description: Update the current branch's GitHub pull request title and description.
---

# Update PR

Rewrite the title and body of the current branch's existing PR so they describe what it actually contains; stop if there is no PR. What it contains is the diff from the merge-base with its real `baseRefName` to the remote `headRefOid`, not local `HEAD`. Mention unpushed or divergent local commits separately rather than describing them as part of the PR.

Use a concise Conventional Commit-style title.

<!-- include: parts/pr-description -->

Pass the text to `gh api --input` as a temporary JSON file rather than interpolating it into a shell command, since generated text contains quotes and backticks. Re-read the PR afterward and report the result.
