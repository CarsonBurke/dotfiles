---
name: queue-ml-jobs
description: Queue and manage local machine-learning workloads with mlq. Use for local training, evaluation, preprocessing, or benchmarks that consume shared CPU or GPU resources.
---

- Submit with `mlq submit --name NAME --max-parallel-runs N --cwd /absolute/repository/path -- COMMAND...`.
  - Give a reasonable time limit, and set max parallel runs by how saturated you expect the hardware to be.
  - Override the default priority only when there's a reason.
- A run should stay alive only as long as it's providing information.
- Consider an autocull hook at evaluation boundaries to kill runs that are falling behind or plateauing, usually based on an EMA of the loss.
- `mlq follow JOB` subscribes to a job. By default it triggers on the final outcome, and you can add conditional hooks, such as for low GPU utilization or other worrying diagnostics.
- `mlq status` shows the latest active and queued runs.
- There are many other useful commands; see `mlq --help`.
