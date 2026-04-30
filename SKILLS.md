# ThermaliZed — AI Agent Guidelines

This document contains system-level instructions for AI coding assistants (Antigravity, Cursor, Copilot, etc.) that need to modify, debug, or extend the ThermaliZed repository.

> Read this document in full before making any changes. It encodes hard-won architectural decisions that prevent subtle bugs.

---

## 1. Architecture at a Glance

ThermaliZed uses a **strictly decoupled, event-driven** architecture. No component holds a direct reference to another — all communication flows through the `EventBus`.

```
AppContext  ←  single source of truth
  ├── event_bus      EventBus instance (pub/sub + pipeline)
  ├── state          dict: {'params': {...}, 'devices': [...], 'infos': {...}}
  ├── services       dict: {'camera': ThermalDeviceManager, 'renderer_canvas': tk.Canvas}
  └── plugins        list of loaded SystemComponent instances
```

**Never hardcode cross-component references.** Use `context.event_bus` and `context.get_service()`.

---

## 2. Key Files — What Lives Where

| File / Package | Responsibility |
|---|---|
| `src/core/app_context.py` | Bootstrap, plugin loader, main `after()` loop |
| `src/core/events.py` | `EventBus` — `publish`, `subscribe`, `pipeline` |
| `src/core/plugin_base.py` | `SystemComponent` base class (`on_load`, `get_ui`, `on_unload`) |
| `src/core/processor.py` | Frame processing: 16-bit extraction → pipeline → 8-bit colormap |
| `src/core/device_manager.py` | `ThermalDeviceManager` — cross-platform device abstraction |
| `src/core/components/renderer/` | `ThermalViewFrame` — canvas display + `HUD_DRAW` emission |
| `src/core/components/controls/base.py` | `BaseControlFrame` — styled Tkinter grid + slider helpers |
| `src/core/components/overlay/` | `GradientOverlay`, `HudOverlay`, `CanvasOverlay` |
| `src/utils/hud/` | **HUD Engine package** — see §4 |
| `src/utils/hud_engine.py` | Legacy re-export shim (do not delete) |
| `src/utils/functions.py` | `to_degrees_c(raw)`, `to_raw(celsius)` |
| `src/utils/constants.py` | `DEFAULT_PARAMS`, `COLORMAPS` |
| `plugins/` | External plugins auto-loaded at startup |

---

## 3. The Event Pipeline — Critical Rules

### 3.1 `RAW_FRAME_PIPELINE`
- **Signature**: `def cb(self, data: np.ndarray[uint16], raw: np.ndarray[uint16]) -> np.ndarray | None`
- Fires on every camera frame **before** normalization / colormap.
- `data` may already be modified by a prior plugin; `raw` is always the original sensor output.
- Return the modified array to pass it on; return `None` for pass-through.
- **Do not mutate `raw`** — it is used downstream for temperature math.
- Auto-normalization is computed from `raw`, so pipeline modifications do not corrupt it.

### 3.2 `IMAGE_PIPELINE` (+ `PROCESSED_FRAME_PIPELINE` alias)
- **Signature**: `def cb(self, data: np.ndarray[uint8, BGR], raw: dict) -> np.ndarray | None`
- Fires after the 8-bit BGR heatmap is fully assembled.
- `raw` dict keys: `'8bit'` (reference copy), `'16bit'` (original sensor data), `'thermal_info'`.
- The legacy name `PROCESSED_FRAME_PIPELINE` fires immediately after and carries the same payload.

