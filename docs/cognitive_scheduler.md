# Cognitive Scheduler

The cognitive scheduler monitors idle time to drive the agent's internal
processes. It keeps track of the last user interaction and switches between
three states:

- **Active** – recent user input, no background tasks
- **Reflective** – idle for `T_think` seconds, starts the ThinkingEngine
- **Asleep** – idle for `T_dream` seconds, starts the DreamEngine

Dreaming is automatically stopped after `T_alarm` seconds to prevent endless
sleep. Any user activity immediately wakes the scheduler and cancels running
engines.
