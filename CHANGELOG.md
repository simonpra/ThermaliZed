# Changelog

All notable changes to the Thermal Viewer application will be documented in this file.

## [0.0.3-alpha] - Unreleased

### Added
- **Cross-Platform Device Architecture**: Implemented a robust `ThermalDeviceManager` to automatically detect the host OS and load the appropriate backend.
- **OpenCV Backend Stub**: Added a generic OpenCV device backend to gracefully support future Windows and Linux system integration.
- **Device Refresh Controls**: Added a dedicated `↻` refresh button next to the device selection dropdown, allowing users to scan for recently plugged-in cameras without restarting the application.
- **Unified Pipeline Context**: Introduced a `HUD_DRAW` pipeline event equipped with a rich context dictionary, removing the need for plugins to guess drawing bounds or canvas scales.

### Changed
- **Thermal Pipeline Routing**: Refactored the internal rendering loops to explicitly decouple 16-bit sensor math (`RAW_PIPELINE`), 8-bit image styling (`IMAGE_PIPELINE`), and Tkinter vector mapping (`HUD_DRAW`).
- **Dynamic HUD Engine Scaling**: Integrated automated sensor-to-canvas ratio logic directly into the `HUDEngine`, allowing extensions like the temperature overlay to draw using constant "sensor" coordinates regardless of how far the application is zoomed.
- **Device Caching Security**: The hardware scanning logic now securely caches device object profiles during discovery. This fixes a critical bug where UI indexing could mismatch and attempt to load standard webcams instead of the TC001.
- **Modular Component Updates**: Console toggle button alignment was shifted vertically, and custom Tkinter components now utilize native `pointinghand` cursors.

### Fixed
- **Orphaned Event Listeners**: Hardened Tkinter component teardown flows across overlays (`GradientOverlay`, `HudOverlay`). Implemented strict `winfo_exists()` checks to prevent the EventBus from spamming `invalid command name` exceptions on destroyed widgets during UI hot-reloads.

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
