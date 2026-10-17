# External AGENTS instruction evaluation

BigCodeBench-Hard v0.1.4: 40 seeded random externally authored tasks; four frozen policies; one fresh gpt-6.1-sol session per task and policy. Original benchmark prompts and tests; unmodified upstream execution grader. All 40 canonical solutions passed before generation.

| Policy | Passed | Infrastructure errors | Median output tokens | Median seconds |
|---|---:|---:|---:|---:|
| none | 12/40 | 0 | 788 | 28.3 |
| original | 11/40 | 0 | 1031 | 32.3 |
| compact | 11/40 | 0 | 874 | 30.3 |
| telegraphic | 14/40 | 0 | 970 | 31.2 |

Telegraphic minus original: +7.5 percentage points. Descriptive paired task-bootstrap 95% interval: +0.0 to +17.5 points. Telegraphic-only passes: 3; original-only passes: 0. Exact paired two-sided test p = 0.250; this run does not establish an improvement. The bootstrap boundary at zero reflects the observed absence of reversals and must not be read as ruling out harm.

This is an exploratory estimate of coding performance under this Codex scaffold. This sample and one generation per condition do not establish equivalence or a capability change. Public benchmark contamination is unknown. Policies differ in length and some wording strength, so this does not isolate telegraphic syntax. Benchmark tests do not score every AGENTS behavior; no claim about correction generalization, epistemic honesty, or idiomatic quality is made from pass rates alone.

The prior self-authored pilot is withdrawn as effectiveness evidence and retained solely as infrastructure calibration. The same-model subagent reviewed infrastructure, not answers or benchmark task selection.

Execution runtime: Python 3.9.25, headless Matplotlib Agg, multiprocessing spawn; four condition graders concurrently, each with four upstream workers. The reference gate included temporary diagnostic stack tracing; candidate grading used no tracing. Installed packages are frozen in [external-environment.txt](external-environment.txt).

Provenance: dataset revision `298d2cc7b96612e15e47313c3603ee124cee0c1f`; upstream commit `09dd993f46c3fbf3a799465bb96d524edcb0b199`; seed `20261012`. Hashes, selected IDs, full per-task scores and protocol are in [external-results.json](external-results.json). Raw run: `/home/marvin/Documents/repositories/dotfiles/evaluations/agent-instructions/runs/external-v1`.

Sources: [BigCodeBench](https://github.com/bigcode-project/bigcodebench), [BigCodeBench-Hard dataset](https://huggingface.co/datasets/bigcode/bigcodebench-hard).
