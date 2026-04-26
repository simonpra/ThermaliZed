# HUD Engine — Developer Guide

A modular, layer-aware HUD drawing engine for Tkinter canvas overlays.

---

## Quickstart — Drawing Your First Temperature Label

```python
from src.utils.hud import HUDEngine

# Inside a HUD_DRAW callback:
def _on_hud_draw(self, hud_context):
    canvas = hud_context["canvas"]
    bbox   = hud_context["bbox"]
    raw    = hud_context["raw_payload"]["16bit"]

    if self._hud is None or self._hud.canvas is not canvas:
        self._hud = HUDEngine(canvas)

    hud = self._hud
    hud.clear()
    hud.set_sensor_mapping(bbox, raw.shape)

    # Draw a gold label at sensor pixel (col=128, row=96)
    hud.draw_sensor_smart_text(
        128, 96,
        text="37.5 °C",
        color="#FFD700",
        bg_color=(0, 0, 0, 180),  # semi-transparent black
    )
```

---

## Package Structure

```
src/utils/hud/
├── __init__.py          ← Public API entry point
├── core.py              ← HUDEngine class
├── mapper.py            ← CoordMapper (sensor ↔ canvas)
├── interaction.py       ← TickEngine (async hover pipeline)
└── library/
    ├── primitives.py    ← create_text, create_rounded_rect, create_svg_icon
    ├── composites.py    ← create_crosshair, create_text_rect, create_smart_text
    └── thermal.py       ← create_sensor_pixel_rect, create_sensor_crosshair, ...
```

---

## Layer System

Canvas items are organised into **named layers** (integer z-index, multiples of 100).

| Constant           | Value | Typical use                                    |
|--------------------|-------|------------------------------------------------|
| `LAYER_BACKGROUND` | 0     | Background fills, scale bars                   |
| `LAYER_MAIN`       | 100   | Default — crosshairs, temperature labels       |
| `LAYER_INTERACTION`| 200   | Selection borders (pixel picker)               |
| `LAYER_TOP`        | 300   | Always-on-top items (debugging overlays, etc.) |

```python
from src.utils.hud import HUDEngine, LAYER_INTERACTION

hud.draw_sensor_pixel_rect(sx, sy, color="#FFD700", layer=LAYER_INTERACTION)
```

### Selective Clearing

```python
hud.clear()                   # clear ALL layers
hud.clear(layer=LAYER_INTERACTION)  # clear only the interaction layer
```

This is the key trick used by `interactive_canvas`: the hover border lives as a raw canvas item (never in `HUDEngine`), while the selection border lives in `LAYER_INTERACTION`.  Calling `hud.clear(layer=LAYER_INTERACTION)` removes the selection without touching the hover.

---

## Sync vs Async Pipelines

### Sync Pipeline — `HUD_DRAW` event

Fired by the renderer after each camera frame is placed on the canvas.  Use this for data-driven overlays that need the latest sensor values.

```python
context.event_bus.subscribe("HUD_DRAW", self._on_hud_draw)
```

### Async Pipeline — `TickEngine`

For hover effects, animations, and UI feedback that must remain fluid even when the camera is frozen.

```python
from src.utils.hud import TickEngine

tick = TickEngine(canvas, fps=30)
tick.on_tick(self._redraw_hover)
tick.start()

# From a mouse handler:
tick.mark_dirty()   # next tick will call _redraw_hover()

# On teardown:
tick.stop()
```

---

## Coordinate Mapping

`HUDEngine` exposes a `mapper` attribute (a `CoordMapper` instance):

```python
hud.set_sensor_mapping(bbox, raw.shape)

# Sensor → Canvas
cx, cy = hud.sensor_to_canvas(sx, sy)

# Canvas → Sensor (returns None if outside image)
pixel = hud.canvas_to_sensor(event.x, event.y)

# Get bounding box of a sensor pixel on canvas
px, py, px2, py2 = hud.mapper.get_pixel_bounds(sx, sy)
```

`CoordMapper` can also be used standalone (no Tkinter dependency):

```python
from src.utils.hud.mapper import CoordMapper

m = CoordMapper()
m.set_mapping(image_bbox=(10, 10, 266, 202), sensor_shape=(192, 256))
cx, cy = m.sensor_to_canvas(128, 96)
```

---

## Public API Reference

### `HUDEngine`

| Method | Description |
|--------|-------------|
| `clear(layer=None)` | Remove canvas items (all layers or one) |
| `set_sensor_mapping(bbox, shape)` | Configure coord transform |
| `sensor_to_canvas(sx, sy)` | Sensor → canvas coords |
| `canvas_to_sensor(cx, cy)` | Canvas → sensor pixel |
| `draw_text(x, y, text, color, ...)` | Primitive text |
| `draw_rounded_rect(x1, y1, x2, y2, radius, fill_rgba, ...)` | Alpha rect |
| `draw_svg_icon(x, y, filepath, ...)` | SVG icon (Tk 9+) |
| `draw_crosshair(cx, cy, color, ...)` | Four-arm crosshair |
| `draw_text_rect(x, y, text, color, bg_color, ...)` | Text + background |
| `draw_smart_text(x, y, text, color, ...)` | Edge-clamped label |
| `draw_sensor_pixel_rect(sx, sy, color, ...)` | Pixel border (sensor coords) |
| `draw_sensor_crosshair(sx, sy, color, ...)` | Crosshair (sensor coords) |
| `draw_sensor_smart_text(sx, sy, text, color, ...)` | Label (sensor coords) |
| `finalize(draw_fn)` | Register resize hook |
| `update()` | Replay the registered draw function |

All drawing methods accept an optional `layer: int` kwarg (default `LAYER_MAIN = 100`).

### `TickEngine`

| Method | Description |
|--------|-------------|
| `start()` | Begin the after() loop |
| `stop()` | Stop on the next iteration |
| `mark_dirty()` | Request a redraw on the next tick |
| `on_tick(callback)` | Register a zero-arg callback |
| `remove_tick(callback)` | Unregister a callback |
| `is_dirty` | Property — True if a redraw is pending |

---

## Performance Tips

### Use sensor-mapped methods for data overlays

`draw_sensor_crosshair` and `draw_sensor_smart_text` handle the coordinate transform internally so plugin code stays clean.

### Composites vs Primitives

- **Use composites** (`draw_smart_text`, `draw_text_rect`) for most overlays — they handle edge clamping, background sizing, and z-ordering automatically.
- **Use primitives** (`draw_text`, `draw_rounded_rect`) only when you need fine-grained control (e.g. a custom layout that doesn't fit the composite API).

### Frame deduplication

`HUDEngine` deduplicates identical drawing calls within the same frame via `_frame_registry`.  Calling `draw_crosshair(128, 96, "red")` twice in one frame creates only one canvas item.

### PIL image memoisation

`draw_rounded_rect` caches PIL images by `(w, h, radius, fill, outline)` in `_rect_cache` across frames.  At 30 FPS, a label that doesn't change geometry never re-creates a PIL image.

---

## Handling Mouse Clicks on Sensor Pixels

```python
def _on_click(self, event: tk.Event) -> None:
    pixel = self._hud.canvas_to_sensor(event.x, event.y)
    if pixel is not None:
        col, row = pixel
        raw_val  = self._raw_16bit[row, col]
        print(f"Clicked pixel ({col}, {row}) = {raw_val}")
```

`canvas_to_sensor` returns `None` when the click is outside the rendered image area, so no bounds checking is needed.
