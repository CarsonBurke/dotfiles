---
name: handshake-review
description: Use Codex or Claude to review
---

Use other agent for their strengths:

Claude is more exploratory but gets more things wrong. Use it to find a swath of issues.

Codex is focussed and smart. It will not find as many issues, but is more grounded and reasonable. Use it to validate claims from claude, and to find some errors on its own.

## Workflow

Generally spawn a codex and a claude subagent, then reasonably verify and resolve the concerns raised. You may want a separate codex subagent to verify claude's claims.

## Invoking

Claude asking Codex:

```bash
codex exec - <<'EOF'
<review prompt>
EOF
```

Codex asking Claude:

```bash
claude -p <<'EOF'
<review prompt>
EOF
```
