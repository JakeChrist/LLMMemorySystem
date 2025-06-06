# Context Reconstruction

The `Reconstructor` combines retrieved memory fragments into the prompt sent to the LLM. The length of this context is limited by the `max_context_length` option in `config/default_config.yaml`.

The default value is `1000` characters which allows relatively long memory text to be included without truncation. When the final context exceeds this limit the oldest characters are removed so that the last `max_context_length` characters remain.

To adjust the limit for a specific agent, copy `default_config.yaml` and modify the `reconstruction.max_context_length` field. Then pass the path via the agent's configuration loading logic or instantiate `Reconstructor(max_context_length=VALUE)` directly.

