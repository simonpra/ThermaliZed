import tkinter as tk
from tkinter import simpledialog
from src.core.components.controls.base import BaseControlFrame
from src.utils.functions import to_degrees_c, to_raw
from src.gui.components import Checkbox

class ControlLevelingFrame(BaseControlFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        
        row = 0
        self.add_section_header(row, "Leveling")
        row += 1
        
        self.manual_var = tk.BooleanVar(value=self.params['manual_leveling'])
        Checkbox(self, text="Manual Leveling", variable=self.manual_var, command=self._on_manual_toggled).grid(row=row, column=0, sticky=tk.W, pady=(0, 5)); row += 1
        
        self.min_c = tk.DoubleVar(value=to_degrees_c(self.params['manual_min_raw']))
        self.add_label_slider(row, "Min °C:", self.min_c, -20.0, 100.0, 0.5, self._on_min_changed)
        row += 2
        
        self.max_c = tk.DoubleVar(value=to_degrees_c(self.params['manual_max_raw']))
        self.add_label_slider(row, "Max °C:", self.max_c, -20.0, 100.0, 0.5, self._on_max_changed)
        row += 2
        
        # Add to parent
        self.parent.add_control_frame(self)
        
    def _on_manual_toggled(self):
        self.params['manual_leveling'] = self.manual_var.get()
        
    def _on_min_changed(self, event=None):
        deg = self.min_c.get()
        self.params['manual_min_raw'] = to_raw(deg)
        
    def _on_max_changed(self, event=None):
        deg = self.max_c.get()
        self.params['manual_max_raw'] = to_raw(deg)
