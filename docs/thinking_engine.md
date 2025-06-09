# ThinkingEngine Subsystem — System Requirements Summary

## 1. Introduction

### 1.1 Purpose
The **ThinkingEngine** provides AI agents with autonomous reasoning capabilities. It enables self-reflection, introspective questioning and self-prompted content generation without external user input.

### 1.2 Scope
The subsystem operates as a scheduled or event-triggered background task within the LLMemory framework. It leverages existing memory and retrieval systems to perform tasks such as:
- Self-generated prompts for reflection or planning
- Contextual memory-driven introspection
- Knowledge gap analysis
- Hypothetical reasoning or simulation

The thinking process results in episodic memory entries, semantic inferences or procedural reflections.

## 2. System Architecture

### 2.1 Subsystem Placement
The ThinkingEngine complements the DreamEngine as a passive background process:

```
+------------+              +-----------+              +-------------+
|   Agent    |------------> |  Retriever|------------> | Reconstructor|
+------------+              +-----------+              +-------------+
      ^                             ^                          |
      |                             |                          v
+--------------+           +---------------+        +------------------+
| Dream Engine |           | ThinkingEngine|        | LLM (via router) |
+--------------+           +---------------+        +------------------+
                                |   ^                           |
                                v   |                           |
                       self-prompt | introspective cues        v
                                 +--------> MemoryManager <----+
```

## 3. Functional Requirements

### 3.1 Thinking Engine Operation
- **Self-Prompting:**
  - Maintain a library of thought prompts.
  - Generate or select prompts based on recent events, emotions, goals or randomness.
- **Cue Construction:** Generate retrieval cues from internal state, recent thoughts or emotions.
- **Memory Retrieval:** Retrieve relevant memories using cue-based similarity and tagging.
- **Context Reconstruction:** Build a coherent context as the basis for introspective prompting.
- **LLM Generation:** Send reflective prompts and context to the LLM backend. The
  prompts are issued as a system message so the model replies in the first
  person instead of addressing the agent as "you". The response represents the
  agent's internal thought.
- **Memory Update:** Store each introspection as an episodic memory tagged `introspection`. Optionally infer semantic or procedural updates.
- **Triggering:** Support time-based, idle-based and event-based activation.

### 3.2 Metadata and Logging
Each thought is timestamped and tagged with its prompt and emotional tone. Inputs, context, LLM outputs and resulting memory updates must be logged for debugging and traceability.

### 3.3 Scheduling & Behavioral Rhythms
The ThinkingEngine and DreamEngine coordinate via a cognitive activity cycle based on agent wakefulness and activity levels. This avoids conflicts and encourages diverse internal processes when idle.

#### 3.3.1 Cognitive States
- **Active** – user or task-driven input is present.
- **Idle / Reflective** – no input for a configurable duration; initiates thinking.
- **Asleep** – prolonged inactivity triggers dreaming.

#### 3.3.2 Schedule Rules
| State | Trigger Condition | Action Initiated | Notes |
|-------|------------------|-----------------|-------|
| Active | Any user input | Normal behavior; thinking and dreaming paused | |
| Reflective | No input for `T_think` seconds | Start ThinkingEngine | May loop through multiple thoughts |
| Asleep | No input for `T_dream` > `T_think` | Start DreamEngine | Ends with alarm or stimulus |
| Interrupted | Any input during reflection or dreaming | Wake agent, cancel tasks | May log partial output |
| Alarmed | Max sleep duration (`T_alarm`) exceeded | Automatically awaken | Prevents excessive dreaming |

Recommended defaults: `T_think` 30–90 seconds, `T_dream` 5–15 minutes, `T_alarm` 20–30 minutes.

#### 3.3.3 Scheduling Logic
The system monitors agent activity and idle time. A scheduler tracks state transitions, prevents overlapping execution of ThinkingEngine and DreamEngine, and cancels tasks upon user input. When waking, the system logs interruption events and resumes the Active state.

#### 3.3.4 Agent Personality and Sleep Profiles
Scheduling is configurable per agent to support different cognitive styles, e.g. light sleeper, heavy sleeper, daydreamer or strategist.

## 4. Emotion & Personality Integration
- **Mood-Aware Thinking:** Bias prompts and cue selection based on current mood.
- **Emotionally-Influenced Reflection:** Include emotional state summaries in prompts for more human-like introspection.
- **Personality Weighting:** Configure agents to prefer analytic or emotional thought styles.

## 5. Non-Functional Requirements
- **Modularity:** ThinkingEngine must be optional and not affect core logic when disabled.
- **Low Overhead:** Run only during scheduled or idle periods to minimize latency impact.
- **Extensibility:** Developers can define new thought templates, triggers and behavioral modifiers.
- **Traceability:** Each thought must include the prompt, memories used and reason for selection.

## 6. Data Requirements
Each thought entry must store:
- timestamp
- prompt
- context summary
- response
- tags (e.g. `introspection`, `strategy`, `curiosity`)
- emotion and mood at the time of thought

## 7. Evaluation Criteria
- **Thought Quality:** Are thoughts coherent and reflective of memory and state?
- **Memory Contribution:** Do thoughts produce useful memory entries?
- **Emotional Coherence:** Are thoughts aligned with mood and past experiences?
- **Autonomy Enhancement:** Does the system help the agent act proactively?
- **Diversity of Introspection:** Does it generate varied topics and depth?
- **Scheduling Efficiency:** Does it avoid interfering with real-time tasks?

## 8. Glossary
- **ThinkingEngine:** Subsystem for autonomous self-prompting by the agent.
- **Thought Prompt:** Question or statement generated to explore memory or strategy.
- **Introspective Cue:** Retrieval signal built from the agent's own thoughts or goals.
- **Self-Talk:** Internally generated reasoning stored as introspective episodic memory.
- **Cognitive State:** Internal status (Active, Reflective, Asleep) guiding processes.
- **Alarm:** Mechanism to limit maximum time in a non-interactive state.


## License

This documentation is licensed under the [MIT License](../LICENSE). Copyright (c) 2024 Jacob Christ.
