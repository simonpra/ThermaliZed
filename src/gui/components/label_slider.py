import tkinter as tk
from src.gui.components.label import Label
from src.gui.components.slider import Slider
from src.gui.components.spinbox import Spinbox

class LabelSlider(tk.Frame):
    """
    A composite widget providing a standardized parameter slider.
    
    Combines a horizontal Scale and a Spinbox that stay synchronized.
    Provides a consistent visual API for all threshold and tuning controls.
    """
    def __init__(self, parent, variable, from_, to, resolution=1.0, **kwargs):
        super().__init__(parent, **kwargs)
        self.variable = variable
        
        # Configure layout
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=0)
        
        # Build components using centralized wrappers
        self.scale = Slider(
            self,
            variable=self.variable,
            from_=from_,
            to=to
        )
        
        self.spinbox = Spinbox(
            self,
            textvariable=self.variable,
            from_=from_,
            to=to,
            increment=resolution,
            width=6
        )
        
        # Layout
        self.scale.grid(row=0, column=0, sticky=tk.EW, padx=(0, 10))
        self.spinbox.grid(row=0, column=1, sticky=tk.E)

        # Force sync on focus loss/return to ensure typed values are committed
        self.spinbox.bind("<Return>", lambda e: self._sync_var())
        self.spinbox.bind("<FocusOut>", lambda e: self._sync_var())

    def _sync_var(self):
        try:
            # Force the internal variable to update from the spinbox string
            val = float(self.spinbox.get())
            self.variable.set(val)
        except ValueError:
            pass
