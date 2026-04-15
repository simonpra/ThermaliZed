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
    def __init__(self, parent, variable, from_, to, resolution=1.0, command=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.variable = variable
        self.command = command
        
        # Configure layout
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=0)
        
        self.resolution = resolution
        
        # Build components using centralized wrappers
        self.scale = Slider(
            self,
            variable=self.variable,
            from_=from_,
            to=to,
            command=self._round_value
        )
        
        self.spinbox = Spinbox(
            self,
            textvariable=self.variable,
            from_=from_,
            to=to,
            increment=resolution,
            width=6,
            command=self._on_spinbox_btn
        )
        
        # Layout
        self.scale.grid(row=0, column=0, sticky=tk.EW, padx=(0, 10))
        self.spinbox.grid(row=0, column=1, sticky=tk.E)

        # Force sync on focus loss/return to ensure typed values are committed
        self.spinbox.bind("<Return>", self._on_return)
        self.spinbox.bind("<KP_Enter>", self._on_return)
        self.spinbox.bind("<FocusOut>", lambda e: self._sync_var())

    def _round_value(self, value):
        try:
            val = float(value)
            val = self._apply_resolution_rounding(val)
            self.variable.set(val)
            if self.command:
                self.command(val)
        except ValueError:
            pass

    def _on_spinbox_btn(self, *args):
        # Triggers when spinbox up/down arrows are pressed
        self._sync_var()

    def _on_return(self, event=None):
        self._sync_var()
        # Drop focus from spinbox
        self.focus_set()

    def _apply_resolution_rounding(self, val):
        if self.resolution > 0:
            # Snap to the nearest multiple of resolution
            val = round(val / self.resolution) * self.resolution
            # Optional: round to handle float imprecision based on resolution decimal places
            decimals = max(0, len(str(self.resolution).rstrip('0').split('.')[-1]) if '.' in str(self.resolution) else 0)
            val = round(val, decimals)
        return val

    def _sync_var(self):
        try:
            # Force the internal variable to update from the spinbox string
            val = float(self.spinbox.get())
            val = self._apply_resolution_rounding(val)
            self.variable.set(val)
            if self.command:
                self.command(val)
        except ValueError:
            pass
