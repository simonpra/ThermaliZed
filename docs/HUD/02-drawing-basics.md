# HUD Engine — Part 2: Drawing Basics

Drawing on the HUD is divided into two categories: **Primitives** (simple shapes) and **Composites** (complex widgets made of multiple shapes).

## 1. Prerequisites: Setting up the Mapping

Before the engine can draw anything relative to the thermal image, it needs to know where that image is on the canvas.

```python
# Typically done at the start of a draw callback
hud.set_sensor_mapping(image_bbox, sensor_shape)
```
- `image_bbox`: `(x1, y1, x2, y2)` of the image on the canvas.
- `sensor_shape`: `(height, width)` of the raw data (e.g., `(192, 256)`).

---

## 2. Sensor-Relative Drawing (Recommended)

This is the most powerful feature. You provide a pixel column (`sx`) and row (`sy`) from the thermal sensor, and the engine handles the rest.

### `draw_sensor_crosshair`
Draws a classic 4-arm crosshair centered on a sensor pixel.
```python
hud.draw_sensor_crosshair(sx=128, sy=96, color="red")
```

### `draw_sensor_smart_text`
Draws a label (like a temperature) that is "edge-aware." If the pixel is at the very top of the screen, the label will automatically flip to appear below the pixel so it doesn't get cut off.
```python
hud.draw_sensor_smart_text(sx=128, sy=96, text="36.5°C", color="white", bg_color=(0,0,0,150))
```

### `draw_sensor_pixel_rect`
Draws a perfect border around the screen area occupied by a single sensor pixel. Useful for selection highlighting.
```python
hud.draw_sensor_pixel_rect(sx=10, sy=20, color="cyan", width=2)
```

---

## 3. Canvas-Relative Drawing

Sometimes you want to draw things that *don't* move with the image (like a logo, a scale bar, or a title). Use the "Raw" primitives for this.

```python
# Draw text at absolute canvas coordinates (10, 10)
hud.draw_text(10, 10, "ThermaliZed v1.0", color="gray", anchor="nw")

# Draw a rounded rectangle background
hud.draw_rounded_rect(5, 5, 100, 30, radius=10, fill_rgba=(50, 50, 50, 200))
```

---

## 4. Primitives vs. Composites

| Type | Examples | Description |
| :--- | :--- | :--- |
| **Primitives** | `draw_text`, `draw_rounded_rect`, `draw_svg_icon` | Single Tkinter canvas items. Low level. |
| **Composites** | `draw_crosshair`, `draw_text_rect`, `draw_smart_text` | Groups of primitives (e.g., a Box + Text). They return a list of IDs. |

### Pro-Tip: Smart Color Arguments
Most drawing functions accept `fill_rgba` which can be:
- A simple string: `"red"`, `"#FF0000"`.
- A tuple with Alpha: `(255, 0, 0, 128)` for 50% transparent red.

## Next Steps

In [Part 3: Layers and Clearing](03-layers-and-clearing.md), we'll see how to manage multiple overlays without them clobbering each other.
