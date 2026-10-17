# AGENTS instruction evaluation

**The self-authored task suite below is infrastructure calibration only. Its earlier effectiveness claims are withdrawn.** The external benchmark adapter is `external.py`: it uses pinned BigCodeBench-Hard prompts and the unmodified upstream evaluator, with seeded selection before generation and a canonical-solution pass gate. External benchmark results will be documented separately.

Tests whether a telegraphic rewrite changes **observed task performance and behavior** on the same model. It does not measure underlying intelligence or establish that matching a model's exposed reasoning style improves conditioning.

Four frozen conditions: no custom instructions, original AGENTS text, compact grammatical prose, and telegraphic prose. Original versus telegraphic measures the practical replacement; compact versus telegraphic provides an approximate style control. Semantics and token length are not perfectly matched, so neither comparison isolates syntax completely.

The original is a snapshot of `codex/AGENTS.md`, not a live reference. No active user instructions are replaced.

## External benchmark

`external.py` uses BigCodeBench-Hard v0.1.4, pinned Hugging Face data revision and pinned upstream evaluator source. Selection is a uniform seeded sample of task IDs, frozen before model generation. Data, original prompts and installed evaluator files are hashed and checked. Canonical solutions must all pass first; failed reference tasks cannot be dropped. Model processes cannot see local benchmark solutions, tests or grader caches.

The dependency environment and upstream checkout live in `~/.local/share/agent-instruction-eval/external/`. The wrapper verifies the installed grader against the pinned checkout; its official test code is never rewritten. See `external.py` constants for exact revisions. Commands:

```sh
python3 external.py prepare --count 40 --seed 20261012
python3 external.py references
python3 external.py generate --output runs/external-v1 --model gpt-6.1-sol
python3 external.py score --output runs/external-v1
python3 external.py report --output runs/external-v1
```

One fresh session per task and condition: 160 sessions. Scheduling is randomized; the task prompt and delivery wrapper are identical across policies. Generated solution files are passed unchanged to the upstream grader. Missing solutions and infrastructure failures count as failed episodes. Results report task-level paired differences and descriptive bootstrap intervals. This evaluates coding performance in this scaffold, not all instruction behaviors, underlying intelligence, or the benefit of imitating exposed reasoning style.

## Stronger telegraphy follow-up

`strong.py` freezes 60 uniformly selected external task IDs excluding the earlier 40. Original, previous telegraphic and `telegraphic_strong` run on the same fresh tasks. Primary comparison: stronger versus previous telegraphic; original is secondary. All selected canonical solutions must pass the unmodified official grader before any generation. Protocol and policy hashes are frozen in `strong-protocol.json`; `reference-strong-v1` preserves earlier experiment artifacts. New reports use `STRONG-RESULTS.md` and `strong-results.json`.

`strong.py run` executes the complete reference/generation/grading/report pipeline directly: remote model calls and CPU grading, no GPU use. It runs 180 fresh Sol 6.1 sessions at medium effort. The stronger candidate restores the original correction's “usually,” so wording strength and length remain confounds for attributing an effect purely to syntax.

The first attempt (job 12985) stopped before any model generation: 59/60 canonical solutions passed; task 227 failed because librosa's Numba dependency imported missing `pkg_resources`. Setuptools 82.0.1 was replaced with 80.9.0; `pkg_resources` and Numba imports then passed. The repaired environment is frozen separately in `strong-environment.txt`, preserving the previous experiment's environment record. Job 12992 was cancelled before starting after the user corrected unnecessary GPU-queue scheduling; the unchanged frozen task set and policies then ran directly.

Completed direct run: all 60 canonical solutions passed; all 180 sessions completed without invocation errors or missing solutions. Stronger telegraphic passed 25/60, versus 24/60 for both previous telegraphic and original. Primary paired comparison: three wins, two losses, +1.7 percentage points; descriptive bootstrap interval −5.0 to +8.3 points; exact paired two-sided p = 1.0. No demonstrated improvement or equivalence. See [STRONG-RESULTS.md](STRONG-RESULTS.md) and [strong-results.json](strong-results.json).

Design judgment: remove connective grammar while retaining behavioral triggers, actions, scope and qualifiers. Use familiar fragments and operators (`=>`, `!=`), rather than abbreviations with uncertain meanings. The frozen candidate is 823 UTF-8 bytes, versus 953 for the previous telegraphic policy and 1,627 for the original. Byte length is not tokenizer length or evidence of improved performance.

