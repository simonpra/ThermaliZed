# Thermal HUD Engine — Developer Tutorials

Welcome to the in-depth guide for the ThermaliZed HUD Engine. This series of tutorials will teach you how to build professional, responsive, and high-performance overlays for thermal camera data.

## Tutorials

1.  **[Introduction](01-introduction.md)**
    *   What is the HUDEngine?
    *   The Layer system and Mental Model.
    *   Package structure.

2.  **[Plugin Setup](02-plugin-setup.md)**
    *   Subscribing to `HUD_DRAW`.
    *   Lazy initialization of the engine.
    *   Standard callback structure and boilerplate.

3.  **[Drawing Basics](03-drawing-basics.md)**
    *   Primitives vs. Composites.
    *   Canvas Coordinates vs. Sensor Coordinates.
    *   Drawing your first crosshair and smart label.

4.  **[Layers and Clearing](04-layers-and-clearing.md)**
    *   Managing Z-order.
    *   Selective clearing for complex interfaces.
    *   The lifecycle of a single frame.

5.  **[Interaction with TickEngine](05-interaction-with-tickengine.md)**
    *   Handling 30 FPS mouse hover/selection.
    *   The "Dirty" pattern for performance.
    *   Mapping mouse clicks to sensor pixels.

6.  **[Performance and Best Practices](06-performance-and-best-practices.md)**
    *   How memoization and PIL caching work.
    *   Common pitfalls and how to avoid them.
    *   Developer checklist.

---

## Quick Reference

- **Sensor Pixel to Canvas**: `hud.sensor_to_canvas(sx, sy)`
- **Canvas Point to Sensor**: `hud.canvas_to_sensor(cx, cy)`
- **Standard Layer**: `LAYER_MAIN = 100`
- **Recommended FPS**: 30 (for `TickEngine`)
