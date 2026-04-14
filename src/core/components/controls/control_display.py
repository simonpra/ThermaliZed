import tkinter as tk
from src.core.components.controls.base import BaseControlFrame
from src.gui.components import Checkbox

class ControlDisplayFrame(BaseControlFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        
        row = 0
        self.add_section_header(row, "Image Filtering")
        row += 1
        
        self.edge_var = tk.BooleanVar(value=self.params['edge_detection'])
        Checkbox(self, text="Edge Detection", variable=self.edge_var, command=self._on_edge_toggled).grid(row=row, column=0, sticky=tk.W); row += 1
        
        self.thresh_var = tk.DoubleVar(value=self.params['edge_threshold'])
        self.add_label_slider(row, "Edge Threshold:", self.thresh_var, 50, 200, 1.0, self._on_thresh_changed)
        row += 2
        
        # Add to parent
        self.parent.add_control_frame(self)
        
    def _on_edge_toggled(self):
        self.params['edge_detection'] = self.edge_var.get()
        
    def _on_thresh_changed(self, event=None):
        self.params['edge_threshold'] = int(float(self.thresh_var.get()))
