# ThermaliZed AI Agent Guidelines

This document provides system instructions for AI coding assistants attempting to modify, refactor, or write plugins for the ThermaliZed repository.

## Architecture & State

ThermaliZed uses a strictly decoupled architecture. Never hardcode references between UI components and core systems.
- **Global Context:** All state is managed by `@file:src/core/app_context.py`. Use it as the single source of truth for the camera service and `EventBus`.
- **Event Bus:** Read the `EventBus` implementation in `@file:src/core/events.py`. Note the difference between `publish()` (fire and forget) and `pipeline()` (sequential mutation).

## Building Plugins

When asked to build a new feature:
1. Create a subfolder in `plugins/`.
2. Inside the folder, create `__init__.py`.
3. In `__init__.py`, you MUST declare a class named exactly `PluginClass` that inherits from `SystemComponent` located in `@file:src/core/plugin_base.py`.

### Pipeline Rule
If your plugin modifies thermal data (like adjusting contrast, overlaying gradients, or doing AI detection), subscribe to the `RAW_FRAME_PIPELINE` event.
Your callback signature must be exactly `def my_callback(self, data, raw)`. 
- `data`: The current processed numpy array.
- `raw`: The unmodified 16-bit sensor array.

**Critical Rule:** If your handler modifies the image, it **must** return the modified array. If it only reads the array, it **must** return `None`.

### UI Injection
To add visual controls, implement `def get_ui(self, parent_widget, zone):`. Check the requested `zone` string (e.g., `'right_panel'`, `'left_sidebar'`). Return a Tkinter widget. Inherit styled components from `src.gui.components` where possible rather than applying raw Tkinter configuration elements manually.
