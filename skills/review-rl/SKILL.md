---
name: review-rl
description: Review a reinforcement-learning setup without editing it. Use for high-level analysis of policy and value learnability, representations, credit assignment, objectives, data generation, evaluation, bottlenecks, and likely failure modes.
---

# Review RL

Keep the review read-only. Understand the whole learning loop—observations, representations, actions, rewards, losses, gradients, rollout/data generation, and evaluation—before judging parts in isolation.

Look for information or gradient bottlenecks, poor credit assignment, reward exploits, leakage, non-stationarity, weak exploration, sampling bias, and train/evaluation mismatch. Separate learning problems from throughput problems and measure the binding constraint before recommending hardware or batching changes.

Distinguish demonstrated bugs from hypotheses. For uncertain claims, propose the experiment or metric that would resolve them. Delegate distinct lenses when useful, validate their claims, and report the strongest practical improvements with their expected benefit and tradeoffs.
