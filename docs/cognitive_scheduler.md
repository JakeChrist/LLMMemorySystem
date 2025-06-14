# Cognitive Scheduler

The cognitive scheduler monitors idle time to drive the agent's internal
processes. It keeps track of the last user interaction and switches between
three states:

- **Active** – recent user input, no background tasks
- **Reflective** – after `T_think` seconds of inactivity the agent thinks for that duration
- **Asleep** – once reflection ends the agent dreams for `T_dream` seconds

Dreaming is automatically stopped after `T_alarm` seconds to prevent endless
sleep. Any user activity immediately wakes the scheduler and cancels running
engines.

The scheduler forwards the agent's configured LLM backend to both the thinking
and dreaming engines so background activities use the same model as interactive
conversations.

## License

This documentation is licensed under the [MIT License](../LICENSE). Copyright (c) 2024 Jacob Christ.
