# ThermaliZed

<img width="1592" height="1076" alt="thermalized_screenshot_02" src="https://github.com/user-attachments/assets/898cef14-96ed-4a68-9b30-3717b8f0c031" />

**ThermaliZed**

> An extensible platform for real-time visualization and processing of raw thermal data.

ThermaliZed is a developer-first tool designed for researchers, engineers, and R&D teams working with thermal imaging systems. It enables interactive exploration, manipulation, and extension of 16-bit thermal data pipelines from both live cameras and recorded datasets.

![Python Version](https://img.shields.io/badge/python-3.11+-blue.svg)

## What is it for?

- Visualize live thermal camera streams with low latency
- Load and explore raw thermal datasets (CSV / Excel)
- Manipulate 16-bit thermal data without compression loss
- Adjust temperature bounds, contrast, and color palettes interactively
- Interactively hover and pin individual sensor pixels to read their temperature
- Easily build and integrate custom data processing plugins
- Prototype thermal analysis pipelines in real time

## Plugin System

ThermaliZed includes an event-driven plugin architecture that allows you to:

- inject custom image processing logic into the 16-bit pipeline
- draw HUD overlays (crosshairs, labels, borders) via the `HUDEngine`
- build interactive tools on top of the thermal canvas (hover, click, select)
- extend the UI with new sidebar controls or visualizations
- create reusable thermal data pipelines

👉 See [PLUGIN.md](PLUGIN.md) for the complete guide

👉 Example reference plugins in [`plugins/`](plugins/):

- [`image_enhancement`](plugins/image_enhancement/__init__.py) — 16-bit contrast / gamma / blur pipeline plugin with sidebar UI
- [`temp_overlay`](plugins/temp_overlay/__init__.py) — HUD overlay marking MIN / MAX temperature spots
- [`interactive_canvas`](plugins/interactive_canvas/__init__.py) — pixel hover & selection on the live canvas

Using a single `__init__.py` file per plugin!

## Architecture Overview

```
main.py
└── AppContext                  # Central state & plugin loader
    ├── EventBus                # Pub/sub + sequential pipeline
    ├── ThermalDeviceManager    # Cross-platform device backend
    └── Plugins (auto-discovered)
         ├── src/core/components/   # Built-in: renderer, controls, overlays
         └── plugins/               # External: image_enhancement, temp_overlay, interactive_canvas

Processing Pipeline (per frame):
  FRAME_READY → processor.py
      ├── RAW_FRAME_PIPELINE   (16-bit uint16 — modifiable)
      ├── IMAGE_PIPELINE       (8-bit BGR heatmap — modifiable)
      └── HUD_DRAW             (canvas + bbox + raw_payload — overlay hook)

HUD Engine (src/utils/hud/):
  HUDEngine    — layer registry, memoisation, draw API
  CoordMapper  — sensor ↔ canvas coordinate math
  TickEngine   — async canvas.after() loop for hover / animations
  library/     — stateless drawing primitives and composites
```

## Included Plugins

| Plugin               | Hook                      | Purpose                                           |
| -------------------- | ------------------------- | ------------------------------------------------- |
| `image_enhancement`  | `RAW_FRAME_PIPELINE`      | Contrast (alpha), Gamma (texture), Blur           |
| `temp_overlay`       | `HUD_DRAW`                | Crosshair + label at MIN / MAX sensor pixels      |
| `interactive_canvas` | `HUD_DRAW` + `TickEngine` | Hover border and pinned pixel temperature readout |

## Supported Inputs

<img width="600" height="312" alt="TCView" src="https://github.com/user-attachments/assets/989635c2-8228-42dc-a134-7bd352c7a5b4" />

ThermaliZed is built to communicate with Topdon TC001, but it probably supports:

- **Topdon**: TC001 - TESTED
- **InfiRay**: P2 Pro
- **InfiRay**: T2 Series (T2L, T2S Plus, T2 Pro)
- _Other generic UVC thermal cameras utilizing the InfiRay Tiny1-C core or similar chipsets._

And can as well load:

- **Excel or CSV files**: thermal data from Excel or CSV files (no Header) into a 16-bit array picture.

## Development Resources

Installation process and all development resources live in [dev/README.md](dev/README.md)

HUD Engine internals and plugin drawing API: [docs/HUD_ENGINE.md](docs/HUD_ENGINE.md)

## Standalone Bundle

![thermaliZed logo](thermalized.png)

You can download the latest pre-compiled application bundle directly from the `dist` folder.

The app is packaged into a standalone executable using PyInstaller and the provided `ThermaliZed.spec` configuration file.

> **Note:** This software is provided _"as is"_ without any guarantees of compatibility for your specific hardware or operating system configuration. It has been primarily developed and tested on a MacBook Air (M3) running macOS 15.7.

## Examples

Temperature steps with live view

https://github.com/user-attachments/assets/e9fc57ef-a1ed-415e-96f2-c2db8a09bafc

Manual temperature leveling with Excel file loaded

https://github.com/user-attachments/assets/f61b616a-568d-4183-b353-2b1a8ca1b7d6

Temperature/Gradient steps on loaded file

https://github.com/user-attachments/assets/304a9ccd-7da5-4aaa-b65e-ed2e02f7c480

Texture & Contrast on loaded file

https://github.com/user-attachments/assets/dde45412-b15c-42bd-ad21-ff663183d3a0
