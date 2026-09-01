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
- We're always compute limited, so make generally make reasonable sacrifices. Examples: 
  - Don't do multiple seeds.
  - Don't have runs continue if they aren't providing more information, they're performing poorly, or they've plateaued. This includes sensible auto culling.
- Model should never run on the CPU or fall back to worse versions. Examples: if the model supports f8 or bf16, it should never fall back to f32; if the model supports compiled, it should never fall back to eager. And generally it should pursue performance optimums.
