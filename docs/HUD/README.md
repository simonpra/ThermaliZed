# Thermal HUD Engine — Developer Tutorials

Welcome to the in-depth guide for the ThermaliZed HUD Engine. This series of tutorials will teach you how to build professional, responsive, and high-performance overlays for thermal camera data.

## Tutorials

1.  **[Introduction](01-introduction.md)**
    *   What is the HUDEngine?
    *   The Layer system and Mental Model.
    *   Package structure.

2.  **[Drawing Basics](02-drawing-basics.md)**
    *   Primitives vs. Composites.
    *   Canvas Coordinates vs. Sensor Coordinates.
    *   Drawing your first crosshair and smart label.

3.  **[Layers and Clearing](03-layers-and-clearing.md)**
    *   Managing Z-order.
    *   Selective clearing for complex interfaces.
    *   The lifecycle of a single frame.

4.  **[Interaction with TickEngine](04-interaction-with-tickengine.md)**
    *   Handling 30 FPS mouse hover/selection.
    *   The "Dirty" pattern for performance.
    *   Mapping mouse clicks to sensor pixels.

5.  **[Performance and Best Practices](05-performance-and-best-practices.md)**
    *   How memoization and PIL caching work.
    *   Common pitfalls and how to avoid them.
    *   Developer checklist.

---

## Quick Reference

- **Sensor Pixel to Canvas**: `hud.sensor_to_canvas(sx, sy)`
- **Canvas Point to Sensor**: `hud.canvas_to_sensor(cx, cy)`
- **Standard Layer**: `LAYER_MAIN = 100`
- **Recommended FPS**: 30 (for `TickEngine`)
