import sys

class ThermalDeviceManager:
    """
    Cross-platform coordinator for thermal camera devices.
    Determines the current operating system and loads the appropriate device backend.
    
    This acts as the main bridge between the application's internal state and the
    hardware capture pipelines.
    """
    def __init__(self):
        self._backend = self._init_backend()

    def _init_backend(self):
        platform = sys.platform
        
        if platform == 'darwin':
            print("[DeviceManager] Loading macOS AVFoundation Backend")
            from src.core.device.platforms.macos import MacOSDeviceBackend
            return MacOSDeviceBackend()
        else:
            print(f"[DeviceManager] Loading generic OpenCV Backend for platform '{platform}'")
            from src.core.device.platforms.opencv_backend import OpenCVDeviceBackend
            return OpenCVDeviceBackend()

    def get_device_names(self):
        """Request a list of available video devices from the active backend."""
        return self._backend.get_device_names()

    def start(self, device_index: int):
        """Start the active backend's capture pipeline."""
        return self._backend.start(device_index)

    def stop(self):
        """Stop the active backend's capture session."""
        return self._backend.stop()

    def get_latest_frame(self) -> dict | None:
        """Safely retrieve the most recent frame data from the active backend."""
        return self._backend.get_latest_frame()