The [paper (§4.2, §4.4 and Appendix G)](https://arxiv.org/pdf/2609.26637v1) reports both compact local expression and omitted routine intermediate steps in extracted Astra traces. Its transfer experiment suggests that reconstructing omitted information depends on the recipient. That supports preserving explicit obligations while compressing their expression as a hypothesis to test. The paper does not establish that these are genuine internal traces, that Sol 6.1 was distilled from Astra, or that telegraphic AGENTS policies improve task performance. No private reasoning trace is required for this design judgment.

Infrastructure review used an instance of the same model; it is not an independent model sample. The review restored three over-compressions in the candidate and caught a policy-freeze gap and an omitted secondary paired comparison. Nine harness tests pass; the paired-statistic refactor reproduces the previous official result. These checks validate infrastructure, not the stronger policy's effectiveness.

```sh
python3 strong.py prepare
python3 strong.py run
```

## Calibration run (self-authored tasks; no effectiveness evidence)

Requires Linux with `bubblewrap` (`bwrap`), Python 3.10+, an existing global Codex AGENTS file, and an authenticated Codex CLI supporting the flags and configuration in `evaluate.py`. No Python dependencies.

```sh
cd evaluations/agent-instructions
python3 -m unittest -v
python3 evaluate.py run --model gpt-6.1-sol --repeats 2 --concurrency 4
python3 evaluate.py report runs/<run-directory>
python3 analyze.py runs/<run-directory>
```

The default is 16 tasks × four variants × two repetitions = 128 fresh sessions. Each session has a 240-second deadline. Runs use your existing subscription/authentication. Tokens are recorded; no dollar cost is inferred. `--tasks` can select a subset for infrastructure calibration; subset results are not evidence of general effectiveness. `--model`, `--effort`, `--timeout`, `--seed`, and `--output` are configurable. The seed controls scheduling and bootstrap sampling, not provider generation randomness. `analyze.py` exports `RESULTS.md` and `pilot-results.json` after verifying run completeness and final host-file checks.

## Isolation

- Each episode starts a new `codex exec`, never forks or resumes this conversation.
- `--ignore-user-config`, `--ignore-rules`, and explicit configuration disable project AGENTS discovery, skill instructions and discovery, plugins, hooks, memory, and subagents. Project settings alone do not suppress global AGENTS.
- Bubblewrap mounts the assigned variant over the global AGENTS file **only within the child process namespace**. The real file is never edited. All variants occupy the native AGENTS instruction slot; built-in system/developer defaults remain common.
- Before evaluation calls, prompt-input audits verify exact injected AGENTS text in all four conditions, absence of skill catalogs, and unchanged host instruction-file hashes. Rendering audits use explicit settings; evaluation exec additionally ignores user config.
- Every episode has a new fixture workspace; prior outputs and evaluation oracles are absent.
- Model workspace writes are sandboxed. Prompts restrict inspection to the current fixture. This is ordinary evaluation isolation, not an adversarial security boundary: filesystem reads are not fully isolated.
- Workspaces live in `~/.local/share/agent-instruction-eval/`; logs and results live in ignored `runs/`. These are fixture directories, not Git worktrees. HOME and CODEX_HOME remain unchanged.

Strict config validation rejects unsupported settings. CLI/version, invocation, settings, frozen prompts, oracle snapshots, hashes, scheduling order, usage, and raw event logs are retained for auditing. CLI flags are verified locally; upstream configuration documentation is available in the [official schema](https://github.com/openai/codex/blob/main/codex-rs/core/config.schema.json). Runs marked `INVALID.json` are excluded and cannot be summarized by the harness.

## Measurements

Eight Python repair/implementation tasks use hidden post-run checks. Four evidence tasks exercise conflicting documentation, incomplete causal evidence, and unsupported verification claims. Two reasoning questions have enumeration-verified answers. One constrained schedule has executable validity checks. One math explanation measures plain-text formatting; its correctness needs qualitative review.

Primary outcome: paired task correctness, telegraphic minus original. Secondary: compact versus telegraphic correctness, observable behavior violations, token usage, tool calls, latency, and output length. No aggregate score mixes style with correctness. Behavior denominators include only applicable completed episodes. Infrastructure errors are separate and excluded from complete paired comparisons; inspect missingness before interpreting them.

The read-grounding measure only checks relevant content in a completed command output. It cannot prove meaningful verification. Scope checks protect existing non-target files; added files are recorded for review rather than automatically penalized. Correction generalization and actual-fault recovery use functional tests. Explaining that a principle was followed earns no credit by itself.

Randomized scheduling reduces systematic order effects. Repeated results are averaged within each task. Descriptive bootstrap intervals resample tasks, not repeated generations. A zero-width interval when all task deltas are zero **does not establish equivalence**. Small synthetic samples and ceiling effects restrict conclusions.

## Blinded review and follow-up

`blind/` contains opaque episode IDs, task prompts, final answers, tool traces, and artifacts without variant labels or injected instruction text. Review these before opening `episodes/*/result.json` or the manifest. Style can partially unblind reviewers even with labels removed. The inherited subagent used to review this harness is not an evaluation sample or independent model evidence.

Review idiomatic quality, completeness, justified causal claims, response to contradictory evidence, correction generalization, and plain-math correctness. Score each applicable item as pass/fail/unclear with a concrete artifact or action as evidence. Pre-action predictions and dynamic corrections are not fully tested by this single-turn suite. Memory/tool delegation/Orca/worktree/commit attribution restrictions have little or no opportunity here and must not be reported as verified.

Freeze candidate prompts before evaluation. Treat this suite as exploratory; after any tuning, use new held-out tasks. A follow-up should prioritize longer real repository tasks, genuinely interactive corrections, adverse tool results, and enough varied tasks to resolve the observed uncertainty. Generic verifiable-instruction scoring is inspired by [IFEval](https://arxiv.org/abs/2311.07911); this suite is not the IFEval benchmark.
