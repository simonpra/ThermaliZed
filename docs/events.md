# Event Bus

The `EventBus` is the central communication hub for ThermaliZed. It enables a decoupled architecture where core logic, plugins, and UI components can interact without direct dependencies.

## Key Concepts

The system utilizes two primary communication patterns:

1.  **Publish/Subscribe (Pub/Sub)**: A one-to-many broadcast mechanism for events like `LOG_MESSAGE` or `APP_QUIT`.
2.  **Pipeline**: A sequential processing chain where each subscriber can modify a data payload (e.g., `RAW_FRAME_PIPELINE`).

---

## API Reference

### `subscribe(event_name, callback)`

Registers a listener for a specific event.

| Argument     | Type       | Description                                   |
| :----------- | :--------- | :-------------------------------------------- |
| `event_name` | `str`      | The unique identifier for the event.          |
| `callback`   | `callable` | The function to execute when the event fires. |

> [!NOTE]
> Callbacks are stored in a simple list; they are executed in the order they were registered.

---

### `unsubscribe(event_name, callback)`

Removes a previously registered listener. Always call this during a plugin's `on_unload` phase to prevent memory leaks and "zombie" callbacks.

---

### `publish(event_name, data=None)`

Broadcasts a payload to all subscribers of a specific event.

| Argument     | Type  | Description                                                       |
| :----------- | :---- | :---------------------------------------------------------------- |
| `event_name` | `str` | The event to trigger.                                             |
| `data`       | `any` | Optional payload passed to the callback (e.g., a string or dict). |

**Pattern: Fire-and-Forget**
The publisher does not receive any feedback from listeners. Errors in individual callbacks are caught and logged to prevent a single listener from crashing the bus.

---

### `pipeline(event_name, data, raw=None)`

Runs a sequential, mutable processing chain. This is the heart of the thermal image processing logic.

| Argument     | Type  | Description                                          |
| :----------- | :---- | :--------------------------------------------------- |
| `event_name` | `str` | The pipeline identifier.                             |
| `data`       | `any` | The initial mutable payload (e.g., a NumPy array).   |
| `raw`        | `any` | Optional immutable reference to the original source. |

**Processing Logic**:

- Subscribers receive `(data, raw)`.
- If a subscriber returns a value that is **not None**, that value becomes the new `data` for the next subscriber in the chain.
- If a subscriber returns **None**, the current `data` is passed through unchanged.
- The method returns the final state of `data` after all subscribers have finished.

---

## Error Handling

The `EventBus` is designed for robustness:

- **Isolation**: Each callback execution is wrapped in a `try/except` block. A failure in one plugin will not stop other plugins from receiving the event.
- **Logging**: Failures are printed to the console with the `[EventBus]` prefix to aid in debugging.

---

## Standard usage in Plugins

```python
class PluginClass(SystemComponent):
    def on_load(self, context):
        # Passive Listening
        context.event_bus.subscribe('COLORMAP_CHANGED', self._on_cmap)

        # Sequential Processing
        context.event_bus.subscribe('RAW_FRAME_PIPELINE', self._process_raw)

    def _on_cmap(self, cmap_name):
        print(f"User selected {cmap_name}")

    def _process_raw(self, data, raw):
        # Modify the 16-bit array
        return data * 1.5
```

> [!TIP]
> For a full list of standard events broadcasted by the core, see the [Plugin Guide](../dev/PLUGIN.md).
