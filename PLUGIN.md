# ThermaliZed Plugin Guide

Welcome to the ThermaliZed plugin ecosystem. The application is designed to be highly modular, relying on an internal `EventBus` to handle communication between the camera, the data processors, and the UI. This guide will show you how to write a simple plugin.

## Core Concepts

All plugins live in the `plugins/` directory and are automatically discovered upon launching `main.py`.

To be recognized by the system, your plugin folder must contain an `__init__.py` file that defines a `PluginClass`. This class must inherit from `SystemComponent` (found in `src.core.plugin_base`).

### The SystemComponent Lifecycle
Your plugin can override the following hooks:
1. `on_load(self, context)`: Called when the plugin is discovered. This is where you subscribe to events or register services.
2. `get_ui(self, parent_widget, zone)`: Called during UI construction. You return a `ttk.Frame` (or any widget) to be injected into a specific `zone` (e.g., `left_sidebar`, `main_content`). Return `None` if your plugin has no UI.
3. `on_unload(self, context)`: Called on application exit for cleanup.

## The Event Bus & Pipeline

The system uses `context.event_bus` to broadcast data. There are two primary ways to interact with data:

### 1. `subscribe(event_name, callback)`
Use this to simply listen for data without modifying it.
```python
self.context.event_bus.subscribe('APP_QUIT', self.on_quit)
```

### 2. The Mutable Pipeline `pipeline(event_name, data, raw)`
For things like thermal image processing, the system passes data through a sequential pipeline. Subscribers to a pipeline event (like `RAW_FRAME_PIPELINE`) receive the current `data` and the originally captured `raw` data. If your callback returns a value, it replaces `data` for the next plugin in the chain.

## Quick Start Example

Here is a basic plugin that prints the min/max temperature of every frame.

**File:** `plugins/my_logger/__init__.py`

```python
import numpy as np
from src.core.plugin_base import SystemComponent

class PluginClass(SystemComponent):
    def on_load(self, context):
        self.context = context
        # Subscribe to the pipeline to view the thermal data
        self.context.event_bus.subscribe('RAW_FRAME_PIPELINE', self.process_frame)
        self.context.event_bus.publish('LOG_MESSAGE', "MyLogger Plugin Loaded!")

    def process_frame(self, data, raw):
        if raw is not None:
            min_temp = np.min(raw)
            max_temp = np.max(raw)
            # You could publish this to the LOG_MESSAGE event or standard output
            print(f"Min Temp: {min_temp:.2f}, Max Temp: {max_temp:.2f}")
        
        # We do not modify the data, so returning None passes it through unchanged.
        return None
```
