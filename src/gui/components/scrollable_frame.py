import tkinter as tk
from src.gui.components.frame import Frame
from src.gui.components.scrollbar import Scrollbar

class ScrollableFrame(Frame):
    """
    A unified Tkinter scrollable frame.
    Items should be packed into `self.scrollable_content`.
    """
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)

        self.canvas = tk.Canvas(self, borderwidth=0, highlightthickness=0)
        self.scrollbar = Scrollbar(self, orient=tk.VERTICAL, command=self.canvas.yview)
        
        # Inner content frame
        self.scrollable_content = Frame(self.canvas)
        
        self.scrollable_content.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        self.window_id = self.canvas.create_window((0, 0), window=self.scrollable_content, anchor="nw")
        
        self.canvas.bind("<Configure>", self._on_canvas_configure)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        # Pack scrollbar FIRST so it always claims its space before the canvas expands
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Bind mousewheel directly to all sub-widgets — no conditional bind_all needed
        for widget in (self, self.canvas, self.scrollable_content, self.scrollbar):
            widget.bind("<MouseWheel>", self._on_mousewheel)
            widget.bind("<Button-4>", self._on_mousewheel)
            widget.bind("<Button-5>", self._on_mousewheel)

    def _on_canvas_configure(self, event):
        # Update inner frame width to match canvas
        self.canvas.itemconfig(self.window_id, width=event.width)

    def _on_mousewheel(self, event):
        if not self.canvas.winfo_exists():
            return
            
        if event.num == 4:
            self.canvas.yview_scroll(-1, "units")
        elif event.num == 5:
            self.canvas.yview_scroll(1, "units")
        else:
            delta = event.delta
            if delta != 0:
                self.canvas.yview_scroll(int(-1*(delta/120)), "units")
