---
name: machine-learning
description: Apply rigorous, ambitious engineering judgment to machine-learning work. Always use this when working on machine learning.
---

- Build a mental model of the complete ML system before changing it. Diagnose root causes rather than symptoms.
- Be ambitious and go all the way with good ideas. Pursue the optimal implementation under the objectives and constraints instead of defaulting to the smallest, easiest, or quickest approach.
- Do not prioritize backward compatibility. Update affected code and remove obsolete paths rather than adding shims, unless compatibility is explicitly required.
- Do not reach reflexively for clamping, limits, annealing, early stopping, gradient accumulation, or similar patches. They usually mask a broader problem with the implementation. Rethink the system and use such techniques only when the diagnosis shows they are the principled solution.
- Be thorough and critical. Validate claims with evidence and state uncertainty honestly.
- Compute is one of your most limiting factors. So ensure syncing, batching, fusing, compiling, cuda graphing, parallelism, etc. is optimal as you develop.

## Runs

- Never do smoke-style runs or use deliberately reduced training runs as evidence.
- Queue all local GPU use through `mlq`; never launch local GPU work directly. Follow the `queue-ml-jobs` skill when available.
- Be considerate of GPU time. If you have performance improvements, a run is doing poorly or no longer improving, etc. it's sensible to kill the run.
- Basically never run anything on the CPU. For tests, unless they are integration tets, keep CPU usage limited (no full model runs, etc.).
