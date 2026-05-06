# Development resources

## Requirements

- **macOS on Apple Silicon (M1+)**: Required for high-performance zero-copy memory buffers via CoreVideo and AVFoundation.
- **Python 3.11+ (Native ARM64 build)**: Do not use an x86 version under Rosetta 2, or video frame extraction performance will severely degrade. Ideally Python 3.14+ for `ttk` v9+ SVG support. You can use [PyEnv](https://github.com/pyenv/pyenv#installation) to install any Python version.
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

   **On macOS:**
<<<<<<< starting-docs

=======
>>>>>>> main
   ```bash
   pip install -r requirements-mac.txt
   ```

   **On Windows:**
<<<<<<< starting-docs

=======
>>>>>>> main
   ```bash
   pip install -r requirements-win.txt
   ```

   **Core only (headless/other):**
<<<<<<< starting-docs

=======
>>>>>>> main
   ```bash
   pip install -r requirements.txt
   ```

3. Connect your thermal camera via USB. (optional, you can also load [raw file](thermal_pictures/tc001_snapshot.npz) )
4. Run the application:
   ```bash
   python main.py
   ```

## Troubleshoot

### ModuleNotFoundError: No module named '\_tkinter'

It means your version of Python is not configured to use Tkinter.

Install tkinter with `brew install python-tk`

Note : if you use PyEnv, you need to first uninstall your local Python version, install Tkinter and install the version of Python again via PyEnv.

## Developer Documentation

[docs/PLUGIN.md](../docs/PLUGIN.md) will give you a good overview of the plugin and modular system.

[image_enhancement PLUGIN](../plugins/image_enhancement/__init__.py) as a full exemple of a data-stream-manipulation plugin.

[SKILLS.md](SKILLS.md) can be used to ask AI agents to directly build your desired plugin.
