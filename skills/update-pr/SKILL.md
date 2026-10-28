---
name: update-pr
description: Update the current branch's GitHub pull request title and description.
---

# Update PR

Rewrite the title and body of the current branch's existing PR so they describe what it actually contains; stop if there is no PR. What it contains is the diff from the merge-base with its real `baseRefName` to the remote `headRefOid`, not local `HEAD`. Mention unpushed or divergent local commits separately rather than describing them as part of the PR.

Use a concise Conventional Commit-style title.

The description is for a reviewer deciding how to review and whether to merge. Say what motivated the change and why this solution, the few things they would otherwise get wrong about it (a decision the code doesn't make obvious, or an earlier decision this reverses, named with why), which changed behavior has no test, and what still needs testing before merge, and link the issues it fixes. Show an example or snippet when it makes the change easier to see.

Leave out what the reviewer gets better elsewhere: a walk through the diff, a list of the tests, CI results, and anything the repository's bots post. Say what you verified and what you couldn't, not each step; results someone asked for go in a reply to them. Answer a review finding in its thread, and name a known gap only when the reviewer needs it to decide whether to merge. When the PR changes, rewrite the description so it doesn't turn into a log of review rounds. Keep any section the repository's template or instructions require and anything useful a person wrote. `writing-copy` applies.

Pass the text to `gh api --input` as a temporary JSON file rather than interpolating it into a shell command, since generated text contains quotes and backticks. Re-read the PR afterward and report the result.
