---
name: queue-ml-jobs
description: Queue and manage local machine-learning workloads with mlq. Use for local training, evaluation, preprocessing, or benchmarks that consume shared CPU or GPU resources.
---

- Submit: `mlq submit --name NAME --max-parallel-runs N --cwd /absolute/repository/path -- COMMAND...`
 - Give a reasonable time limit, and set max parallel runs based on how saturated you expect hardware to be.
 - Override default priority only when justified.
- Runs should only stay alive so long as they are providing information.
- You should generally consider using an autocull hook at evaluation boundaries to kill runs that are not performing sufficiently well - such as if they are falling behind or plateauing. Usually this will be an EMA on loss.
- Use `mlq follow JOB` to subscribe; by default it will trigger on the finnal outcome; you can set conditional hooks as you see fit, such as low gpu util or other concerning diagnostics.
- `mlq status` to see the latest active and queued runs.
- There are many other commands that you will find useful.
