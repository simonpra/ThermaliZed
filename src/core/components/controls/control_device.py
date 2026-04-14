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
        devices = self.context.state.get('devices', [])
        
        if devices:
            self.device_var.set(devices[0])
            self.device_combo = Combobox(self, textvariable=self.device_var, values=devices)
            self.device_combo.grid(row=row, column=0, sticky=tk.EW, pady=0)
            
            self.connect_btn = Button(self, text="Connect", command=self._on_connect)
            self.connect_btn.grid(row=row, column=1, sticky=tk.EW, pady=0); row += 1
        else:
            Label(self, text="No devices found", foreground="red").grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=(0, 15)); row += 1
            
        # Add to parent
        self.parent.add_control_frame(self)
            
    def _on_connect(self):
        idx = self.device_combo.current()
        if idx >= 0:
            try:
                camera = self.context.get_service('camera')
                if camera:
                    camera.start(idx)
                    self.status_var.set("Connected")
                    self.connect_btn.config(state="disabled")
                    self.device_combo.config(state="disabled")
                    self.context.event_bus.publish('LOG_MESSAGE', f"Connected to camera index {idx}")
                else:
                    self.status_var.set("Camera Service Not Found")
            except Exception as e:
                self.status_var.set(f"Error: {e}")
                self.context.event_bus.publish('LOG_MESSAGE', f"Error connecting: {e}")
