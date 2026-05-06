# Changelog

All notable changes to the Thermal Viewer application will be documented in this file.

## [0.1.1-alpha] - 2026-05-06

### Added

- **HUD Engine Tutorial Series** (`docs/HUD/`): A comprehensive six-part developer guide:
  - `01-introduction.md` — Conceptual architecture and layer mental model.
  - `02-plugin-setup.md` — Standard boilerplate and lifecycle integration.
  - `03-drawing-basics.md` — Library of primitives and composites.
  - `04-layers-and-clearing.md` — Advanced Z-index management and selective clearing.
  - `05-interaction-with-tickengine.md` — High-frequency async redraws for hover effects.
  - `06-performance-and-best-practices.md` — Memoization, lazy init, and optimization tips.
- **Internal Core Documentation**:
  - `docs/app_context.md`: Deep dive into the `AppContext` state, services, and 30 FPS loop.
  - `docs/events.md`: Detailed explanation of the `EventBus` Pub/Sub and Pipeline patterns.

### Changed

- **Developer Guide Refactor** (`docs/PLUGIN.md`): Rewritten to emphasize the "Micro-Core" architecture and provide clearer examples of pipeline hooks.
- **Path Standardization**: Moved development-specific files like `SKILLS.md` into the `dev/` directory for better repository organization.

### Fixed

- **Documentation Links**: Audited and corrected broken internal links and relative paths across the entire `docs/` directory.

## [0.1.0-alpha] - 2026-04-30

### Added

- **HUD Engine Package** (`src/utils/hud/`): Refactored the monolithic `hud_engine.py` (580 lines) into a clean, modular package:
  - `core.py` — `HUDEngine` class with layer-aware registry, frame deduplication, and PIL memoisation.
  - `mapper.py` — `CoordMapper`, a Tkinter-free class for sensor ↔ canvas coordinate transforms. Usable and testable independently of any GUI.
  - `interaction.py` — `TickEngine`, a reusable async redraw driver built on `canvas.after()`.
  - `library/primitives.py` — Stateless canvas creators: `create_text`, `create_rounded_rect`, `create_svg_icon`.
  - `library/composites.py` — Higher-level elements: `create_crosshair`, `create_text_rect`, `create_smart_text`.
  - `library/thermal.py` — Sensor-space elements: `create_sensor_pixel_rect`, `create_sensor_crosshair`, `create_sensor_smart_text`.
- **Layer System**: `HUDEngine` now organises canvas items into named z-index layers (multiples of 100): `LAYER_BACKGROUND=0`, `LAYER_MAIN=100`, `LAYER_INTERACTION=200`, `LAYER_TOP=300`. `clear(layer=N)` removes only items on a specific layer without affecting others.
- **`TickEngine`**: Standalone high-frequency async pipeline class. Replaces any ad-hoc `after()` loop pattern with a clean `start()` / `stop()` / `mark_dirty()` / `on_tick(cb)` API.
- **HUD Developer Guide** (`docs/HUD_ENGINE.md`): Wiki-style documentation covering the package architecture, layer system, sync vs async pipelines, coordinate mapping, public API reference, and performance tips.
- **Cross-Platform Device Architecture**: Implemented a robust `ThermalDeviceManager` to automatically detect the host OS and load the appropriate backend.
- **OpenCV Backend Stub**: Added a generic OpenCV device backend to gracefully support future Windows and Linux system integration.
- **Device Refresh Controls**: Added a dedicated `↻` refresh button next to the device selection dropdown, allowing users to scan for recently plugged-in cameras without restarting the application.
- **Unified Pipeline Context**: Introduced a `HUD_DRAW` pipeline event equipped with a rich context dictionary, removing the need for plugins to guess drawing bounds or canvas scales.
- **Robustness**: Safe cleanup in `AppContext` when plugin loading fails; `SnapshotFrame` now unsubscribes from event buses on unload.

### Changed

- **`interactive_canvas` Plugin Refactor**: Replaced the hand-rolled `after()` hover loop with `TickEngine`. The plugin now accesses `hud.mapper.get_pixel_bounds()` / `hud.mapper.image_bbox` instead of private `hud._scale_x` / `hud._image_bbox` attributes. Selection drawing calls `hud.clear(layer=LAYER_INTERACTION)` so the hover border (raw canvas item) is never accidentally cleared.
- **`temp_overlay` Plugin Refactor**: Updated import path to `from src.utils.hud import HUDEngine` and added explicit `layer=LAYER_MAIN` to all draw calls.
- **`src/utils/hud_engine.py`**: Replaced the 580-line monolith with a clean re-export module that forwards `HUDEngine`, `CoordMapper`, `TickEngine`, and layer constants from the new package. Existing `from src.utils.hud_engine import HUDEngine` imports continue to work unchanged.
- **Thermal Pipeline Routing**: Refactored the internal rendering loops to explicitly decouple 16-bit sensor math (`RAW_PIPELINE`), 8-bit image styling (`IMAGE_PIPELINE`), and Tkinter vector mapping (`HUD_DRAW`).
- **Dynamic HUD Engine Scaling**: Integrated automated sensor-to-canvas ratio logic directly into the `HUDEngine`, allowing extensions like the temperature overlay to draw using constant "sensor" coordinates regardless of how far the application is zoomed.
- **Device Caching Security**: The hardware scanning logic now securely caches device object profiles during discovery. This fixes a critical bug where UI indexing could mismatch and attempt to load standard webcams instead of the TC001.
- **Modular Component Updates**: Console toggle button alignment was shifted vertically, and custom Tkinter components now utilize native `pointinghand` cursors.
- **Standardized Temperature Formatting**: Enforced `:.1f` precision across all HUD and overlay components.

### Fixed

- **Orphaned Event Listeners**: Hardened Tkinter component teardown flows across overlays (`GradientOverlay`, `HudOverlay`). Implemented strict `winfo_exists()` checks to prevent the EventBus from spamming `invalid command name` exceptions on destroyed widgets during UI hot-reloads.
- **Snapshot Stability**: Caught specific `OSError` in snapshot loading to prevent application crashes on invalid files.
- **HUD Performance**: Implemented LRU cache for primitive drawing and fixed redundant processing on canvas resize.

## [0.0.2-alpha] - Previous Updates

### Added

- **Data Ingestion Extensions**: Added robust functionality to load, clean, and map raw temperature arrays directly from CSV and Excel snapshot files.
- **Application Distribution**: Overhauled `build_mac.sh` to natively compile and package versioned `.app` datasets into accessible distribution files.
- **Plugin Architecture Config**: Adjusted PyInstaller `.spec` capabilities to properly encapsulate dynamic, late-loaded application plugins.
- **Developer Documentation**: Released robust architectural instructions (`PLUGIN.md` and `AGENTS.md`) outlining the EventBus data pipeline to encourage simple LLM-assisted plugin creation.

### Changed

- **Device Drop/Resume States**: Reworked the connection logic within `control_device.py` to allow live-dropping of hardware contexts (Disconnecting and Reconnecting).
- **Precise Sliders**: The `LabelSlider` component now accepts strict internal `resolution` settings for highly controlled incremental limits.
- **Hardware Filtering Engine**: Implemented ratio-based resolution algorithms to actively sift out and reject standard 16:9 / 4:3 webcams from loading into the thermal data processor.

### Fixed

- **Overlay Rendering Exceptions**: Fixed a bug where data overlay views would attempt to configure visibility pipelines before the base renderer canvas was successfully loaded into the application context.
