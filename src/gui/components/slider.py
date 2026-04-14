import tkinter as tk
from tkinter import ttk

class Slider(ttk.Scale):
    """Wrapped ttk.Scale (Slider) for uniform styling and future framework decoupling."""
    def __init__(self, parent, **kwargs):
        # Default orientation to horizontal if not specified
        if 'orient' not in kwargs:
            kwargs['orient'] = tk.HORIZONTAL
        super().__init__(parent, **kwargs)
