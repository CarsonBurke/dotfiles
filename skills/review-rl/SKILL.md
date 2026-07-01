---
name: review-rl
description: Review an RL setup at a high level for policy/value learnability, strengths, bottlenecks, credit assignment, and likely failure modes without making code changes.
---

# Review RL

- Create a mental model of the model architecture. Especially how it constructs representations and how gradients flow.
- Make sure you deeply understand every part of the model. Given context is limited, you may want to delegate.
- From this, extrapolate: think of the most optimal version of the ideas and features, both granularly and at a higher level. Use your mental model to find bottlenecks. Be ambitious in your imagination.
- Overall, be thorough and critical.
- Identify bugs or mistakes hurting learning.
