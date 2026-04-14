import tkinter as tk
from tkinter import ttk

class Label(ttk.Label):
    """Wrapped ttk.Label for uniform styling and future framework decoupling."""
    def __init__(self, parent, **kwargs):
        # Allow passing font as a simple tuple/string or use default
        if 'font' not in kwargs:
            kwargs['font'] = ('', 10)
        super().__init__(parent, **kwargs)
