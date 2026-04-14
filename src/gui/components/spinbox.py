import tkinter as tk
from tkinter import ttk

class Spinbox(ttk.Spinbox):
    """Wrapped ttk.Spinbox for uniform styling and future framework decoupling."""
    def __init__(self, parent, **kwargs):
        # Default width
        if 'width' not in kwargs:
            kwargs['width'] = 6
        super().__init__(parent, **kwargs)
