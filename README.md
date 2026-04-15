# ThermaliZed

**ThermaliZed** is a Python-based extensible thermal camera viewer designed for seamless live rendering, dynamic GUI controls, and advanced raw thermal data manipulation. This application provides researchers, engineers, and hobbyists with a powerful, desktop-class interface to interact with affordable thermal imaging hardware.

![Python Version](https://img.shields.io/badge/python-3.11+-blue.svg)

## Requirements

- **macOS on Apple Silicon (M1+)**: Required for high-performance zero-copy memory buffers via CoreVideo and AVFoundation.
- **Python 3.11+ (Native ARM64 build)**: Do not use an x86 version under Rosetta 2, or video frame extraction performance will severely degrade. Ideally Python 3.14+ for `ttk` v9+ SVG support.
- **Tkinter 9+**: If older, SVG icons will fallback to displaying `[icon]`, but the application will still function perfectly.
- **Xcode Command Line Tools**: Only required if a pre-compiled wheel for PyObjC is not available for your specific Python/macOS environment. It allows `pip` to build the C-extensions from source. Install via terminal: `xcode-select --install`
- **Camera Permissions**: macOS will terminate the script unless your Terminal or IDE is granted Camera access in `System Settings > Privacy & Security > Camera`.

## Supported Brands

ThermaliZed is built to communicate with Topdon TC001, but it probably supports :

- **Topdon**: TC001 - TESTED
- **InfiRay**: P2 Pro
- **InfiRay**: T2 Series (T2L, T2S Plus, T2 Pro)
- _Other generic UVC thermal cameras utilizing the InfiRay Tiny1-C core or similar chipsets._

## Key Features

- **Robust Live Rendering**: Low-latency thermal video display leveraging modern UI frameworks.
- **Raw Data Pipeline**: Direct access to 16-bit raw thermal arrays, allowing non-destructive post-processing and accurate temperature measurements.
- **Extensible Plugin Engine**: An event-driven architecture that allows developers to easily inject custom image filters, UI components, and data exports.
- **Dynamic Visuals**: CV2 color palettes, temperature bound leveling, contrast and gamma.

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

## Developer Documentation

[PLUGIN.md](PLUGIN.md) will give you a good overview of the plugin and modular system.

[image_enhancement PLUGIN](plugins/image_enhancement/__init__.py) as a full exemple of a data-stream-manipulation plugin.

[SKILLS.md](SKILLS.md) can be used to ask AI agents to directly build your desired plugin.
