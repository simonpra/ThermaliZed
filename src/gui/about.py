import tkinter as tk
from tkinter import ttk
import sys
import numpy as np
import cv2
import PIL

def show_about_dialog(parent, app_version):
    """Shows the About dialog."""
    about_win = tk.Toplevel(parent)
    about_win.title("About ThermaliZed")
    about_win.geometry("350x400")
    about_win.resizable(False, False)
    
    # Make it modal
    about_win.transient(parent)
    about_win.grab_set()
    
    # Content
    # Title
    lbl_title = ttk.Label(about_win, text="ThermaliZed", font=("Helvetica", 16, "bold"))
    lbl_title.pack(pady=(20, 5))
    
    # Version
    lbl_version = ttk.Label(about_win, text=f"Version {app_version}")
    lbl_version.pack(pady=0)
    
    # Author
    lbl_author = ttk.Label(about_win, text="Created by Simon Pra")
    lbl_author.pack(pady=(10, 0))
    
    # License
    lbl_license = ttk.Label(about_win, text="MIT License")
    lbl_license.pack(pady=0)
    
    # Separator
    ttk.Separator(about_win, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=20, pady=15)
    
    # Dependencies
    lbl_deps = ttk.Label(about_win, text="System & Dependencies", font=("Helvetica", 12, "bold"))
    lbl_deps.pack(pady=(0, 10))
    
    py_version = sys.version.split(' ')[0]
    
    deps_frame = ttk.Frame(about_win)
    deps_frame.pack(fill=tk.X, padx=40)
    
    deps = [
        ("Python:", py_version),
        ("OpenCV:", cv2.__version__),
        ("NumPy:", np.__version__),
        ("Pillow:", PIL.__version__)
    ]
    
    for row, (name, ver) in enumerate(deps):
        ttk.Label(deps_frame, text=name, font=("Helvetica", 10, "bold")).grid(row=row, column=0, sticky="w", pady=2)
        ttk.Label(deps_frame, text=ver).grid(row=row, column=1, sticky="e", padx=(20, 0), pady=2)
        
    deps_frame.columnconfigure(1, weight=1)
    
    # Close button
    btn_close = ttk.Button(about_win, text="Close", command=about_win.destroy)
    btn_close.pack(side=tk.BOTTOM, pady=20)
    
    # Center the window
    about_win.update_idletasks()
    x = parent.winfo_x() + (parent.winfo_width() - about_win.winfo_reqwidth()) // 2
    y = parent.winfo_y() + (parent.winfo_height() - about_win.winfo_reqheight()) // 2
    about_win.geometry(f"+{x}+{y}")
