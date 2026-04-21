---
name: review-rl
description: Review an RL setup at a high level for policy/value learnability, strengths, bottlenecks, credit assignment, and likely failure modes without making code changes.
---

# Review RL

Use this skill when the user wants a high-level analysis of how an RL setup is likely to learn, where its policy and value components are structurally strong or weak, and what shortcomings matter most.

Think in terms of learning constraints, not implementation trivia.

- Ask what the actor can actually represent, not just what it outputs.
- Ask whether the critic is learning a clean value signal or a noisy proxy.
- Separate capacity limits from target quality, credit assignment, exploration, and optimization.
- Pay attention to what biases the system toward local/reactive play versus coordinated long-horizon play.
- Be concrete. Prefer a few real bottlenecks over many vague observations.
- Call out when a weakness is an intentional tradeoff for runtime or deployment constraints.

Lead with the most important findings. Be explicit about both strengths and ceilings. Use code references when they help support a point.

Do not turn this into a generic code review. Do not suggest code changes unless asked. Do not hand-wave.
