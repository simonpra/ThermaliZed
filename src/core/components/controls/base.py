import tkinter as tk
from tkinter import ttk
from src.gui.components import Label, LabelSlider

class BaseControlFrame(ttk.Frame):
    """
    Abstract base class for all control panel sections.
    
    Provides standardized styling and utilities for constructing UI elements.
    Automatically links to the shared Application Context and Parameters dictionary.
    """
    def __init__(self, parent, context=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.parent = parent
        self.context = context if context is not None else getattr(parent, 'context', None)
        if self.context:
            self.params = self.context.state['params']
        self.columnconfigure(0, weight=1)

    def add_section_header(self, row, text, top_pad=5):
        """Standardized visual header for grouped controls."""
        Label(
            self, text=text, font=('', 10, 'bold')
        ).grid(row=row, column=0, sticky=tk.W, pady=(top_pad, 5))

    def add_label_slider(self, row, label_text, variable, from_, to, resolution=1.0, command=None):
        """
        Creates and grids a standardized Label + LabelSlider stack.
        
        Args:
            row (int): The current grid row index to placement.
            label_text (str): Descriptive text above the slider.
            variable (tk.Variable): The Tkinter variable to bind.
            from_ (float): Minimum value.
            to (float): Maximum value.
            resolution (float): Step size for the spinbox.
            command (callable): Optional callback when the slider is moved.
                                Note: Scale passes the new value as a string to the command.
        """
        # Detail descriptor label
        Label(
            self, text=label_text, font=('', 10)
        ).grid(row=row, column=0, sticky=tk.W, pady=0, padx=0)
        
        # The scale + spinbox composite
        slider = LabelSlider(self, variable=variable, from_=from_, to=to, resolution=resolution, command=command)
        slider.grid(row=row+1, column=0, sticky=tk.EW, pady=0, padx=0)
        
        return slider

