import tkinter as tk
from tkinter import ttk

class Combobox(ttk.Combobox):
    """Wrapped ttk.Combobox for uniform styling and future framework decoupling."""
    def __init__(self, parent, **kwargs):
        # Default state
        if 'state' not in kwargs:
            kwargs['state'] = "readonly"
        super().__init__(parent, **kwargs)
