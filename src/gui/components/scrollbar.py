import tkinter as tk
from tkinter import ttk

class Scrollbar(ttk.Scrollbar):
    """Wrapped ttk.Scrollbar for uniform styling and future framework decoupling."""
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
