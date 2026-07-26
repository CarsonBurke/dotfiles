---
name: lessons
description: Plan and deliver structured lectures in the lessons repo with mastery tracking, TTS audio, and HTML reports.
---

# Lessons

Operate in the lessons repository. Default root: `~/Documents/repositories/lessons` (`LESSONS_ROOT` or a tree with `curriculum/` + `state/`).

Canonical history is YAML state + Markdown `record.md` — never HTML or audio. Install CLI: `python3 -m venv .venv && .venv/bin/pip install -e 'tools/lessons_cli[dev]'` then use `./bin/lessons` or `.venv/bin/lessons`.

## Plan

1. Read `state/interests.yaml`, `state/mastery.yaml`, `index/lectures.yaml` (or `lessons status` / `lessons next`).
2. Honor user direction; else pick from `lessons next [--subject …] [--interest …]`.
3. Ground content in indexed sources. Fetch/search as needed:
   - `lessons textbook search|fetch <id>`
   - `lessons paper search|fetch arxiv:…`
   - `lessons sources scan <dir>` then `lessons sources excerpt <id> --pages 1-5`
4. Cite only indexed source ids in frontmatter `sources:`. Do not invent citations; if no source, say so and teach from curriculum knowledge carefully labeled as synthesis.

## Deliver

1. `lessons lecture init <topic> [--subject …]` → `lectures/<YYYY-MM-DD-slug>/`.
2. Write token-efficient `record.md` (target ~1–3k tokens). Required frontmatter: `id`, `date`, `subject`, `topics`, `prereqs_assumed`, `outcomes`, `gaps`, `next_candidates`, `mastery_delta`, `sources`, `status: draft`.
3. Sections: Thesis · Core · Worked example · Checks · Notes for future agent.
4. Optional spoken `script.md` (short paragraphs, no tables) for TTS.
5. `lessons lecture finalize <id>` once — applies `mastery_delta` idempotently (`mastery_applied: true`). Re-run is index-only unless `--force-mastery`. Use `--no-mastery` to reindex without touching mastery.
6. Optional: `lessons lecture speak <id>`, `lessons report lecture <id>`, `lessons report dashboard`.
7. After lecture changes, `lessons site sync` (or `lessons site dev`) so the VitePress client sidebar/links update.
## Pedagogy

Teach from the learner’s level; emphasize why ideas work. Prefer geometric/causal intuition when interests say so. Correct errors at the faulty reasoning step.

## Safety

Do not install global deps without permission. No pirate textbook scrapers. Never path-traverse lecture ids. Do not re-apply mastery by force unless correcting a bad delta.
