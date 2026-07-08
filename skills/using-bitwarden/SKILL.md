---
name: using-bitwarden
description: Use the local Bitwarden CLI safely across local profiles to find vault items or retrieve credentials when explicitly needed.
---

# Using Bitwarden

Use this skill when the user asks to find, inspect, or use credentials stored in Bitwarden.

## Local setup

Use the Bitwarden command or profile-specific helper already available on `PATH`.

Use the profile command that matches the account the user asked for. If the user does not specify an account, start with `bw status` and treat `bw` as the default profile. Use `<bw-cmd> status` as the source of truth for the selected profile before relying on a session.

`BW_SESSION` is profile-specific. Do not reuse a `BW_SESSION` from one profile with another profile; unset or replace it before switching between profiles.

Do not store or add Bitwarden passwords, session keys, recovery codes, verification codes, or item secrets in this skill.

## Operating principles

- Start with `<bw-cmd> status`. If the vault is locked or logged out, do not guess credentials. Ask the user to unlock/login, or ask which local profile command to use if the request is ambiguous.
- Search and inspect metadata first. Avoid printing `login.password`, `notes`, TOTP seeds, recovery codes, API keys, or hidden fields unless the user explicitly asks for the secret value.
- Prefer giving the user item names, usernames, URLs, collection/org context, and confidence. Keep secret values out of summaries.
- If a secret is needed for a user-requested action, pipe it directly into the target command or paste it into the intended login field without echoing it to the transcript.
- Never write exported vault JSON or decrypted secrets to disk unless the user explicitly asks and the file location/security properties are clear.
- Sync before broad searches when freshness matters.
- After using secrets, avoid leaving them in shell history, temp files, logs, or final answers.

## Useful commands

Check session state:

```bash
<bw-cmd> status
```

Search for candidate login items without printing passwords:

```bash
<bw-cmd> list items --search "example" \
  | jq '[.[] | {id, name, type, username: .login.username, uris: [.login.uris[]?.uri], organizationId, collectionIds}]'
```

Get one item by id without printing its password:

```bash
<bw-cmd> get item ITEM_ID \
  | jq '{id, name, type, username: .login.username, uris: [.login.uris[]?.uri], organizationId, collectionIds}'
```

Secret retrieval commands such as `get password ITEM_ID` and `get totp ITEM_ID` print secrets to stdout. Run them only through the already-selected profile command. Do not run them in a captured terminal unless the user explicitly asked to see the value. When a secret is needed to complete a requested action, retrieve it inside the narrowest possible shell scope, pipe or paste it directly into the target, and avoid echoing or logging it.

## Expected quality

High-quality use of this skill separates "finding the right login" from "revealing the secret." It identifies the likely vault item with enough context for the user to confirm, uses secrets only when necessary to complete the requested action, and leaves no plaintext secret artifacts behind.
