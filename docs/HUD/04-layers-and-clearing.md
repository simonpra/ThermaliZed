# HUD Engine — Part 4: Layers and Clearing

Managing a complex HUD with multiple plugins requires a way to organize items so they don't overlap in messy ways. The HUDEngine uses a **Layer System**.

## 1. How Layers Work

Every drawing method (`draw_text`, `draw_sensor_crosshair`, etc.) accepts an optional `layer` argument.

```python
from src.utils.hud import LAYER_BACKGROUND, LAYER_INTERACTION

# Draw on the default layer (100)
hud.draw_sensor_crosshair(128, 96, "red")

# Draw behind everything
hud.draw_text(10, 10, "Status: OK", color="green", layer=LAYER_BACKGROUND)

# Draw a selection border on top
hud.draw_sensor_pixel_rect(10, 10, color="yellow", layer=LAYER_INTERACTION)
```

### Why use Layers?
1.  **Z-Ordering**: High layer numbers are drawn "on top" of lower ones.
2.  **Selective Clearing**: You can wipe one layer without touching others.

---

## 2. The Clearing Strategy

In a real-time application (30 FPS), we usually clear the HUD and redraw it every frame.

### Global Clear
This removes **everything** managed by the engine.
```python
hud.clear()
```

### Selective Clear
This is useful if you have a layer that updates less frequently than others (like a static legend) or a layer driven by a different loop (like a hover effect).
```python
# Clear ONLY the interaction layer
hud.clear(layer=LAYER_INTERACTION)
```

---

## 3. The Lifecycle of a Frame

Typically, a plugin's `HUD_DRAW` callback follows this pattern:

1.  **Check/Init**: Ensure `self._hud` exists and is attached to the current canvas.
2.  **Clear**: Call `hud.clear()` to remove the previous frame's items.
3.  **Map**: Call `hud.set_sensor_mapping(...)` with current image bounds.
4.  **Draw**: Call your drawing functions.
5.  **Finalize (Optional)**: If you want this HUD to automatically redraw when the window is resized, use `hud.finalize(self.update)`.

### Example:
```python
def on_hud_draw(self, hud_context):
    hud = self._get_hud(hud_context["canvas"]) # Lazy helper
    
    hud.clear()
    hud.set_sensor_mapping(hud_context["bbox"], hud_context["raw"].shape)
    
    # Do your drawing here...
    hud.draw_sensor_smart_text(...)
```

## Next Steps

In [Part 5: Interaction with TickEngine](05-interaction-with-tickengine.md), we'll learn how to make the HUD responsive to mouse movement without lagging the main video feed.
