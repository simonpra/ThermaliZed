import tkinter as tk
from src.core.components.controls.base import BaseControlFrame
from src.gui.components import Label, Button, Combobox

class ControlDeviceFrame(BaseControlFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        
        row = 0
        self.add_section_header(row, "Device Status")
        
        self.status_var = tk.StringVar(value="Not Connected")
        self.status_label = Label(self, textvariable=self.status_var, foreground="gray")
        self.status_label.grid(row=row, column=1, sticky=tk.E, pady=0); row += 1
        
        Label(self, text="Input Device:").grid(
            row=row, column=0,
            columnspan=2, sticky=tk.W
        ); row += 1
        self.device_var = tk.StringVar()
        self.device_combo = Combobox(self, textvariable=self.device_var, state="readonly")
        self.device_combo.grid(row=row, column=0, sticky=tk.EW, pady=0)
        
        self.refresh_btn = Button(self, text="↻", width=3, command=self._on_refresh)
        self.refresh_btn.grid(row=row, column=1, sticky=tk.EW, pady=0); row += 1
        
        self.connect_btn = Button(self, text="Connect", command=self._on_connect)
        self.connect_btn.grid(row=row, column=0, columnspan=2, sticky=tk.EW, pady=(5, 10)); row += 1
        
        # Initial scan for devices
        self._on_refresh()
        
        # Add to parent
        self.parent.add_control_frame(self)
        
    def _on_refresh(self):
        try:
            camera = self.context.get_service('camera')
            if camera:
                devices = camera.get_device_names()
                self.context.state['devices'] = devices
                if devices:
                    # Provide string names to combobox (AVF devices use localizedName normally, but backend just returns the objects.
                    
                    # Backend Macos returns objects. Linux/Windows OpenCV returns strings.
                    # Normalize them to strings.
                    display_names = []
                    for d in devices:
                        if hasattr(d, 'localizedName'):
                            display_names.append(str(d.localizedName()))
                        else:
                            display_names.append(str(d))
                            
                    self.device_combo.config(values=display_names)
                    self.device_var.set(display_names[0])
                    self.connect_btn.config(state="normal")
                    self.context.event_bus.publish('LOG_MESSAGE', f"Found {len(display_names)} device(s)")
                else:
                    self.device_combo.config(values=["No devices found"])
                    self.device_var.set("No devices found")
                    self.connect_btn.config(state="disabled")
                    self.context.event_bus.publish('LOG_MESSAGE', f"No Device Found")
        except Exception as e:
            self.context.event_bus.publish('LOG_MESSAGE', f"Error refreshing devices: {e}")
            
    def _on_connect(self):
        idx = self.device_combo.current()
        if idx >= 0:
            try:
                camera = self.context.get_service('camera')
                if camera:
                    camera.start(idx)
                    self.status_var.set("Connected")
                    self.connect_btn.config(text="Disconnect", command=self._on_disconnect)
                    self.device_combo.config(state="disabled")
                    self.context.event_bus.publish('LOG_MESSAGE', f"Connected to camera index {idx}")
                else:
                    self.status_var.set("Camera Service Not Found")
            except Exception as e:
                self.status_var.set(f"Error: {e}")
                self.context.event_bus.publish('LOG_MESSAGE', f"Error connecting: {e}")

    def _on_disconnect(self):
        try:
            camera = self.context.get_service('camera')
            if camera:
                camera.stop()
                self.status_var.set("Not Connected")
                self.connect_btn.config(text="Connect", command=self._on_connect)
                self.device_combo.config(state="normal")
                self.context.event_bus.publish('LOG_MESSAGE', "Camera disconnected")
        except Exception as e:
            self.status_var.set(f"Error: {e}")
            self.context.event_bus.publish('LOG_MESSAGE', f"Error disconnecting: {e}")
