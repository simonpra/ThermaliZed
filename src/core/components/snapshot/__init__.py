import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
import numpy as np
import os
import time

from src.core.plugin_base import SystemComponent

class SnapshotFrame(ttk.LabelFrame):
    """
    Snapshot plugin UI component. Provides tools for saving the current raw thermal 
    frame to disk, and loading frozen files for offline processing.
    """
    def __init__(self, parent, context, **kwargs):
        super().__init__(parent, text="Snapshot & Freeze", padding=10, **kwargs)
        self.context = context
        self.last_frame_data = None
        
        self.context.event_bus.subscribe('FRAME_READY', self._on_frame_ready)
        
        self._build_ui()
        
    def _build_ui(self):
        # Tools layout
        tools_frame = ttk.Frame(self)
        tools_frame.pack(fill=tk.X, expand=True)

        self.btn_snap = ttk.Button(tools_frame, text="Take Snapshot", command=self._take_snapshot)
        self.btn_snap.pack(side=tk.TOP, fill=tk.X, pady=0)
        
        self.btn_load = ttk.Button(tools_frame, text="Load Snapshot", command=self._load_snapshot)
        self.btn_load.pack(side=tk.TOP, fill=tk.X, pady=0)
        
        self.btn_resume = ttk.Button(tools_frame, text="Resume Live", command=self._resume_live, state=tk.DISABLED)
        self.btn_resume.pack(side=tk.TOP, fill=tk.X, pady=0)

    def _on_frame_ready(self, frame_data):
        # We just keep a copy of the latest live frame for snapping
        # Only update if we are not currently frozen, or if we want to snap
        # wait, if frozen, frame_data IS the frozen frame.
        if 'frozen_frame_data' not in self.context.state or self.context.state['frozen_frame_data'] is None:
            self.last_frame_data = frame_data

    def _take_snapshot(self):
        if not self.last_frame_data:
            self.context.event_bus.publish('LOG_MESSAGE', "Error: No frame data available to snapshot.")
            return

        initial_dir = os.path.expanduser("~/Pictures/TC001_Snapshots")
        if not os.path.exists(initial_dir):
            try:
                os.makedirs(initial_dir)
            except:
                initial_dir = os.path.expanduser("~")

        timestamp_str = time.strftime("%Y%m%d_%H%M%S")
        default_name = f"tc001_snap_{timestamp_str}.npz"

        filepath = filedialog.asksaveasfilename(
            initialdir=initial_dir,
            title="Save Snapshot",
            initialfile=default_name,
            defaultextension=".npz",
            filetypes=(("Numpy Zipped Files", "*.npz"), ("All Files", "*.*"))
        )

        if filepath:
            try:
                # Save the raw data and metadata
                np.savez_compressed(
                    filepath,
                    frame=self.last_frame_data['frame'],
                    width=self.last_frame_data['width'],
                    height=self.last_frame_data['height'],
                    stride=self.last_frame_data['stride']
                )
                self.context.event_bus.publish('LOG_MESSAGE', f"Snapshot saved to: {os.path.basename(filepath)}")
            except Exception as e:
                self.context.event_bus.publish('LOG_MESSAGE', f"Failed to save snapshot: {e}")

    def _load_snapshot(self):
        initial_dir = os.path.expanduser("~/Pictures/TC001_Snapshots")
        if not os.path.exists(initial_dir):
             initial_dir = os.path.expanduser("~")

        filepath = filedialog.askopenfilename(
            initialdir=initial_dir,
            title="Load Snapshot",
            filetypes=(("Numpy Zipped Files", "*.npz"), ("All Files", "*.*"))
        )

        if filepath:
            try:
                data = np.load(filepath)
                frozen_data = {
                    'frame': data['frame'],
                    'width': int(data['width']),
                    'height': int(data['height']),
                    'stride': int(data['stride']),
                    'timestamp': time.time()
                }
                
                self.context.state['frozen_frame_data'] = frozen_data
                self.btn_resume.config(state=tk.NORMAL)
                self.context.event_bus.publish('LOG_MESSAGE', f"Loaded snapshot: {os.path.basename(filepath)}")
                
            except Exception as e:
                self.context.event_bus.publish('LOG_MESSAGE', f"Failed to load snapshot: {e}")

    def _resume_live(self):
        self.context.state['frozen_frame_data'] = None
        self.btn_resume.config(state=tk.DISABLED)
        self.context.event_bus.publish('LOG_MESSAGE', "Resumed live feed.")

class PluginClass(SystemComponent):
    """Snapshot plugin for taking and loading still frames."""
    
    def on_load(self, context):
        self.context = context
        
    def get_ui(self, parent_widget, zone):
        if zone == 'left_sidebar':
            wrapper = ttk.Frame(parent_widget, padding=5)
            ui = SnapshotFrame(wrapper, self.context)
            ui.pack(fill=tk.BOTH, expand=False, pady=0, padx=0)
            return wrapper
        return None
