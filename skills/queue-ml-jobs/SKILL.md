---
name: queue-ml-jobs
description: Queue and manage local machine-learning workloads with mlq. Use for local training, evaluation, preprocessing, or benchmarks that consume shared CPU or GPU resources, and for inspecting or controlling the mlq queue or daemon.
---

# Queue Local ML Work

Run local training, evaluation, preprocessing, and benchmarks through `mlq`; never bypass the queue for resource-intensive work.

## Submit

```text
mlq submit --name NAME --max-parallel-runs N \
  --cwd /absolute/repository/path -- COMMAND...
```

- Set `--max-parallel-runs` on every job. It is the maximum safe total number of concurrent managed jobs, not desired utilization. Use `1` for unknown, exclusive, multi-GPU, or benchmark-sensitive work; raise it only from coexistence evidence.
- Keep the command and descendants in the runner's foreground process group. Do not daemonize or call `setsid`.
- Add a generous `--time-limit` when excess runtime indicates a hang or cannot produce useful evidence. Queue time is excluded; startup, compilation, and descendants count.
- Omit default priority `0`. Higher values outrank eligible queued work but never preempt running jobs; do not raise priority merely to advance your own work.
- Pass required environment explicitly. `--env` values are stored as plaintext, so keep secrets in credential files.
- Use `--after-success` for strict prerequisites and `--after-terminal` for cleanup or aggregation that must include failed and culled runs.

## Cull Uninformative Runs

Long iterative runs should expose a framework-native pruning callback or use [scripts/autocull_hook.py](scripts/autocull_hook.py) at evaluation boundaries. Configure task-specific warmup, patience, and absolute material-improvement thresholds; persist the hook state with checkpoints.

Cull only after warmup when neither a smoothed return metric nor a meaningful loss has materially improved for the full patience window. Improvement in either resets patience. For RL, prefer EMA evaluation returns; use loss only when its direction is expected to track learning. For supervised work, prefer held-out loss. Raw episodic returns, noisy batch loss, one regression, or a short plateau are insufficient.

Choose patience from evaluation cadence and signal noise, with enough room for delayed learning; err toward one extra evidence window when uncertain. The goal is to stop runs that have become uninformative, not merely runs that are behind.

On cull, emit the triggering metrics and decision, preserve the latest useful checkpoint when cheap, and mark the trial pruned through the training framework. Without native pruning, emit a structured `AUTOCULL` record and use a documented exit code. `mlq` retries all nonzero exits uniformly, so keep `--max-attempts 1` unless a wrapper distinguishes culls from retryable failures; downstream collection should use `--after-terminal`.

## Operate

- Use `mlq wait JOB`, `mlq logs JOB --follow`, or `mlq subscribe` instead of polling.
- Inspect with `status`, `show`, and `logs`; control with `hold`, `release`, `cancel`, `retry`, `set-max-parallel-runs`, and `set-priority`.
- Running priority cannot change. Lowering a live parallel limit does not preempt work; it blocks new admission until the active set becomes compatible.
- Check `mlq daemon status` when the client cannot connect. If absent, run `mlqd` through the available process supervisor; do not install, uninstall, or replace the shared daemon unless requested.
- Report the job ID, parallel limit, time limit or deliberate omission, nonzero priority, and any autocull policy.
