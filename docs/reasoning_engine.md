# ReasoningEngine Overview

The `reasoning.reasoning_engine` module provides a small utility class for
autonomous reasoning and planning.  It queries episodic, semantic and
procedural memories, reconstructs a context and prompts the configured LLM
for a multi-step analysis or a plan.

- `ReasoningEngine.reason_once` performs one reasoning cycle about a topic and
  stores the result in episodic memory tagged `reasoning`.
- `ReasoningEngine.plan` creates a step-by-step plan for a goal and stores the
  plan in procedural memory tagged `plan`.

Both operations log prompts, retrieved memory identifiers and outputs via
`ms_utils.logger.Logger`.
