# ThermaliZed Plugin Guide

Welcome to the ThermaliZed plugin ecosystem. The application uses an internal `EventBus` to handle all communication between the camera, data processors, renderers, and the UI. This guide shows you how to write plugins that tap into any of those layers.

## Core Concepts

All plugins live in the `plugins/` directory and are automatically discovered on startup.

Each plugin folder must contain an `__init__.py` that declares a class named exactly **`PluginClass`** inheriting from `SystemComponent` (found in `src.core.plugin_base`).

### The SystemComponent Lifecycle

Override any of these three hooks as needed:

| Hook                                | When it fires                | Typical use                             |
| ----------------------------------- | ---------------------------- | --------------------------------------- |
| `on_load(self, context)`            | Plugin discovered at startup | Subscribe to events, store context      |
| `get_ui(self, parent_widget, zone)` | UI layout is being built     | Return a `ttk.Frame` for the given zone |
| `on_unload(self, context)`          | Application is shutting down | Stop threads, unbind events             |

Return `None` from `get_ui` if your plugin has no UI.

---

## The Event Bus

`context.event_bus` is the central communication hub.

### `publish(event_name, data)` — fire-and-forget

```python
self.context.event_bus.publish('LOG_MESSAGE', "My plugin loaded!")
```

### `subscribe(event_name, callback)` — passive listener

```python
self.context.event_bus.subscribe('APP_QUIT', self._on_quit)
```

### `pipeline(event_name, data, raw)` — sequential mutable pipeline

Subscribers receive `(data, raw)`. Return a modified array to replace `data` for the next stage; return `None` to pass through unchanged.

---

## The Three Pipeline Hooks

### 1. `RAW_FRAME_PIPELINE` — 16-bit sensor data

Fires immediately after the raw 16-bit thermal array is assembled, **before** any normalization or colormap.

```
callback(data: np.ndarray[uint16], raw: np.ndarray[uint16]) -> np.ndarray | None
```

- `data` — current (possibly modified) 16-bit array (shape: `H × W`, dtype `uint16`)
- `raw` — original unmodified sensor array — **never mutate this**
- Return the modified array, or `None` for pass-through

```python
def _on_raw_frame(self, data, raw):
    # Example: invert the thermal range
    return np.max(raw) - data + np.min(raw)
```

### 2. `IMAGE_PIPELINE` — 8-bit BGR heatmap

Fires after the final 8-bit colorized heatmap is produced.

```
callback(data: np.ndarray[uint8, BGR], raw: dict) -> np.ndarray | None
```

The `raw` dict contains:

- `'8bit'` → reference copy of the original 8-bit heatmap
- `'16bit'` → `original_raw_16bit` for temperature math
- `'thermal_info'` → dict with `min_raw`, `max_raw`, `norm_min`, `norm_max`, `min_c`, `max_c`

### 3. `HUD_DRAW` — Canvas overlay hook

Fires **after** the thermal image is placed at its final position on the Tkinter canvas. This is the correct hook for all canvas drawing (crosshairs, labels, borders).

```
callback(hud_context: dict) -> None
```

The `hud_context` dict contains:

- `'canvas'` → `tk.Canvas` — the main display canvas
- `'bbox'` → `(x1, y1, x2, y2)` — pixel bounding box of the rendered image on the canvas
- `'raw_payload'` → same dict as `IMAGE_PIPELINE`'s `raw` argument (`'8bit'`, `'16bit'`, `'thermal_info'`)

```python
def _on_hud_draw(self, hud_context):
    canvas = hud_context.get('canvas')
    bbox   = hud_context.get('bbox')
    raw    = hud_context.get('raw_payload', {})
    raw_16 = raw.get('16bit')
    # ... draw on canvas
```

---

## The HUD Engine

`HUDEngine` is a high-level drawing wrapper for the Tkinter canvas. It handles:

- **Layer registry** — z-ordered layers (`LAYER_BACKGROUND=0`, `LAYER_MAIN=100`, `LAYER_INTERACTION=200`, `LAYER_TOP=300`)
- **Automatic cleanup** — `hud.clear()` or `hud.clear(layer=N)` removes only the items in a given layer
- **Alpha-transparent rounded rects** — via Pillow, memoised across frames
- **Smart text** — edge-clamped labels that never bleed off canvas
- **Sensor coordinate mapping** — draw using raw sensor pixel indices, regardless of zoom

### Importing

```python
from src.utils.hud import HUDEngine, LAYER_MAIN, LAYER_INTERACTION
```

### Setting up in `HUD_DRAW`

```python
def _on_hud_draw(self, hud_context):
    canvas = hud_context['canvas']
    bbox   = hud_context['bbox']
    raw    = hud_context['raw_payload']
    raw_16 = raw['16bit']

    if self._hud is None or self._hud.canvas is not canvas:
        self._hud = HUDEngine(canvas)

    self._hud.clear()
    self._hud.set_sensor_mapping(bbox, raw_16.shape)
    # ... draw
```

### Key HUDEngine Methods

