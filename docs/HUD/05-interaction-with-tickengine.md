# HUD Engine — Part 5: Interaction with TickEngine

If you want a HUD element to follow the mouse (like a hover-tip) or animate, doing it inside the `HUD_DRAW` callback isn't enough. `HUD_DRAW` only fires when the camera provides a new frame. If the camera is slow (9Hz) or frozen, your hover will feel laggy.

The **TickEngine** solves this by providing a separate 30 FPS "heartbeat" loop.

## 1. Setting up the TickEngine

Inside your plugin's `on_load`:

```python
from src.utils.hud import TickEngine

def on_load(self, context):
    self.canvas = context.app.renderer.canvas # or similar
    self._tick = TickEngine(self.canvas, fps=30)
    self._tick.on_tick(self._render_loop)
    self._tick.start()
```

---

## 2. The "Dirty" Pattern

To save CPU, the `TickEngine` doesn't actually run your callback 30 times a second unless something has changed. You must "mark it dirty."

### Example: Mouse Hover

```python
def _on_mouse_move(self, event):
    # Update your internal state (where is the mouse?)
    self.mouse_pos = (event.x, event.y)

    # Tell the TickEngine to run the next render cycle
    self._tick.mark_dirty()

def _render_loop(self):
    # This only runs if mark_dirty() was called
    # Update your canvas items here
    ...
```

---

## 3. Interaction Best Practices

When building an interactive canvas, you usually combine several tools:

### Canvas → Sensor Mapping

Use `hud.canvas_to_sensor(x, y)` to find out which thermal pixel is under the mouse.

```python
def _on_click(self, event):
    pixel = self.hud.canvas_to_sensor(event.x, event.y)
    if pixel:
        col, row = pixel
        # Now you can read the temperature at this pixel!
```

### Layer Separation

A common pattern for a "Pixel Picker" plugin:

- **Layer MAIN**: Draw the selected pixel border. This is cleared and redrawn only when the camera frames come in or the selection changes.
- **Raw Canvas Items**: Draw the hover border. Don't register it with `HUDEngine` layers at all, so `hud.clear()` doesn't delete it. Manage its lifecycle manually in the `TickEngine` loop.

## 4. Teardown

Don't forget to stop the heartbeat when your plugin is unloaded!

```python
def on_unload(self, context):
    self._tick.stop()
```

## Next Steps

In [Part 6: Performance and Best Practices](06-performance-and-best-practices.md), we'll look at how to ensure your HUD stays buttery smooth even with hundreds of items.
