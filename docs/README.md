# ThermaliZed Documentation Index

Welcome to the ThermaliZed developer documentation. This directory contains in-depth references and tutorials for extending the application through plugins and custom visualizations.

---

## Core Architecture

Understanding the "Micro-Core" architecture is essential for building robust plugins.

- **[Application Context](app_context.md)**: The central brain of the app. Manages state, services, and the 30 FPS main loop.
- **[Event Bus & Pipelines](events.md)**: The communication hub. Explains Pub/Sub broadcasting and sequential data processing pipelines.

---

## The HUD Engine

The HUD Engine is a high-level drawing wrapper designed specifically for thermal imaging overlays.

- **[HUD Engine Developer Guide](HUD_ENGINE.md)**: A technical reference for coordinate mapping, the layer system, and high-performance redraw patterns.

---

## HUD Masterclass (Tutorial Series)

A step-by-step guide to building advanced interactive thermal overlays.

1.  **[Introduction to the HUD](HUD/01-introduction.md)**: Core concepts and the rendering lifecycle.
2.  **[Plugin Setup](HUD/02-plugin-setup.md)**: Integrating the engine into your plugin boilerplate.
3.  **[Drawing Basics](HUD/03-drawing-basics.md)**: Working with text, boxes, and crosshairs.
4.  **[Layers & Clearing](HUD/04-layers-and-clearing.md)**: Managing visual depth and Z-ordering.
5.  **[Async Interaction](HUD/05-interaction-with-tickengine.md)**: Using the `TickEngine` for fluid mouse-hover effects.
6.  **[Performance & Best Practices](HUD/06-performance-and-best-practices.md)**: Optimizing your HUD for real-time 30 FPS use.

---

## 🛠️ Plugin Development

- **[Plugin Developer Guide](../dev/PLUGIN.md)**: The "Quickstart" guide found in the `dev/` folder. Start here if you are new to the project.
