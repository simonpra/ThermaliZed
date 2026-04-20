import abc

class BaseDeviceBackend(abc.ABC):
    """
    Abstract base class for all platform-specific thermal camera backends.
    All backends must implement these methods to be compatible with ThermalDeviceManager.
    """

    @abc.abstractmethod
    def get_device_names(self) -> list:
        """
        Request a list of available video devices.
        
        Returns:
            list: A list of device identifiers or names.
        """
        pass

    @abc.abstractmethod
    def start(self, device_index: int):
        """
        Start the capture pipeline.
        
        Args:
            device_index (int): The index of the selected device.
        """
        pass

    @abc.abstractmethod
    def stop():
        """
        Gracefully stop the capture session.
        """
        pass

    @abc.abstractmethod
    def get_latest_frame(self) -> dict | None:
        """
        Safely retrieve the most recent frame data.
        
        Returns:
            dict | None: Dictionary containing 'frame', 'width', 'height', 'stride', and 'timestamp'.
        """
        pass
