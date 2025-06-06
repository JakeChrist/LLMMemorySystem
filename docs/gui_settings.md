# GUI Scheduler Settings

The Qt interface features a menu bar containing a **Settings** action that opens
a dialog to tweak the idle thresholds used by the `CognitiveScheduler`.

Use the *Settings* action in the window's menu bar to open the dialog. Older
versions exposed a separate button on the side panel. The
fields correspond to:

- `T_think` – seconds of inactivity before background thinking starts.
- `T_dream` – idle time before the DreamEngine is triggered.
- `T_alarm` – maximum duration of dreaming before waking automatically.
- `LMStudio timeout` – request timeout in seconds when using the LMStudio
  backend. Set the value to `0` to wait indefinitely. This option only appears
  when the active LLM is LMStudio.

Changes are applied immediately to the attached scheduler and any running
background tasks are restarted. When using the LMStudio backend, the timeout
for API requests can also be tuned here. Setting the value to ``0`` has the same
effect as exporting ``LMSTUDIO_TIMEOUT=none``.
