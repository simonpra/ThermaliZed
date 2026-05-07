import tkinter as tk
from tkinter import ttk

class LabelFrame(ttk.LabelFrame):
    """Wrapped ttk.LabelFrame for uniform styling and future framework decoupling."""
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
