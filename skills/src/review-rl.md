---
name: review-rl
description: Review an RL setup's learnability, credit assignment, objectives, bottlenecks, and failure modes without making changes.
---

# Review RL

Keep the review read-only. Understand the whole learning loop, from observations, representations, and actions through rewards, losses, gradients, data generation, and evaluation, before judging any part in isolation.

Look for information or gradient bottlenecks, poor credit assignment, reward exploits, leakage, non-stationarity, weak exploration, sampling bias, and mismatch between training and evaluation. Separate learning problems from throughput problems, and measure the binding constraint before recommending hardware or batching changes.

Distinguish demonstrated bugs from hypotheses, and for an uncertain claim propose the experiment or metric that would settle it. Delegate distinct lenses when useful, validate what they report, and give the strongest practical improvements with their expected benefit and tradeoffs.
