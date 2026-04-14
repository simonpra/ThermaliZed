import tkinter as tk
import tkinter.ttk as ttk
from src.core.plugin_base import SystemComponent
from src.gui.components import Frame, Button, Label, Scrollbar, ButtonIcon

class ConsoleFrame(tk.Frame):
    """
    Debugging console component. Listens to 'LOG_MESSAGE' events and provides a 
    collapsible text interface at the bottom of the screen to track system status.
    """
    def __init__(self, parent, context, **kwargs):
        # Use tk.Frame kwargs for styling instead of ttk styles
        kwargs.setdefault('bg', '#111111')
        kwargs.setdefault('padx', 10)
        kwargs.setdefault('pady', 10)
        super().__init__(parent, **kwargs)
        self.context = context
        self.is_expanded = False
        self.container = parent
        
        # Subscribe to logs
        self.context.event_bus.subscribe('LOG_MESSAGE', self._on_log)
        
        # Toggle Button using ButtonIcon
        self.toggle_btn = ButtonIcon(
            self, 
            icon_name="circle-chevron", 
            color="#44aaaa", 
            size=18, 
            bg="#111111", 
            rotation=0, # point up
            command=self._toggle
        )
        self.toggle_btn.grid(row=0, column=0, sticky=tk.W, padx=0, pady=0)
        
        # Minimized Label
        self.status_var = tk.StringVar(value="Ready.")
        self.status_label = tk.Label(self, textvariable=self.status_var, bg='#111111', fg='#44aaaa', font=('Consolas', 10), anchor=tk.W)
        self.status_label.grid(row=0, column=1, sticky=tk.EW, padx=5, pady=2)
        
        # Expanded Text Area (Hidden by default)
        self.text_frame = Frame(self)
        self.text_area = tk.Text(self.text_frame, height=8, state='disabled', bg='#222', fg='#ddd', font=('Consolas', 10))
        self.scrollbar = Scrollbar(self.text_frame, command=self.text_area.yview)
        self.text_area.configure(yscrollcommand=self.scrollbar.set)
        
        self.text_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
    def _toggle(self):
        self.is_expanded = not self.is_expanded
        if self.is_expanded:
            self.toggle_btn.update_icon(rotation=180) # point down
            self.status_label.grid_remove() # Hide single line
            self.text_frame.grid(row=0, column=1, sticky=tk.EW, padx=5, pady=2)
            # Ensure we scroll to bottom when opening
            self.text_area.yview_moveto(1)
        else:
            self.toggle_btn.update_icon(rotation=0) # point up
            self.text_frame.grid_remove() # Hide history
            self.status_label.grid() # Show single line


    def _on_log(self, message):
        # Update collapsed state
        self.status_var.set(str(message))
        
        # Update expanded state
        self.text_area.config(state='normal')
        self.text_area.insert(tk.END, str(message) + "\n")
        self.text_area.see(tk.END)
        self.text_area.config(state='disabled')


class PluginClass(SystemComponent):
    """Core console plugin."""
    def on_load(self, context):
        self.context = context

    def get_ui(self, parent_widget, zone):
        if zone == 'bottom_bar':
            # wrapper = Frame(parent_widget, borderwidth=0, relief="flat", padding=0)
            self.console = ConsoleFrame(parent_widget, self.context)
            self.console.pack(fill=tk.BOTH, expand=True)
            return self.console
        return None
