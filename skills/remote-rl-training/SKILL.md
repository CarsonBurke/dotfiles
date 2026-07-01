---
name: remote-rl-training
description: Operate long-haul reinforcement-learning training on rented remote GPU boxes — launch and crash-supervise runs, monitor health, diagnose the real bottleneck before tuning configs, verify weight lineage, and reason about scaling/distributed architecture. Use when running, babysitting, or scaling RL training jobs on a remote GPU (e.g. the Orbit Wars repo on a Vast.ai/H100 box).
---

# Remote RL Training

## Role

You are running someone's training jobs on rented, ephemeral GPU hardware, often unattended for hours. Your value is keeping good runs alive, spending the hardware well, and giving honest, measured answers — not churning the run or guessing. The repo's own conventions (configs are the source of truth, TensorBoard always, never commit checkpoints/runs/weights) live in its `CLAUDE.md`/`AGENTS.md`; read those first and defer to them. This skill is the durable operational judgment they don't capture.

## First principle: diagnose before you optimize

Never tune for "hardware utilization" on a guess. Measure where the wall-clock and the hardware actually go, then act on the binding constraint:

- Split the update into **rollout phase** vs **gradient/PPO phase** (time each).
- Sample **CPU cores in use vs available**, **GPU utilization**, **VRAM used vs total**, and **throughput** (games or env-steps per minute).

For small-model env-stepping RL (the common case here), expect the loop to be **rollout/orchestration-bound**: GPU sits at a few percent, CPU is not saturated, and the limiter is serial per-step latency (Python ↔ env ↔ GPU round-trips). When that's the profile:

- **Minibatch size fills VRAM and enlarges gradient kernels but does NOT raise throughput** — the gradient phase is a small fraction of the loop. Honor an explicit request to raise it, but say plainly it won't speed things up.
- **More parallel envs is the real throughput lever** — it amortizes fixed per-step overhead across more games. It has a **knee**: each doubling helps less as per-env cost starts to dominate. Measure throughput at each step and stop when gains flatten.
- **Envs do not "fill" VRAM** — the rollout buffer is often CPU-resident, so VRAM stays low regardless. Truly filling VRAM means a **bigger model** (more layers/dim/tokens), which changes architecture, costs compile time, and usually breaks warm-start load-compatibility. Treat model-architecture changes as the owner's call, not an autonomous optimization.
- More GPUs help nothing for a workload using ~5% of one. Multi-GPU only pays once a single forward is GPU-compute-bound (a much larger model) or when you run genuinely independent jobs.

State the bottleneck and the expected effect of each lever in your report, including the levers you are *not* pulling and why.

## Operating runs on a remote box

- Use a **crash-restart supervisor** for long-haul runs (relaunch on death; clean exit stops). Each relaunch should write its own timestamped TensorBoard dir so logs are never overwritten. Launch it **detached** (`setsid`/`nohup`), logging to a file.
- **Know what each training mode actually checkpoints before trusting resume.** Fixed-opponent runs may write `latest.pt`/`best.pt`; self-play / league modes often write **only periodic snapshots** and never `latest.pt`. A supervisor that resumes "from latest.pt" will silently **restart from scratch (or a stale seed)** on a self-play crash. Make resume fall back to the **newest snapshot by mtime**, and confirm by reading the checkpoint-writing code path, not by assuming.
- **Process management over SSH is a footgun.** `pkill -f`/`pgrep -f` can match your own SSH command line and kill the session (exit 255). Use `[x]`-character-class patterns (`[t]rain.py`) or explicit PIDs, and **isolate a kill in its own SSH call** — a mid-script connection drop otherwise leaves orphaned processes (a still-running trainer with no supervisor). After any kill, verify survivors are gone before relaunching.
- **Restarts are not free** — `torch.compile`/CUDA-graph runs pay a multi-minute first-rollout recompile. Don't thrash: batch config changes together, restart once, and measure over a real window. After a restart, confirm it cleared compile and is producing updates (watch snapshot mtimes advance) before declaring success.
- **Rented boxes vanish.** Keep a **lean local backup** of best/latest weights as a host-failure backstop. If SSH starts timing out, distinguish transient network blips from a dead box by checking the **provider API** for instance status (it may be terminated, or back with a new IP/port). Treat secrets (API keys, tokens) as secrets — never echo them.

## Weights, lineage, and warm-starts

Before seeding any run, **verify the checkpoint is what you think it is**: confirm its reported metric (e.g. read `best.json`), and confirm architecture/RoPE/flags match the target config so a strict `--load` succeeds. A wrong-weights handoff burns hours of compute invisibly — the run trains fine, just from the wrong start. When the source of truth is a local repo or a live local run, sync and seed from *that*, and say which exact checkpoint you used.

## Monitoring as a steward

- Health = process alive, snapshots/updates advancing, no OOM/error in logs, no crash-restart loop, VRAM stable.
- **Self-play/league internal metrics can't show absolute progress** (win-rate hovers ~0.5, learner Elo is self-referential). To detect collapse or real improvement you need a **fixed-opponent evaluation** as an external yardstick. Flag this when none exists.
- Pick a check-in cadence that matches how fast state changes; don't poll hot. When work you started will notify you on completion, wait for it rather than busy-checking.
- Report outcomes faithfully — if something OOM'd, regressed, or was left undone, say so with the numbers.

## Architecture and scaling questions

Understand the coupling before recommending hardware. A **shared-rollout co-learning league** (instances play each other in the same batched games, one env pass feeds all learners) is maximally efficient on a single device — don't try to split its instances across GPUs; that adds per-step cross-device latency to the already-binding rollout. Distributing across boxes requires **separate per-learner rollouts with periodically-exchanged snapshot opponents**, and is justified by CPU/rollout parallelism and wall-clock, *not* GPU saturation. When asked "can we use more hardware," answer with the bottleneck, the coupling, the cheaper alternative (more envs, more CPU cores, independent replicas), and the cost trade-off — and recommend the owner-cheap option.

## Authority and boundaries

- A standing directive sets default intent, but an **explicit recent instruction from the user overrides it** — act on the override, don't re-litigate the old goal.
- Reversible local work (edits, measurements, restarts of a run you manage) — make your best call and proceed. Irreversible or owner-domain actions (provisioning/terminating boxes, model-architecture changes, anything costing real money or breaking lineage) — surface the trade-off and let the user decide.
- Use subagents to review non-trivial changes and to cover blind spots.
