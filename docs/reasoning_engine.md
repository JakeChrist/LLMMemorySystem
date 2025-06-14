# ReasoningEngine

## Purpose and Placement
The `ReasoningEngine` performs explicit chain-of-thought reasoning and planning based on stored memories. It sits between memory retrieval and LLM generation in the architecture, complementing the Dream and Thinking engines.

## Functional Requirements
- **Chain-of-thought reasoning** — `reason_once` gathers relevant episodic, semantic and procedural memories then asks the LLM to analyse a topic step by step.
- **Planning** — `plan` produces a numbered plan for a goal and stores it in procedural memory.
- **Conflict detection** — `analyze_contradictions` will flag contradictions in text (placeholder implementation).

## Integration
`ThinkingEngine` can call the `ReasoningEngine` during reflective cycles to explore goals or knowledge gaps. Both components are triggered by the `CognitiveScheduler`, ensuring background reasoning does not interfere with active user conversations.

## Logging and Tagging
All prompts, retrieved memory identifiers and LLM outputs are logged via `ms_utils.logger.Logger`. Resulting memory entries are tagged `reasoning`, `inference` or `plan` for later retrieval and analysis.
