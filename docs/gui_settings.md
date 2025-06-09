# GUI Scheduler Settings

The Qt interface features a menu bar containing a **Settings** action that opens
a dialog.  In addition to the scheduler thresholds it allows switching the
active LLM backend and the database file.

Use the *Settings* action in the window's menu bar to open the dialog. Older
versions exposed a separate button on the side panel. The
fields correspond to:

- `T_think` – seconds of inactivity before background thinking starts.
- `T_dream` – idle time before the DreamEngine is triggered.
- `T_alarm` – maximum duration of dreaming before waking automatically.
- `LLM backend` – selects which language model implementation to use.
- `Database file` – location of the SQLite memory store.
- `LMStudio timeout` – request timeout in seconds when using the LMStudio
  backend. Set the value to `0` to wait indefinitely. This option only appears
  when the active LLM is LMStudio.

`T_think` and `T_dream` also determine how frequently the thinking and dreaming
engines run once started. Lower values result in more frequent background
updates.

Changes are applied immediately to the attached scheduler and any running
background tasks are restarted. When using the LMStudio backend, the timeout
for API requests can also be tuned here. Setting the value to ``0`` has the same
effect as exporting ``LMSTUDIO_TIMEOUT=none``.

## Persistence

The values chosen in the settings dialog are saved to
``~/.llmemory_gui.json``. When the GUI starts again these settings are
loaded automatically so the scheduler and LLM options continue from the
previous session.

## License

This documentation is licensed under the [MIT License](../LICENSE). Copyright (c) 2024 Jacob Christ.
