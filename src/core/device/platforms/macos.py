import threading
import time
import objc
import dispatch
import AVFoundation as AVF
import CoreMedia as CM
from Quartz import CoreVideo as CV

from src.core.device.platforms.macos_delegate import FrameDelegate
from src.core.device.base import BaseDeviceBackend

class MacOSDeviceBackend(BaseDeviceBackend):
    """
    Manages the AVFoundation capture session and retrieves frames from the thermal camera hardware on macOS.
    """
    
    def __init__(self):
        self.frame_lock = threading.Lock()
        self.shared_frame_data = {
            'latest_frame': None,
            'width': 0,
            'height': 0,
            'stride': 0,
            'is_planar': False,
            'timestamp': 0.0
        }
        self.capture_thread = None
        self.session_active = False
        self.devices = []

    def get_device_names(self) -> list[AVF.AVCaptureDevice]:
        """
        Request a list of available video devices from AVFoundation.
        """
        try:
            self.devices = []
            devices = AVF.AVCaptureDevice.devicesWithMediaType_(AVF.AVMediaTypeVideo)
            for d in devices :
                if not MacOSDeviceBackend.filter_devices(d):
                    continue
                self.devices.append(d)
                dId = d.uniqueID()
                dModelId = d.modelID()
                dName = d.localizedName()
                dManufacturer = d.manufacturer()
                dFormat = d.formats()
                print(f"Device ID: {dId}, Model ID: {dModelId}, Name: {dName}, Manufacturer: {dManufacturer}, Format: {dFormat}")
                
            return self.devices
        except Exception as e:
            print(f"Error getting device names: {e}")
            return []
    
    @staticmethod
    def filter_devices(device: AVF.AVCaptureDevice):
        """
        Filter out devices that are simple webcam.
        Using the resolution ratio to filter out devices.
        TC001 resolution ratio is 1.5 (384/256), wich is 2 384x128 standard 16/9 supperposed,
        to be "merged" togheter to create the final 16bits image.
        Webcam resolution ratio is 16/9 (1.777...) or 4/3 (1.333...).
        """
        for fmt in device.formats():
            desc = fmt.formatDescription()
            dims = CM.CMVideoFormatDescriptionGetDimensions(desc)
            if dims.height / dims.width == 1.5:
                return True  # TC001 signature found
        return False

    def start(self, device_index):
        if not self.session_active:
            self.session_active = True
            self.capture_thread = threading.Thread(
                target=self._capture_loop,
                args=(device_index,),
                daemon=True
            )
            self.capture_thread.start()

    def stop(self):
        self.session_active = False
        if self.capture_thread:
            self.capture_thread.join(timeout=2.0)

    def _capture_loop(self, device_index):
        session = None
        try:
            # Initialize delegate
            delegate = FrameDelegate.alloc().initWithLock_Data_(self.frame_lock, self.shared_frame_data)
            
            # Get device from cached list
            if device_index >= len(self.devices):
                print("Device index out of range")
                return
                
            device = self.devices[device_index]
            
            # Find TC001 format
            target_format = None
            for fmt in device.formats():
                desc = fmt.formatDescription()
                dims = CM.CMVideoFormatDescriptionGetDimensions(desc)
                if dims.width == 256 and dims.height == 384:
                    target_format = fmt
                    break
                    
            if not target_format:
                print("TC001 format not found on device")
                return
                
            # Configure device
            session = AVF.AVCaptureSession.alloc().init()
            session.beginConfiguration()
            
            locked, _ = device.lockForConfiguration_(None)
            if locked:
                device.setActiveFormat_(target_format)
                device.setActiveVideoMinFrameDuration_(CM.CMTimeMake(1, 25))
                device.setActiveVideoMaxFrameDuration_(CM.CMTimeMake(1, 25))
                device.unlockForConfiguration()
                
            # Add input
            device_input, _ = AVF.AVCaptureDeviceInput.deviceInputWithDevice_error_(device, None)
            if device_input and session.canAddInput_(device_input):
                session.addInput_(device_input)
                
            # Add output
            video_output = AVF.AVCaptureVideoDataOutput.alloc().init()
            video_output.setVideoSettings_({CV.kCVPixelBufferPixelFormatTypeKey: 2037741171}) # kCVPixelFormatType_422YpCbCr8
            video_output.setAlwaysDiscardsLateVideoFrames_(True)
            
            # Be explicit about creating a serial queue
            queue = dispatch.dispatch_queue_create(b"thermal_queue", dispatch.DISPATCH_QUEUE_SERIAL)
            video_output.setSampleBufferDelegate_queue_(delegate, queue)
            
            if session.canAddOutput_(video_output):
                session.addOutput_(video_output)
                
            session.commitConfiguration()
            session.startRunning()
            
            # Keep thread alive
            while self.session_active:
                time.sleep(0.1)
                
        except Exception as e:
            print(f"Capture error: {e}")
        finally:
            if session and session.isRunning():
                session.stopRunning()

    def get_latest_frame(self):
        with self.frame_lock:
            timestamp = self.shared_frame_data['timestamp']
            
            if self.shared_frame_data['latest_frame'] is None:
                return None
                
            frame = self.shared_frame_data['latest_frame']
            width = self.shared_frame_data['width']
            height = self.shared_frame_data['height']
            stride = self.shared_frame_data['stride']
            
            return {
                'frame': frame,
                'width': width,
                'height': height,
                'stride': stride,
                'timestamp': timestamp
            }
