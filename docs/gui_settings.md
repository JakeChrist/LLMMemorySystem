# GUI Scheduler Settings

The Qt interface includes a **Settings** dialog allowing you to tweak the idle
thresholds used by the `CognitiveScheduler`.

Open the dialog using the *Settings* button next to **Browse Memories**. The
fields correspond to:

- `T_think` – seconds of inactivity before background thinking starts.
- `T_dream` – idle time before the DreamEngine is triggered.
- `T_alarm` – maximum duration of dreaming before waking automatically.

Changes are applied immediately to the attached scheduler and any running
background tasks are restarted.
