import tkinter as tk
from tkinter import ttk

class PanedWindow(ttk.PanedWindow):
    """Wrapped ttk.PanedWindow for uniform styling and future framework decoupling."""
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
