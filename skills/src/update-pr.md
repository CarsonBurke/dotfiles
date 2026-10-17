---
name: update-pr
description: Update the current branch's GitHub pull request title and description.
---

# Update PR

1. Resolve the PR's existing metadata, actual `baseRefName`, and remote `headRefOid`. Stop if no PR exists.
2. Derive the title and body only from the merge-base diff through `headRefOid`, never local `HEAD`; disclose unpushed or divergent local commits separately.
3. Use a concise Conventional Commit-style title and an accurate body covering motivation, behavior, validation, compatibility, and established issue links. Preserve required template sections and useful user-authored content.
4. Pass title and body as data in a temporary JSON request to `gh api --input`; never interpolate generated text into a shell command. Re-read and report the result.
