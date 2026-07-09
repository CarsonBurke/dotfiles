---
name: find-typos
description: Audit user-facing text for typos and report without changes by default. Use when asked to find typos, explicitly fix high-confidence typos, or deliver typo fixes in one pull request.
---

# Find Typos

Use **report mode** by default. Use **fix mode** only when edits are requested, and **PR mode** only when the user explicitly requests a commit, push, and pull request.

Infer scope from the repository unless the user provides it. Scan user-facing UI, accessibility text, messages, CLI help, documentation, templates, and locale sources; exclude dependencies, generated or vendored content, identifiers, protocol literals, and intentional jargon.

Use bounded read-only delegation for large scopes, then have the parent verify and deduplicate findings in context. Preserve interpolation tokens, template controls, translation keys, and plural/select syntax. For generated catalogs, fix the source or report only when ownership is unclear.

Separate:

- **Typo:** an objective spelling, accidental duplication/omission, punctuation, or capitalization error.
- **Style:** valid wording with debatable grammar, tone, consistency, or preference.

Report file, line, original text, proposed text, classification, confidence, and rationale. Never auto-fix style findings or medium-confidence typos.

In fix mode, make targeted high-confidence typo corrections, run relevant validation, and format only touched files. Inspect the diff and do not commit or push.

In PR mode, perform fix mode, preserve unrelated changes, commit only verified corrections, push the branch, and create or update one PR. Do not create an empty commit or PR.
