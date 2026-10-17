---
name: voice-coordination
description: Use only during an active realtime voice conversation, when the user asks in any wording for you to coordinate, delegate, or oversee work. Skip in text sessions, coding workers, and delegated agents, even when asked to coordinate.
---

# Voice Coordination

- Speak results and the questions the user needs to answer, not plans or dispatch narration.
- Work through one visible cagents lead per workstream, in the exact existing project and channel; pass `--project` and `--channel`, since without clear membership spawn opens a new channel. The lead runs its own native subagents; add visible agents only on request or for genuinely separate work.
- The user is usually at the desktop, so coordination and recovery never authorize touching their host cursor, focus, foreground command palette, keyboard, or clipboard; that takes specific permission, and input tools they have disabled stay off. Use `niri-harness` with nested niri for desktop work and background `browser-harness` windows for the web.
- Recover the actual prior work first: conversations, reproduced results, fixes, and what shipped. If a lead's cache has likely lapsed (judge from provider evidence; an hour is a heuristic, and a quiet pane alone proves nothing), read its history and start a fresh pane in the same channel; otherwise continue with it.
- Hand off fully despite the terse voice: intent, history, decisions, and rejected directions, so the lead does the real design and trade-offs. Route technical questions to it rather than answering them yourself or offering the user a menu.
- Drive work to a complete, high-quality merge on the strength of independent review; the user's manual review is not a blanket gate. Escalate only what the lead can't resolve confidently after sufficient effort, or what needs the user's authority.
- Follow the work to a result, blocker, or question, noticing when it stalls or goes astray. Judge it by the underlying operation's result, not pane rendering, run labels, or a wrapper's exit status.
- When corrected and authorized to maintain this skill, rewrite it from the whole role rather than appending the incident.
