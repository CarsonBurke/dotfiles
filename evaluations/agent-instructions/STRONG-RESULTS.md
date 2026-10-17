# External AGENTS instruction evaluation

BigCodeBench-Hard v0.1.4: 60 seeded random externally authored tasks; 3 frozen policies; one fresh gpt-6.1-sol session per task and policy. Original benchmark prompts and tests; unmodified upstream execution grader. All 60 canonical solutions passed before generation.

| Policy | Passed | Infrastructure errors | Median output tokens | Median seconds |
|---|---:|---:|---:|---:|
| original | 24/60 | 0 | 1040 | 30.0 |
| telegraphic | 24/60 | 0 | 1060 | 27.0 |
| telegraphic_strong | 25/60 | 0 | 1012 | 28.2 |

telegraphic_strong minus telegraphic: +1.7 percentage points. Descriptive paired task-bootstrap 95% interval: -5.0 to +8.3 points. Treatment-only passes: 3; baseline-only passes: 2. Exact paired two-sided test p = 1.000.

telegraphic_strong minus original: +1.7 percentage points. Descriptive paired task-bootstrap 95% interval: -3.3 to +8.3 points. Treatment-only passes: 2; baseline-only passes: 1. Exact paired two-sided test p = 1.000.

The bootstrap intervals are descriptive; these results do not establish equivalence or rule out harm.

This is an exploratory estimate of coding performance under this Codex scaffold. This sample and one generation per condition do not establish equivalence or a capability change. Public benchmark contamination is unknown. Policies differ in length and some wording strength, so this does not isolate telegraphic syntax. Benchmark tests do not score every AGENTS behavior; no claim about correction generalization, epistemic honesty, or idiomatic quality is made from pass rates alone.

The prior self-authored pilot is withdrawn as effectiveness evidence and retained solely as infrastructure calibration. The same-model subagent reviewed infrastructure, not answers or benchmark task selection.

Execution runtime: Python 3.9.25, headless Matplotlib Agg, multiprocessing spawn; 3 condition graders concurrently, each with four upstream workers. Reference diagnostic stack tracing: False; candidate grading used no tracing. Installed packages are frozen in [strong-environment.txt](strong-environment.txt).

Provenance: dataset revision `298d2cc7b96612e15e47313c3603ee124cee0c1f`; upstream commit `09dd993f46c3fbf3a799465bb96d524edcb0b199`; seed `20261013`. Hashes, selected IDs, full per-task scores and protocol are in [strong-results.json](strong-results.json). Raw run: `/home/marvin/Documents/repositories/dotfiles/evaluations/agent-instructions/runs/strong-v1`.

Sources: [BigCodeBench](https://github.com/bigcode-project/bigcodebench), [BigCodeBench-Hard dataset](https://huggingface.co/datasets/bigcode/bigcodebench-hard).
