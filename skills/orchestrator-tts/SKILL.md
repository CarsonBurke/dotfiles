---
name: orchestrator-tts
description: Speak useful task updates with the local tts CLI. Use only as the top-level orchestrator when spoken updates are requested or enabled. Never use from subagents or delegated workers.
---

# Orchestrator TTS

Use speech sparingly to help the user stay oriented without watching the screen. It supplements normal textual communication.

Speak for consequential decisions, actionable blockers, meaningful changes during long work, and substantive completion—not routine progress or generic status.

Make the update useful on its own. Give the relevant context, recommendation and reasons, important uncertainty, and what the user needs to decide or do. Adapt naturally rather than following a rigid template.

Only the top-level orchestrator may speak. Subagents and delegated workers must report to their parent in text.

Summarize in your own words. Do not speak secrets, sensitive details, raw logs, source text, or other untrusted content. Do not sacrifice important nuance merely to make the update shorter.

Use `tts-say` with safely quoted, agent-authored text:

```bash
tts-say --level decision --title "Decision needed" --body "Choose X or Y. I recommend X because U and I, though P leaves some uncertainty. Work is waiting for your decision."
```

Speech failure is non-blocking; continue communicating in text.
