import tkinter as tk
from tkinter import ttk
from src.gui.components import Frame, PanedWindow, ScrollableFrame
from src.core.app_context import AppContext

class ThermalApp(tk.Tk):
    """Main window for the Tkinter TC001 Thermal Camera application."""
    
    def __init__(self):
        super().__init__()
        
        self.title("ThermaliZed - Thermal Camera Viewer")
        self.geometry("1000x750")
        self.minsize(800, 600)
        
        # Build UI Zones FIRST before initializing context because plugins might need to attach immediately
        self.zones = {}
        self._build_dynamic_zones()
        
        # Initialize context (loads plugins and binds them to zones automatically if they request it)
        self.context = AppContext(self)
        self._mount_plugins()
        
        # Close handler
        self.protocol("WM_DELETE_WINDOW", self._on_closing)

    def _build_dynamic_zones(self):
        """
        Constructs the primary layout regions (zones) of the application.
        These abstract zones allow components to attach themselves to UI regions.
        """
        # --- Horizontal Layout: Fixed Sidebar + Main Area ---
        
        # Left Sidebar: Scrollable and fixed width (no sash/not resizable)
        self.zones['left_sidebar'] = ScrollableFrame(self, padding=5, width=300)
        self.zones['left_sidebar'].pack_propagate(False) # Keep fixed width regardless of content
        self.zones['left_sidebar'].pack(side=tk.LEFT, fill=tk.Y, expand=False)
        
        # Right container for the main content and console
        self.right_container = Frame(self)
        self.right_container.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # --- Vertical Layout in Right Area: Content (Top) vs Console (Bottom) ---
        
        self.vertical_paned = PanedWindow(self.right_container, orient=tk.VERTICAL)
        self.vertical_paned.pack(fill=tk.BOTH, expand=True)
        
        # Main Content Zone (Video/Camera Preview)
        self.zones['main_content'] = Frame(self.vertical_paned, relief=tk.SUNKEN)
        self.vertical_paned.add(self.zones['main_content'], weight=1)
        
        # Bottom Console Zone (Logs/Status)
        self.zones['bottom_bar'] = Frame(self.vertical_paned, relief=tk.FLAT, padding=0)
        self.vertical_paned.add(self.zones['bottom_bar'], weight=0)
        
    def _mount_plugins(self):
        """
        Iterates over discovered plugins within the AppContext and asks each
        plugin to voluntarily inject UI components into available layout zones.
        """
        for plugin in self.context.plugins:
            for zone_name, zone_frame in self.zones.items():
                
                # If this zone is a ScrollableFrame, plugins must attach to its inner content frame
                target_parent = zone_frame
                if hasattr(zone_frame, 'scrollable_content'):
                    target_parent = zone_frame.scrollable_content
                    
                ui_component = plugin.get_ui(target_parent, zone_name)
                if ui_component:
                    ui_component.pack(fill=tk.BOTH, expand=True)

    def _on_closing(self):
        """
        Application shutdown handler. Cleans up camera resources and notifies
        plugins to safely unmount and save state.
        """
        # Notify plugins of unload
        for plugin in self.context.plugins:
            try:
                plugin.on_unload(self.context)
            except Exception as e:
                print(f"Error unloading plugin: {e}")
                
        camera = self.context.get_service('camera')
        if camera:
            camera.stop()
        self.destroy()
