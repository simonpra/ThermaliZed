import tkinter as tk
from tkinter import ttk
from src.core.plugin_base import SystemComponent

### CONTROLS ######################
from src.core.components.controls.control_device import ControlDeviceFrame
from src.core.components.controls.control_colormaps import ControlColormapsFrame
from src.core.components.controls.control_leveling import ControlLevelingFrame
from src.core.components.controls.control_display import ControlDisplayFrame

class ControlPanelFrame(ttk.Frame):
    def __init__(self, parent, context, **kwargs):
        super().__init__(parent, **kwargs)
        self.context = context

        ### INIT sub-components
        ### They will add themselves to the control panel
        ControlDeviceFrame(self)
        ControlColormapsFrame(self)
        ControlLevelingFrame(self)
        # ControlDisplayFrame(self)

    def add_control_frame(self, frame_instance, **pack_options):
        """Add a control frame to the control panel."""
        # Default options
        options = {'fill': tk.X, 'pady': 0, 'padx': 0}
        options.update(pack_options)
        frame_instance.pack(**options)

class PluginClass(SystemComponent):
    """Core control panel plugin."""
    def on_load(self, context):
        self.context = context

    def get_ui(self, parent_widget, zone):
        if zone == 'left_sidebar':
            # Wrapping with padding frame just like we did in gui/app.py before
            wrapper = ttk.Frame(parent_widget, padding=0)
            self.panel = ControlPanelFrame(wrapper, self.context)
            self.panel.pack(fill=tk.BOTH, expand=True)
            return wrapper
        return None
