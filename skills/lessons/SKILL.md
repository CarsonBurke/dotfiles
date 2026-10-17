---
name: lessons
description: Plan and deliver structured lectures in the lessons repo with mastery tracking, TTS audio, and HTML reports.
---

# Lessons

Operate in the lessons repository. Default root: `~/Documents/repositories/lessons` (`LESSONS_ROOT` or a tree with `curriculum/` + `state/`).

Canonical history is the YAML state and each lecture's Markdown `record.md`, not the HTML or audio generated from them. Install CLI: `python3 -m venv .venv && .venv/bin/pip install -e 'tools/lessons_cli[dev]'` then use `./bin/lessons` or `.venv/bin/lessons`.

## Plan

1. Read `state/interests.yaml`, `state/mastery.yaml`, `index/lectures.yaml` (or `lessons status` / `lessons next`).
2. Honor user direction; else pick from `lessons next [--subject …] [--interest …]`.
3. Ground content in indexed sources. Fetch/search as needed:
   - `lessons textbook search|fetch <id>`
   - `lessons paper search|fetch arxiv:…`
   - `lessons sources scan <dir>` then `lessons sources excerpt <id> --pages 1-5`
4. Cite only indexed source ids in frontmatter `sources:`. Do not invent citations; if no source, say so and teach from curriculum knowledge carefully labeled as synthesis.

## Deliver

Keep `lessons site dev` running while writing; it re-syncs lectures, curriculum, and state into the wiki without a restart. For a one-shot sync, use `lessons site sync`.

1. `lessons lecture init <topic> [--subject …]` → `lectures/<YYYY-MM-DD-slug>/`.
2. Write token-efficient `record.md` (target ~1–3k tokens). Required frontmatter: `id`, `date`, `subject`, `topics`, `prereqs_assumed`, `outcomes`, `gaps`, `next_candidates`, `mastery_delta`, `sources`, `status: draft`.
3. Sections: Thesis · Core · Worked example · Checks · Notes for future agent.
4. Optional spoken `script.md` (short paragraphs, no tables) for TTS.
5. `lessons lecture finalize <id>` once — applies `mastery_delta` idempotently (`mastery_applied: true`). Re-run is index-only unless `--force-mastery`. Use `--no-mastery` to reindex without touching mastery.
6. Optional: `lessons lecture speak <id>` → `assets/audio/<id>/`, then `lessons site sync` (sticky wiki player). Reports: `lessons report lecture|dashboard`.

## Site authoring (in `record.md`)

- **Math:** `$…$` / `$$…$$` (MathJax on site).
- **Checks:** `- Q: …` / `  A: …` → interactive reveal. **Worked example:** numbered `1.` steps → stepper.
- **Charts:** when a relationship helps, embed a `lessons-chart` fence. Prefer **several single-Y line charts** over one multi-axis plot. Never dual Y-axes; same units → series on one Y, different units → separate charts.
  - `mole-bridge` — mass→mol for one species (`M`, `species`, optional `mass_max`/`points`)
  - `mass-moles-compare` — ≥2 species, shared mol axis (`species: [{label, M}, …]`)
  - `line` / raw — `x`, `yLabel`, `series: [{name, values}, …]`
- **Wiki:** real curriculum topic ids in `prereqs_assumed` / `next_candidates` / `topics`; real source ids in `sources`.
- Do not hand-edit `site/docs/**`; regenerate with sync.

## Pedagogy

Teach from the learner's level, emphasizing why ideas work, and lean on geometric or causal intuition when their interests suggest it. Correct errors at the step where the reasoning went wrong. A chart earns its place when it shows a relationship that words would bury.

## Safety

- Don't install global dependencies without permission or use pirated-textbook scrapers.
- Lecture ids become paths, so never let one traverse outside the tree.
- Force-reapply mastery only to correct a bad delta.
