---
name: remote-rl-training
description: Operate, supervise, diagnose, and scale long-running reinforcement-learning jobs on rented remote GPUs. Use for launches, recovery, monitoring, checkpoint lineage, throughput tuning, or distributed-training decisions.
---

# Remote RL Training

Read repository instructions, configs, launcher, and save/load code before acting.

## Authority

- Require explicit authority to start, provision, resize, extend, or terminate paid resources; change architecture; discard checkpoints; or exceed the agreed budget/duration. An available API key is not permission.
- Before launch, record instance/hourly cost, spend or time ceiling, storage limit, and the authorized deadline action. If shutdown/termination is not authorized, stop the workload at the deadline and warn that idle charges may continue.
- Restart only when crash supervision was authorized and a verified resumable checkpoint exists.

## Operate

- Measure rollout/environment and optimization time separately with CPU, GPU, VRAM, memory, disk, network when relevant, and task throughput. Tune only the measured bottleneck; low VRAM alone is not evidence of poor throughput.
- Record commit/diff or artifact hash, config, seed, command, environment, hardware, and run directory. Verify checkpoint hash, metrics, architecture/spaces/flags, optimizer state, and actual load compatibility; never silently fall back to stale weights or scratch.
- Use unique logs/checkpoints and preserve a verified recovery copy when authorized. Never overwrite the only recoverable checkpoint or expose secrets.
- Supervise detached runs with a monotonic deadline and spend ceiling. Default to 1/2/4-minute backoff and at most 3 restarts in 30 minutes; halt on the limit, repeated OOM/load failure, non-advancing updates, or insufficient authorized time for startup plus safe checkpointing.
- Monitor advancing updates/checkpoints, finite metrics, resource stability, disk, restarts, and spend. Stop safely before disk cannot hold recovery artifacts; prune only under an explicit retention policy.

Report run identity and lineage, elapsed spend, bottleneck evidence, learning/evaluation signals, restarts, checkpoint freshness, resource headroom, and unresolved risk, separating measurement from inference.