### 3.3 `HUD_DRAW`
- **Signature**: `def cb(self, hud_context: dict) -> None`
- Fires **after** the canvas image is moved to its final position.
- `hud_context` keys: `'canvas'` (tk.Canvas), `'bbox'` (x1,y1,x2,y2), `'raw_payload'` (same dict as `IMAGE_PIPELINE`'s `raw`).
- **This is the only correct hook for all canvas drawing.** Never draw on the canvas from `RAW_FRAME_PIPELINE` or `IMAGE_PIPELINE`.

### 3.4 Other events

| Event | Direction | Payload |
|---|---|---|
| `FRAME_READY` | publish | `{'frame', 'width', 'height', 'stride', 'timestamp'}` |
| `METADATA_READY` | publish | merged `thermal_info + debug_info + display params` |
| `LOG_MESSAGE` | publish | `str` |
| `APP_QUIT` | publish | `None` |

---

## 4. The HUD Engine Package (`src/utils/hud/`)

### 4.1 Public API (always import from the package root)

```python
from src.utils.hud import HUDEngine, CoordMapper, TickEngine
from src.utils.hud import LAYER_BACKGROUND, LAYER_MAIN, LAYER_INTERACTION, LAYER_TOP
```

The legacy path `from src.utils.hud_engine import HUDEngine` still works (re-export shim) but prefer the package.

### 4.2 Layer constants

| Constant | Value | Purpose |
|---|---|---|
| `LAYER_BACKGROUND` | 0 | Background decorations |
| `LAYER_MAIN` | 100 | Normal HUD (crosshairs, labels) |
| `LAYER_INTERACTION` | 200 | User interaction feedback (selection borders) |
| `LAYER_TOP` | 300 | Always-on-top overlays |

### 4.3 Canonical HUD_DRAW plugin pattern

```python
def _on_hud_draw(self, hud_context):
    canvas  = hud_context.get('canvas')
    bbox    = hud_context.get('bbox')
    raw     = hud_context.get('raw_payload', {})
    raw_16  = raw.get('16bit')

    if not canvas or not bbox or raw_16 is None:
        return

    # Lazy-init or re-init on canvas change
    if self._hud is None or self._hud.canvas is not canvas:
        self._hud = HUDEngine(canvas)
        self._hud.finalize(self.update)   # register for resize redraws

    self._hud.clear()                             # clear all layers
    self._hud.set_sensor_mapping(bbox, raw_16.shape)
    # draw...
```

### 4.4 Selective layer clearing (interactive_canvas pattern)

When a plugin manages two independent visual layers (e.g., hover and selection), clear only the specific layer:

```python
self._hud.clear(layer=LAYER_INTERACTION)  # keeps LAYER_MAIN items intact
```

### 4.5 CoordMapper

`hud.mapper` exposes the sensor ↔ canvas transform without touching the canvas:

```python
cx, cy  = hud.mapper.sensor_to_canvas(sx, sy)    # sensor pixel → canvas
result  = hud.mapper.canvas_to_sensor(cx, cy)    # canvas → sensor pixel (None if outside)
bounds  = hud.mapper.get_pixel_bounds(sx, sy)    # (px, py, px2, py2) for a pixel's bbox
```

### 4.6 TickEngine

Use for hover effects, animations, or any draw loop that must be **independent of the frame rate** (i.e., must also work on a frozen/still frame):

```python
self._tick = TickEngine(canvas, fps=30)
self._tick.on_tick(self._redraw_hover)
self._tick.start()

# In mouse-motion handler:
self._tick.mark_dirty()

# In on_unload:
self._tick.stop()
```

**Critical**: Always call `tick.stop()` in `on_unload`. Failing to do so leaves an orphaned `canvas.after()` loop.

### 4.7 Hover item pattern (raw canvas item, NOT in HUDEngine)

The hover border in `interactive_canvas` is a **raw canvas item** managed directly, not tracked by `HUDEngine`. This avoids `hud.clear()` accidentally deleting it.

```python
# Delete old hover item
if self._hover_item_id is not None:
    canvas.delete(self._hover_item_id)
    self._hover_item_id = None

# Draw new hover item
bounds = hud.mapper.get_pixel_bounds(sx, sy)
if bounds:
    px, py, px2, py2 = bounds
    self._hover_item_id = canvas.create_rectangle(px, py, px2, py2, outline="white", fill="", width=1)
    canvas.tag_raise(self._hover_item_id)
```

---

## 5. Plugin Authoring Rules

1. **One class, one file**: `plugins/<name>/__init__.py` declares exactly one `PluginClass(SystemComponent)`.
2. **Use `on_load` for subscriptions**: subscribe inside `on_load`, not `__init__`. The canvas doesn't exist at `__init__` time.
3. **Never import from another plugin**: plugins are peers; share data only through `context.state` or events.
4. **HUDEngine lazy init**: create `HUDEngine` on first `HUD_DRAW`, not in `__init__` or `on_load` — the canvas is not available yet.
5. **Return discipline in pipelines**: `RAW_FRAME_PIPELINE` and `IMAGE_PIPELINE` handlers **must** return the modified data or `None`. Never return a wrong type.
6. **`on_unload` cleanup**: unsubscribe event listeners, stop `TickEngine`, unbind canvas events.
7. **Guard `winfo_exists()`**: before accessing a Tkinter widget from a callback, check it still exists to avoid `TclError: invalid command name` on shutdown.

---

## 6. Tkinter Threading Model

- All Tkinter calls **must** happen on the main thread.
- `EventBus.publish()` and `EventBus.pipeline()` execute callbacks **synchronously** on the calling thread.
- `TickEngine` uses `canvas.after()` — callbacks run on the main Tkinter thread ✓.
- Do not call `canvas.*` methods from background threads or `threading.Thread` callbacks.

---

## 7. Parameter State

Plugin parameters should be stored in `context.state['params']` and accessed via:

```python
params = self.context.state.get('params', {})
value  = params.get('my_param', default)
params['my_param'] = new_value  # set
```

`BaseControlFrame.params` is a direct reference to `context.state['params']`, so slider callbacks can write directly to it.

---

## 8. Temperature Conversion

The TC001 raw 16-bit values encode temperature as:

```
°C = (raw / 64.0) - 273.15
raw = (°C + 273.15) * 64.0
```

Always use `src.utils.functions.to_degrees_c(raw)` and `to_raw(celsius)` — never inline the formula.

---

## 9. Common Pitfalls

| Pitfall | Correct approach |
|---|---|
| Drawing on canvas from `RAW_FRAME_PIPELINE` | Use `HUD_DRAW` instead |
| Accessing `hud._scale_x` or `hud._image_bbox` | Use `hud.mapper.scale_x`, `hud.mapper.image_bbox` |
| Creating `HUDEngine` in `on_load` | Create lazily on first `HUD_DRAW` |
| Not stopping `TickEngine` on unload | Always call `self._tick.stop()` in `on_unload` |
| Mutating `raw` in `RAW_FRAME_PIPELINE` | Only mutate `data`; `raw` is the ground truth |
| Calling `hud.clear()` when using two independent layers | Use `hud.clear(layer=N)` to target only one layer |
| Canvas calls from a background thread | Always use `canvas.after(0, fn)` to marshal to the main thread |

---

## 10. Adding a New Plugin — Checklist

- [ ] Create `plugins/<my_plugin>/__init__.py`
- [ ] Declare `class PluginClass(SystemComponent)`
- [ ] Implement `on_load(self, context)` — subscribe to relevant events
- [ ] If modifying 16-bit data → subscribe to `RAW_FRAME_PIPELINE`
- [ ] If drawing overlays → subscribe to `HUD_DRAW`, create `HUDEngine` lazily
- [ ] If hover/animation is needed → use `TickEngine`, stop it in `on_unload`
- [ ] If adding UI → implement `get_ui(self, parent_widget, zone)`, return a `ttk.Frame`
- [ ] Implement `on_unload(self, context)` — stop ticks, unbind canvas events
