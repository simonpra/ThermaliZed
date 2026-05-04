import tkinter as tk
import sys
from src.gui.about import show_about_dialog

class ApplicationMenu:
    """Handles the application menu bar and cross-platform differences."""
    
    def __init__(self, app):
        self.app = app
        self.root = app
        self.menubar = tk.Menu(self.root)
        
        self._setup_menus()
        
        # IMPORTANT: Configure root menu AFTER setting it up for macOS to respect it properly
        self.root.config(menu=self.menubar)
        
    def _setup_menus(self):
        is_macos = sys.platform == "darwin"
        
        # File Menu (common for both)
        self.file_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="File", menu=self.file_menu)
        
        if is_macos:
            self.file_menu.add_command(label="Load Snapshot...", command=self._load_snapshot, accelerator="Cmd+O")
            self.file_menu.add_command(label="Save Snapshot...", command=self._save_snapshot, accelerator="Cmd+S")
            
            # Hook into native macOS Application menu (the one named "Python" when running from CLI)
            # When bundled with PyInstaller, this will automatically become "About ThermaliZed"
            self.root.createcommand('tk::mac::ShowAbout', self._show_about)
            self.root.createcommand('tk::mac::Quit', self._quit_app)
            
            # (Optional) Help menu can still exist on Mac, or we can just rely on Application -> About
            self.help_menu = tk.Menu(self.menubar, tearoff=0)
            self.menubar.add_cascade(label="Help", menu=self.help_menu)
            self.help_menu.add_command(label="About ThermaliZed", command=self._show_about)
            
        else:
            self.file_menu.add_command(label="Load Snapshot...", command=self._load_snapshot, accelerator="Ctrl+O")
            self.file_menu.add_command(label="Save Snapshot...", command=self._save_snapshot, accelerator="Ctrl+S")
            self.file_menu.add_separator()
            self.file_menu.add_command(label="Exit", command=self._quit_app, accelerator="Alt+F4")
            
            self.help_menu = tk.Menu(self.menubar, tearoff=0)
            self.menubar.add_cascade(label="Help", menu=self.help_menu)
            self.help_menu.add_command(label="About", command=self._show_about)
            
        # Bind keyboard shortcuts
        self._bind_shortcuts(is_macos)

    def _bind_shortcuts(self, is_macos):
        if is_macos:
            self.root.bind("<Command-o>", lambda e: self._load_snapshot())
            self.root.bind("<Command-s>", lambda e: self._save_snapshot())
        else:
            self.root.bind("<Control-o>", lambda e: self._load_snapshot())
            self.root.bind("<Control-s>", lambda e: self._save_snapshot())
            
    def _show_about(self):
        show_about_dialog(self.root, getattr(self.app, 'version', 'Unknown'))
        
    def _quit_app(self):
        # Call the app's close handler
        if hasattr(self.app, '_on_closing'):
            self.app._on_closing()
        else:
            self.root.destroy()
        
    def _load_snapshot(self):
        if hasattr(self.app, 'context'):
            self.app.context.event_bus.publish("LOAD_SNAPSHOT_REQUEST")
            
    def _save_snapshot(self):
        if hasattr(self.app, 'context'):
            self.app.context.event_bus.publish("SAVE_SNAPSHOT_REQUEST")
