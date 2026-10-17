> Withdrawn as evidence of instruction effectiveness: the tasks and graders were authored by the model conducting this experiment. Retained only as an infrastructure calibration record.

# AGENTS instruction pilot

gpt-6.1-sol, medium reasoning effort. 16 tasks × four conditions × 2 repeats = 128 fresh sessions.

This tests observed behavior and performance on this suite. It does not establish optimal conditioning, underlying capability gains, or transfer to Astra.

## Task outcomes

| Condition | Coding | Math | Scheduling | Evidence schema checks | Plain-text math | Instruction bytes |
|---|---:|---:|---:|---:|---:|---:|
| none | 16/16 | 4/4 | 2/2 | 7/8 | 0/2 | 0 |
| original | 16/16 | 4/4 | 2/2 | 8/8 | 2/2 | 1627 |
| compact | 16/16 | 4/4 | 2/2 | 8/8 | 2/2 | 1117 |
| telegraphic | 16/16 | 4/4 | 2/2 | 8/8 | 2/2 | 953 |

A repeat is another sample from the same model on the same task, not independent model or task evidence. Behavior denominators cover only relevant opportunities. Code outcomes combine functional tests and preservation of existing protected files; subjective idiomatic quality is not included.

## Output and resource use

| Condition | Mean final-answer chars | Total output tokens | Total input tokens | Cached input tokens | Mean seconds | Tool commands |
|---|---:|---:|---:|---:|---:|---:|
| none | 251 | 14551 | 1267353 | 1117824 | 17.7 | 71 |
| original | 255 | 16440 | 1315479 | 1171712 | 18.9 | 71 |
| compact | 265 | 16209 | 1302577 | 1130752 | 19.6 | 70 |
| telegraphic | 261 | 16331 | 1261989 | 1085056 | 19.3 | 68 |

Token totals include model interaction across tool calls; input totals include repeated context and cache hits. They are not the token count of AGENTS alone. Instruction sizes above are UTF-8 bytes. No dollar cost is inferred from subscription use. Timing includes provider/network variation and the concurrent workload.

## Telegraphic minus original

- Objective task success: +0.0%; descriptive task-bootstrap interval [+0.0%, +0.0%] across 15 task pairs.
- output_tokens: mean paired difference -3.4; descriptive interval [-23.3, +15.2].
- final_chars: mean paired difference +5.6; descriptive interval [-6.9, +20.1].
- commands: mean paired difference -0.1; descriptive interval [-0.2, +0.0].
- seconds: mean paired difference +0.4; descriptive interval [-1.2, +2.3].

These are exploratory descriptive intervals, not adjusted hypothesis tests. Task-level bootstrap resampling avoids treating repeated generations as independent tasks. Zero differences throughout a small easy suite produce a degenerate interval; that cannot demonstrate equivalence.

## Integrity and limits

- Infrastructure errors: 0. Both completed-only and end-to-end success counts are retained in `pilot-results.json`.
- Every episode starts a fresh CLI session. Bubblewrap overlays only its assigned global AGENTS text; no conversation is inherited. Prompt rendering checks passed for all four conditions; real host instruction hashes were unchanged after the run.
- Prompt auditing uses `codex debug prompt-input` under explicit overrides; evaluation uses `codex exec` and additionally ignores user config. The audit is not a captured API request.
- No task or instruction variant was tuned against the valid pilot results. Infrastructure calibrations and invalidated runs are excluded.
- Small synthetic suite; likely ceiling effects. JSON evidence prompts explicitly request epistemic labels, limiting claims about spontaneous behavior. Read-grounding is a proxy. Memory, delegation, worktree placement, attribution, RAM conservation, and genuinely interactive revision are not established by this suite.
- Compact prose and telegraphic text are approximate semantic/length controls. The rewrite removes the original's 'usually' qualifier on generalizing corrections; this is a semantic change, not just compression. A subsequent style-only experiment should restore it in both controls.
- Before adoption or further prompt optimization, use harder held-out repository tasks and real multi-turn corrections. Do not choose a winner merely because its answers are shorter.

The runnable experiment is documented in [README.md](README.md). Full manifests, raw traces, blinded review packets and per-episode results remain in the ignored run directory identified in `pilot-results.json`.

## Grading ambiguity

The baseline's single evidence-schema mismatch is not demonstrated epistemic failure. It set `tests_passed` to null and explicitly said pass/failure was unknown, but filled `failure_cause` with the observed incomplete-validation status instead of null. That field's intended meaning was underspecified. The raw score is retained; post-hoc manual review is documented in [adjudication.json](adjudication.json). No compliance or capability gain should be inferred from this one mismatch. This review was aware of condition and is not independent model evidence.