| Method                                                      | Description                                                             |
| ----------------------------------------------------------- | ----------------------------------------------------------------------- |
| `set_sensor_mapping(bbox, sensor_shape)`                    | Configure sensor→canvas transform                                       |
| `sensor_to_canvas(sx, sy)`                                  | Convert sensor pixel to canvas coords                                   |
| `canvas_to_sensor(cx, cy)`                                  | Convert canvas coords to sensor pixel (returns `None` if outside image) |
| `clear(layer=None)`                                         | Remove all items or only a specific layer                               |
| `draw_text(x, y, text, color, ...)`                         | Simple canvas text                                                      |
| `draw_rounded_rect(x1, y1, x2, y2, radius, fill_rgba, ...)` | Alpha-transparent pill / badge                                          |
| `draw_crosshair(cx, cy, color, ...)`                        | Four-arm crosshair                                                      |
| `draw_text_rect(x, y, text, color, bg_color, ...)`          | Text with auto-sized background badge                                   |
| `draw_smart_text(x, y, text, color, ...)`                   | Edge-clamped label                                                      |
| `draw_sensor_pixel_rect(sx, sy, color, ...)`                | Border around a sensor pixel                                            |
| `draw_sensor_crosshair(sx, sy, color, ...)`                 | Crosshair at sensor coords                                              |
| `draw_sensor_smart_text(sx, sy, text, color, ...)`          | Edge-clamped label at sensor coords                                     |
| `finalize(draw_fn)`                                         | Register a zero-arg callable to replay on resize                        |

---

## The TickEngine (Async Redraw)

Use `TickEngine` when you need a draw loop that is **independent of the camera frame rate** — e.g., hover effects that must work on frozen / still frames.

```python
from src.utils.hud import TickEngine

self._tick = TickEngine(canvas, fps=30)
self._tick.on_tick(self._my_callback)
self._tick.start()

# From a mouse-motion handler:
self._tick.mark_dirty()

# On plugin teardown:
self._tick.stop()
```

The engine calls registered callbacks only when `mark_dirty()` has been called since the last tick, keeping CPU overhead near zero when nothing changes.

---

## Quick-Start Examples

### Example 1 — 16-bit pipeline modifier (no UI)

```python
# plugins/my_logger/__init__.py
import numpy as np
from src.core.plugin_base import SystemComponent

class PluginClass(SystemComponent):
    def on_load(self, context):
        self.context = context
        context.event_bus.subscribe('RAW_FRAME_PIPELINE', self._on_frame)
        context.event_bus.publish('LOG_MESSAGE', "MyLogger loaded!")

    def _on_frame(self, data, raw):
        print(f"Min: {np.min(raw)}, Max: {np.max(raw)}")
        return None  # pass-through
```

### Example 2 — HUD overlay with sensor coordinates

```python
# plugins/my_hud/__init__.py
import cv2
from src.core.plugin_base import SystemComponent
from src.utils.hud import HUDEngine, LAYER_MAIN

class PluginClass(SystemComponent):
    def __init__(self):
        super().__init__()
        self._hud = None

    def on_load(self, context):
        self.context = context
        context.event_bus.subscribe('HUD_DRAW', self._on_hud_draw)

    def _on_hud_draw(self, hud_context):
        canvas = hud_context.get('canvas')
        bbox   = hud_context.get('bbox')
        raw    = hud_context.get('raw_payload', {})
        raw_16 = raw.get('16bit')
        if not canvas or not bbox or raw_16 is None:
            return

        if self._hud is None or self._hud.canvas is not canvas:
            self._hud = HUDEngine(canvas)

        self._hud.clear()
        self._hud.set_sensor_mapping(bbox, raw_16.shape)

        _, _, min_loc, max_loc = cv2.minMaxLoc(raw_16)
        self._hud.draw_sensor_crosshair(max_loc[0], max_loc[1], color='red',   layer=LAYER_MAIN)
        self._hud.draw_sensor_crosshair(min_loc[0], min_loc[1], color='cyan',  layer=LAYER_MAIN)
```

### Example 3 — Sidebar UI controls

```python
# plugins/my_controls/__init__.py
import tkinter as tk
from tkinter import ttk
from src.core.plugin_base import SystemComponent
from src.core.components.controls.base import BaseControlFrame

class MyFrame(BaseControlFrame):
    def __init__(self, parent, context, **kwargs):
        super().__init__(parent, context=context, **kwargs)
        self.my_var = tk.DoubleVar(value=self.params.get('my_param', 1.0))
        self.add_section_header(0, "My Plugin")
        self.add_label_slider(1, "My Value:", self.my_var, 0.0, 2.0, 0.1, self._on_change)

    def _on_change(self, _=None):
        self.params['my_param'] = round(float(self.my_var.get()), 1)

class PluginClass(SystemComponent):
    def on_load(self, context):
        self.context = context

    def get_ui(self, parent_widget, zone):
        if zone == 'left_sidebar':
            wrapper = ttk.Frame(parent_widget)
            MyFrame(wrapper, self.context).pack(fill=tk.BOTH)
            return wrapper
        return None
```

---

## UI Zones

| Zone string      | Location                          |
| ---------------- | --------------------------------- |
| `'left_sidebar'` | Left panel — sliders and controls |
| `'main_content'` | Centre — the main canvas area     |
| `'bottom_bar'`   | Bottom status / console strip     |

---

## Useful Utilities

| Import                                  | Purpose                                    |
| --------------------------------------- | ------------------------------------------ |
| `src.utils.functions.to_degrees_c(raw)` | Convert TC001 uint16 raw value to °C       |
| `src.utils.functions.to_raw(celsius)`   | Convert °C back to TC001 uint16            |
| `src.utils.constants.COLORMAPS`         | List of `(cv2_code, name)` colormap tuples |
| `src.utils.constants.DEFAULT_PARAMS`    | Default processing parameter dict          |
