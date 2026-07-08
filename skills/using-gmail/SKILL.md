---
name: using-gmail
description: Use the locally configured gws Gmail accounts to read or inspect email safely.
---

# Using Gmail

Use this skill when the user asks to read, search, summarize, triage, or inspect Gmail through the local `gws` CLI setup.

## Local setup

Use the `gws` command or account-specific helper already available on `PATH`.

Treat mailbox addresses and account helper names as private local identifiers: use them to select the requested mailbox, but do not copy them into skill text, commits, logs, or user-facing summaries unless the user explicitly asks.

Use the mailbox command that matches the account the user asked for. If discovery is ambiguous, ask the user which non-sensitive mailbox label or local command to use.

## Operating principles

- Prefer Gmail metadata and snippets before fetching full message bodies. They are usually enough for "latest email", sender, subject, date, unread status, and triage.
- Avoid revealing secrets from email, including verification codes, reset links, auth URLs, session tokens, customer private data, and full message bodies unless the user explicitly asks for the sensitive content and it is necessary.
- When reporting results, summarize the relevant facts. Include sender, subject, date, mailbox label, labels, and a short non-sensitive snippet when useful.
- Use non-sensitive mailbox labels in user-facing summaries so the user can tell which mailbox was queried without exposing full addresses.
- `gws` may recreate short-lived access-token caches during reads. For sensitive cleanup tasks, remove token caches through the local account tooling after the query.
- Do not run `gws auth logout`, delete encrypted credentials, or start OAuth reauth unless the user explicitly wants auth repair.

## Useful commands

List the newest message:

```bash
<gws-cmd> gmail users messages list --params '{"userId":"me","maxResults":1}'
```

Fetch metadata for a known message id:

```bash
<gws-cmd> gmail users messages get --params '{"userId":"me","id":"MESSAGE_ID","format":"metadata","metadataHeaders":["From","To","Subject","Date"]}'
```

Search mail with Gmail query syntax:

```bash
<gws-cmd> gmail users messages list --params '{"userId":"me","maxResults":10,"q":"from:example.com newer_than:30d"}'
```

Get the authenticated mailbox profile:

```bash
<gws-cmd> gmail users getProfile --params '{"userId":"me"}'
```

## Expected quality

High-quality use of this skill is quiet and scoped: query only the requested mailboxes, fetch the minimum content needed, avoid leaking sensitive email contents into the final answer, and clean up short-lived token caches when the task was security-sensitive.
