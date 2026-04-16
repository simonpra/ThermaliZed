# ThermaliZed

<img width="2067" height="1436" alt="thermalized_screenshot_01" src="https://github.com/user-attachments/assets/251b7fd3-8a62-4232-8835-9cd5ac746439" />


**ThermaliZed**

> An extensible platform for real-time visualization and processing of raw thermal data.

ThermaliZed is a developer-first tool designed for researchers, engineers, and R&D teams working with thermal imaging systems. It enables interactive exploration, manipulation, and extension of 16-bit thermal data pipelines from both live cameras and recorded datasets.

![Python Version](https://img.shields.io/badge/python-3.11+-blue.svg)

## What is it for ?
- Visualize live thermal camera streams with low latency
- Load and explore raw thermal datasets (CSV / Excel)
- Manipulate 16-bit thermal data without compression loss
- Adjust temperature bounds, contrast, and color palettes interactively
- Easly build and integrate custom data processing plugins
- Prototype thermal analysis pipelines in real time

## Plugin System

ThermaliZed includes an event-driven plugin architecture that allows you to:
- inject custom image processing logic
- build analysis tools on top of thermal streams
- extend the UI with new controls or visualizations
- create reusable thermal data pipelines

👉 See [PLUGIN.md](PLUGIN.md) for details

👉 Example: [image_enhancement plugin](plugins/image_enhancement/__init__.py)

Using a single `__init__.py` file !

## Supported Inputs
<img width="600" height="312" alt="TCView" src="https://github.com/user-attachments/assets/989635c2-8228-42dc-a134-7bd352c7a5b4" />

ThermaliZed is built to communicate with Topdon TC001, but it probably supports :

- **Topdon**: TC001 - TESTED
- **InfiRay**: P2 Pro
- **InfiRay**: T2 Series (T2L, T2S Plus, T2 Pro)
- _Other generic UVC thermal cameras utilizing the InfiRay Tiny1-C core or similar chipsets._

And can as well load :
- **Excel or CSV files**: thermal data from Excel or CSV files (no Header) into a 16bits array picture.

## Requirements

- **macOS on Apple Silicon (M1+)**: Required for high-performance zero-copy memory buffers via CoreVideo and AVFoundation.
- **Python 3.11+ (Native ARM64 build)**: Do not use an x86 version under Rosetta 2, or video frame extraction performance will severely degrade. Ideally Python 3.14+ for `ttk` v9+ SVG support.
- **Tkinter 9+**: If older, SVG icons will fallback to displaying `[icon]`, but the application will still function perfectly.
- **Xcode Command Line Tools**: Only required if a pre-compiled wheel for PyObjC is not available for your specific Python/macOS environment. It allows `pip` to build the C-extensions from source. Install via terminal: `xcode-select --install`
- **Camera Permissions**: macOS will terminate the script unless your Terminal or IDE is granted Camera access in `System Settings > Privacy & Security > Camera`.

## Quick Start

Ensure you have Python 3.11+ installed. The `ttk` version 9+ is required for the application's SVG compatibility, but not mandatory.

1. Clone this repository.

   1.1 ideally use a virtual environment

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install --upgrade pip
   ```

2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Connect your thermal camera via USB. (optional, you can also load [raw file](thermal_pictures/tc001_snapshot.npz) )
4. Run the application:
   ```bash
   python main.py
   ```

## Standalone Bundle

![thermaliZd logo](thermalized.png)

You can download the latest pre-compiled application bundle directly from the `dist` folder.

The app is packaged into a standalone executable using PyInstaller and the provided `ThermaliZed.spec` configuration file.

> **Note:** This software is provided _"as is"_ without any guarantees of compatibility for your specific hardware or operating system configuration. It has been primarily developed and tested on a MacBook Air (M3) running macOS 15.7.

## Exemples

Temperature steps with live view

https://github.com/user-attachments/assets/e9fc57ef-a1ed-415e-96f2-c2db8a09bafc

Manual temperature leveling with Excel file loaded

https://github.com/user-attachments/assets/f61b616a-568d-4183-b353-2b1a8ca1b7d6

Temperature/Gradient steps on loaded file

https://github.com/user-attachments/assets/304a9ccd-7da5-4aaa-b65e-ed2e02f7c480

Texture & Contrast on loaded file

https://github.com/user-attachments/assets/dde45412-b15c-42bd-ad21-ff663183d3a0

## Developer Documentation

[PLUGIN.md](PLUGIN.md) will give you a good overview of the plugin and modular system.

[image_enhancement PLUGIN](plugins/image_enhancement/__init__.py) as a full exemple of a data-stream-manipulation plugin.

[SKILLS.md](SKILLS.md) can be used to ask AI agents to directly build your desired plugin.
