import tkinter as tk
from src.core.components.controls.base import BaseControlFrame
from src.utils.constants import COLORMAPS
from src.gui.components import Combobox

class ControlColormapsFrame(BaseControlFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        
        row = 0
        self.add_section_header(row, "Colormap Visualization")
        row += 1
        
        colormap_names = [name for _, name in COLORMAPS]
        self.cmap_var = tk.StringVar(value=colormap_names[self.params['colormap_index']])
        self.cmap_combo = Combobox(self, textvariable=self.cmap_var, values=colormap_names)
        self.cmap_combo.bind("<<ComboboxSelected>>", self._on_cmap_changed)
        self.cmap_combo.grid(row=row, column=0, sticky=tk.EW, pady=(0, 15)); row += 1

        # Add to parent
        self.parent.add_control_frame(self)
        
    def _on_cmap_changed(self, event):
        idx = self.cmap_combo.current()
        if idx >= 0:
            self.params['colormap_index'] = idx
            self.context.event_bus.publish('COLORMAP_CHANGED', COLORMAPS[idx][0])