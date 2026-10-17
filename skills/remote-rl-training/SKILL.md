---
name: remote-rl-training
description: Run, monitor, recover, and scale reinforcement-learning training on rented remote GPUs.
---

# Remote RL Training

Read the repository instructions, configs, launcher, and save and load code before acting.

## Authority

- Paid resources need explicit authority to start, provision, resize, extend, or terminate, and so do changing the architecture, discarding checkpoints, or exceeding the agreed budget or duration. An available API key isn't permission.
- Before launch, record the instance and hourly cost, the spend or time ceiling, the storage limit, and what's authorized at the deadline. If shutting down isn't authorized, stop the workload at the deadline and warn that idle charges may continue.
- Restart only when crash supervision was authorized and a verified resumable checkpoint exists.

## Operate

- Measure rollout and optimization time separately, alongside CPU, GPU, VRAM, memory, disk, network where relevant, and task throughput, and tune only the bottleneck you measured. Low VRAM use alone doesn't show poor throughput.
- Record what reproducing or resuming a run needs: commit or artifact hash, config, seed, command, environment, hardware, and run directory.
- Before resuming, verify the checkpoint's hash, metrics, architecture, spaces and flags, optimizer state, and that it actually loads. Never silently fall back to stale weights or a fresh start.
- Keep logs and checkpoints unique, preserve a verified recovery copy when authorized, never overwrite the only recoverable checkpoint, and keep secrets out of all of it.
- Supervise detached runs with a monotonic deadline and spend ceiling. By default, back off 1, 2, then 4 minutes, with at most 3 restarts in 30 minutes. Halt on reaching that limit, on repeated OOM or load failures, on updates that stop advancing, or when too little authorized time remains to start up and checkpoint safely.
- Watch that updates and checkpoints advance, metrics stay finite, resources and disk hold, and spend stays in bounds. Stop safely before the disk can no longer hold recovery artifacts, and prune only under an explicit retention policy.

Report the run's identity and lineage, spend, bottleneck evidence, learning and evaluation signals, restarts, checkpoint freshness, headroom, and open risks, keeping measurement apart from inference.
