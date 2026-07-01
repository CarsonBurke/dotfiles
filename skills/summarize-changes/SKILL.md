---
name: summarize-changes
description: Summarize pushed code changes as a markdown table with GitHub PR-UI commit-range diff links so a reviewer can open exactly the new commits.
---

# Summarize Changes

After making and/or pushing changes (one or more PRs, or the current branch), produce a concise markdown table summarizing the work with GitHub PR-UI diff links scoped to the new commits.

## When to use

- After addressing review findings, Bugbot/reviewer comments, or a ticket and pushing the result.
- When a reviewer needs to open exactly the new commits, not the whole PR diff.

## Table format

One row per PR:

| PR | Reason for changes | Summary of changes | Combined diff |
| --- | --- | --- | --- |

- **PR** — `#<number>` linking to the PR.
- **Reason for changes** — the driver: the review finding / Bugbot or reviewer comment / ticket. Why it was made.
- **Summary of changes** — what actually changed, concise but specific (files, behaviors).
- **Combined diff** — ONE link per PR covering ALL the new commits together (see below).

List any items intentionally deferred or left unresolved as bullets below the table.

## Combined diff link

Use a range view with FULL 40-char SHAs:

`https://github.com/<owner>/<repo>/pull/<PR>/files/<BASE_FULL_SHA>..<HEAD_FULL_SHA>`

- `BASE` = the commit the branch was at BEFORE the new commits (prior pushed head, or `git merge-base origin/<baseRef> HEAD`).
- `HEAD` = the latest new commit.
- `/files/<base>..<head>` is the canonical Files-changed range view and is preferred. The `/pull/<PR>/changes/<base>..<head>` form renders the same range as a review; document both and use whichever renders.
- For a single new commit, link `https://github.com/<owner>/<repo>/pull/<PR>/commits/<HEAD_FULL_SHA>` instead.

## Gathering the data

- Owner/repo: `gh repo view --json nameWithOwner --jq .nameWithOwner`.
- PR for a branch: `gh pr list --head <branch> --json number,headRefName,headRefOid` or `gh pr view --json number,headRefName,headRefOid`.
- Base ref of the PR: `gh pr view <PR> --json baseRefName --jq .baseRefName`.
- BASE sha (branch point before the new work): the prior remote head if known, else ``git merge-base origin/<baseRef> HEAD``.
- HEAD sha: the latest new commit (`headRefOid`, or `git rev-parse HEAD`).
- Full SHAs (always): `git rev-parse <ref>`.
- New commits, for the summary: ``git log <BASE>..<HEAD> --oneline --no-merges``.

## Multi-PR case

- Repeat the gathering steps per branch/PR and emit one row per PR, each with its own BASE/HEAD range link.
