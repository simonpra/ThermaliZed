# HUD Engine — Part 5: Performance and Best Practices

The HUDEngine is designed to be fast, but as a developer, you should understand how it stays fast to avoid "fighting" the engine.

## 1. Memoization (The `_frame_registry`)

The engine automatically deduplicates identical drawing calls within the **same frame**.

```python
# Calling this twice in one frame...
hud.draw_sensor_crosshair(128, 96, "gold")
hud.draw_sensor_crosshair(128, 96, "gold")

# ...only creates ONE canvas item.
```

The engine generates a "Token" from your arguments. If the token matches an item already drawn in this frame, it just returns the existing ID.
- **Tip**: Avoid using highly dynamic floating point numbers for coordinates if you don't need them (e.g., round to 1 decimal place).

---

## 2. PIL Cache (The `_rect_cache`)

Tkinter cannot natively draw shapes with Alpha transparency (translucent fills). To fix this, HUDEngine uses Pillow to generate images on the fly.

Generating a new Pillow image every frame is slow. To solve this, HUDEngine caches these images based on:
- Width and Height
- Corner Radius
- Fill and Outline colors

**Rule of Thumb**: As long as your label size doesn't change, the background is reused from memory. If your label text is constantly changing length (e.g., "36.5213°C" vs "36.521°C"), it might force a cache miss.
- **Fix**: Use fixed-width formatting for temperature labels (e.g., `f"{temp:5.1f}°C"`).

---

## 3. Common Pitfalls

### Pitfall A: Creating a new `HUDEngine` every frame
**Don't** do this:
```python
def on_draw(self, context):
    hud = HUDEngine(context["canvas"]) # WRONG! Destroys cache every frame.
    hud.clear()
    ...
```
**Do** this:
```python
def on_draw(self, context):
    if self._hud is None:
        self._hud = HUDEngine(context["canvas"])
    hud = self._hud
    hud.clear()
```

### Pitfall B: Forgetting to `clear()`
If you don't call `hud.clear()`, you will leak thousands of canvas items, eventually crashing the application.

### Pitfall C: Drawing in the wrong pipeline
- **Image Enhancement**: Use `RAW_FRAME_PIPELINE`. Do **NOT** draw HUD elements here (math will be wrong).
- **HUD Overlays**: Use `HUD_DRAW`. This fires after the image is positioned, so `canvas.bbox()` works correctly.

---

## 4. Summary Checklist for Plugin Authors

- [ ] Use `HUDEngine` for all overlays.
- [ ] Group related items into Layers (100, 200, etc).
- [ ] Use `draw_sensor_*` methods whenever possible.
- [ ] Call `hud.clear()` at the start of every draw.
- [ ] Call `hud.set_sensor_mapping(...)` before drawing sensor-relative items.
- [ ] Use `TickEngine` for 30 FPS mouse interaction.
- [ ] format temperature strings with fixed precision (e.g., `:.1f`).
