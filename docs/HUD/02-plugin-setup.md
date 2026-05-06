# HUD Engine — Part 2: Plugin Setup

To use the **HUDEngine** in your own plugin, you must integrate it with the application's event system and lifecycle. This guide shows the standard "boilerplate" for a HUD-enabled plugin.

> [!NOTE]
> @see the [hud_example](../../plugins/hud_example/__init__.py) for a full working example.

## 1. Subscribing to the Draw Event

The application fires the `HUD_DRAW` event every time a new frame is ready to be displayed. This is where your drawing logic should live.

```python
from src.core.plugin_base import SystemComponent

class PluginClass(SystemComponent):
    def on_load(self, context):
        # Subscribe to the HUD drawing hook
        context.event_bus.subscribe("HUD_DRAW", self._on_hud_draw)
```

---

## 2. The standard `HUD_DRAW` callback

The callback receives a `hud_context` dictionary containing:

- `canvas`: The Tkinter Canvas widget.
- `bbox`: The current `(x1, y1, x2, y2)` of the image on the canvas.
- `raw_payload`: A dictionary containing the 16-bit thermal data.

```python
def _on_hud_draw(self, hud_context: dict) -> None:
    canvas      = hud_context.get("canvas")
    bbox        = hud_context.get("bbox")
    raw_payload = hud_context.get("raw_payload")

    if not all([canvas, bbox, raw_payload]):
        return

    raw_16bit = raw_payload.get("16bit")

    # Lazy Initialization (Only create the engine once)
    # or if the tkCanvas has changed.
    if self._hud is None or self._hud.canvas is not canvas:
        from src.utils.hud import HUDEngine
        self._hud = HUDEngine(canvas)

    # MAP the sensor space to the canvas space (user screen)
    self._hud.set_sensor_mapping(bbox, raw_16bit.shape)

    # Clear and Redraw
    self._hud.clear()
    self._draw() # Your drawing logic here...
```

---

## 3. Essential Setup Steps

### A. Lazy Initialization

Never create a new `HUDEngine` instance inside the loop. This would destroy the internal caches and severely degrade performance. Reuse the same instance as long as the canvas remains the same.

### B. Setting the Mapping

You **must** call `hud.set_sensor_mapping()` before using any `draw_sensor_*` methods. This function calculates the current zoom level and offsets based on the image's position.

### C. Clearing the HUD

If you don't call `hud.clear()`, items from the previous frame will stay on the canvas forever, leading to a "ghosting" effect and memory leaks.

---

## 4. Full Example: `MyHUDPlugin`

Here is a complete, minimal plugin that draws a crosshair at the center of the sensor.

```python
from src.core.plugin_base import SystemComponent
from src.utils.hud import HUDEngine

class PluginClass(SystemComponent):
    def __init__(self):
        super().__init__()
        self._hud = None

    def on_load(self, context):
        context.event_bus.subscribe("HUD_DRAW", self._on_hud_draw)

    def _on_hud_draw(self, hud_context):
        canvas = hud_context["canvas"]
        bbox = hud_context["bbox"]
        raw_16 = hud_context["raw_payload"]["16bit"]

        # Initialize engine
        if self._hud is None or self._hud.canvas is not canvas:
            self._hud = HUDEngine(canvas)

        # For conveniance
        hud = self._hud

        # Setup mapping
        hud.set_sensor_mapping(bbox, raw_16.shape)

        # Draw logic
        hud.clear()

        # Draw a crosshair at center (128, 96)
        hud.draw_sensor_crosshair(sx=128, sy=96, color="cyan")

        # Add a label
        hud.draw_sensor_smart_text(sx=128, sy=96, text="Sensor Center")

    def on_unload(self, context):
        # Good practice: clear the HUD when plugin is removed
        if self._hud:
            self._hud.clear()
```

## Next Steps

In [Part 3: Drawing Basics](03-drawing-basics.md), we will explore the library of shapes and labels available to you.
