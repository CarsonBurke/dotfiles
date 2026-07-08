---
name: using-gmail
description: Use the locally configured gws Gmail accounts to read or inspect email safely.
---

# Using Gmail

Use this skill when the user asks to read, search, summarize, triage, or inspect Gmail through the local `gws` CLI setup.

## Local setup

The machine has isolated `gws` config directories for these Gmail identities:

```text
/home/marvin/.config/gws-accounts/carsonburke22-gmail-com     carsonburke22@gmail.com
/home/marvin/.config/gws-accounts/marvinburke22-gmail-com     marvinburke22@gmail.com
/home/marvin/.config/gws-accounts/carson-redact-dev           carson@redact.dev
/home/marvin/.config/gws-accounts/support-redact-dev          support@redact.dev
```

Each account stores long-lived OAuth credentials as `credentials.enc` plus a local `0600` `.encryption_key`, which is the `gws` Linux encrypted-storage behavior. Do not delete `.encryption_key` unless replacing the storage mechanism and validating decryption first.

Use `GOOGLE_WORKSPACE_CLI_CONFIG_DIR` to select the account for every command:

```bash
GOOGLE_WORKSPACE_CLI_CONFIG_DIR=/home/marvin/.config/gws-accounts/carsonburke22-gmail-com gws gmail ...
```

## Operating principles

- Prefer Gmail metadata and snippets before fetching full message bodies. They are usually enough for "latest email", sender, subject, date, unread status, and triage.
- Avoid revealing secrets from email, including verification codes, reset links, auth URLs, session tokens, customer private data, and full message bodies unless the user explicitly asks for the sensitive content and it is necessary.
- When reporting results, summarize the relevant facts. Include sender, subject, date, account, labels, and a short non-sensitive snippet when useful.
- Use exact account names in user-facing summaries so the user can tell which mailbox was queried.
- `gws` may recreate `token_cache.json` with a short-lived access token during reads. For sensitive cleanup tasks, remove `/home/marvin/.config/gws-accounts/*/token_cache.json` after the query.
- Do not run `gws auth logout`, delete encrypted credentials, or start OAuth reauth unless the user explicitly wants auth repair.

## Useful commands

List the newest message:

```bash
GOOGLE_WORKSPACE_CLI_CONFIG_DIR=/home/marvin/.config/gws-accounts/carsonburke22-gmail-com \
  gws gmail users messages list --params '{"userId":"me","maxResults":1}'
```

Fetch metadata for a known message id:

```bash
GOOGLE_WORKSPACE_CLI_CONFIG_DIR=/home/marvin/.config/gws-accounts/carsonburke22-gmail-com \
  gws gmail users messages get --params '{"userId":"me","id":"MESSAGE_ID","format":"metadata","metadataHeaders":["From","To","Subject","Date"]}'
```

Search mail with Gmail query syntax:

```bash
GOOGLE_WORKSPACE_CLI_CONFIG_DIR=/home/marvin/.config/gws-accounts/carsonburke22-gmail-com \
  gws gmail users messages list --params '{"userId":"me","maxResults":10,"q":"from:example.com newer_than:30d"}'
```

Get the authenticated mailbox profile:

```bash
GOOGLE_WORKSPACE_CLI_CONFIG_DIR=/home/marvin/.config/gws-accounts/carsonburke22-gmail-com \
  gws gmail users getProfile --params '{"userId":"me"}'
```

## Expected quality

High-quality use of this skill is quiet and scoped: query only the requested mailboxes, fetch the minimum content needed, avoid leaking sensitive email contents into the final answer, and clean up short-lived token caches when the task was security-sensitive.
