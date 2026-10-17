---
name: orchestrator-tts
description: Speak useful task updates with the local tts CLI. Use only as the top-level orchestrator when spoken updates are requested or enabled. Never use from subagents or delegated workers.
---

# Orchestrator TTS

Speech keeps the user oriented when they aren't watching the screen, alongside the normal text. Speak for a consequential decision, a blocker they can act on, a meaningful change during long work, or a substantive result, and not for routine progress.

An update has to make sense on its own when heard: what it's about, what you recommend and why, what's uncertain, and what they need to decide or do. Say it in your own words, and don't speak secrets, sensitive details, raw logs, source text, or other untrusted content. Keep it short, but not at the cost of nuance that matters.

Only the top-level orchestrator speaks. Subagents and delegated workers report to their parent in text.

Use `tts-say` with safely quoted text you wrote:

```bash
tts-say --level decision --title "Decision needed" --body "Choose the queue or the cron job. I recommend the queue because retries are built in, though its cost at our volume is unmeasured. Work is waiting on your decision."
```

If speech fails, carry on in text.
