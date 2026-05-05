# Application Context

The `AppContext` is the central brain of ThermaliZed. It serves as the single source of truth for the application's global state, coordinates the lifecycle of all plugins, and manages the main 30 FPS processing loop.

## Core Responsibilities

1.  **State Management**: Holding global parameters and real-time metadata.
2.  **Plugin Discovery**: Automatically finding and loading components from `src/core/components` and the `plugins/` directory.
3.  **Service Registry**: Providing a central lookup for global services like the `camera`.
4.  **Event Orchestration**: Hosting the central `EventBus` for decoupled communication.

---

## Key Attributes

| Attribute | Type | Description |
| :--- | :--- | :--- |
| `event_bus` | `EventBus` | The primary hub for publishing and subscribing to system events. |
| `state` | `dict` | A dictionary containing globally shared data (params, device lists, metadata). |
| `services` | `dict` | A registry of global singleton services (e.g., the camera manager). |
| `plugins` | `list` | A list of all instantiated and active `PluginClass` objects. |
| `root` | `tk.Tk` | Reference to the main Tkinter root window. |

---

## State Management (`self.state`)

The `state` dictionary is where the application stores its "now" information. Plugins can read from and modify this dictionary to influence app behavior.

### Standard State Keys

| Key | Type | Purpose |
| :--- | :--- | :--- |
| `'params'` | `dict` | Current processing parameters (e.g., colormap, contrast, gamma). |
| `'devices'` | `list[str]` | List of discovered thermal camera names. |
| `'infos'` | `dict` | Real-time frame statistics (Min/Max/Center temperatures). |
| `'frozen_frame_data'` | `dict \| None` | If set, the app bypasses the live camera to display this static data. |

> [!IMPORTANT]
> Always use `DEFAULT_PARAMS` as a reference when initializing plugin settings to ensure compatibility with core components.

---

## Service Registry

Services are global objects that provide specialized functionality. The most common service is the `camera`.

### `register_service(name, service)`
Registers a global service instance. This is typically called during system initialization.

### `get_service(name)`
Retrieves a service by its registered name. 

**Example: Accessing the Camera Service**
```python
camera = context.get_service('camera')
latest_raw = camera.get_latest_frame()
```

---

## The Update Loop

The `AppContext` runs a recurring loop (via `root.after`) at approximately **30 FPS**. On every tick, it performs the following sequence:

1.  **Source Check**: Determines if it should pull from a `frozen_frame_data` or the live `camera` service.
2.  **Broadcast**: Publishes the `FRAME_READY` event to the `event_bus` with the latest frame data.
3.  **Reschedule**: Schedules the next tick to maintain a steady framerate.

> [!NOTE]
> This loop is the primary driver of the processing pipeline. Every time `FRAME_READY` is published, it triggers the sequence of Raw, Image, and HUD pipeline hooks.

---

## Plugin Discovery & Lifecycle

The context uses Python reflection (`pkgutil` and `importlib`) to find plugins.

### Discovery Logic
- **Core Components**: Loaded from `src/core/components`.
- **External Plugins**: Loaded from the `plugins/` directory in the project root.

### Lifecycle Hooks
When a module containing a `PluginClass` is discovered, the context:
1.  **Instantiates** the class.
2.  **Calls `on_load(self)`**, passing itself as the `context`.
3.  **Appends** the instance to `self.plugins`.
4.  **Registers** for cleanup during `on_unload(self)` if initialization fails.

---

> [!TIP]
> For more information on how to interact with the context from a plugin, see the [Plugin Guide](../dev/PLUGIN.md).
