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
            filetypes=(
                ("All Supported Files", "*.npz *.csv *.xlsx *.xls"),
                ("Numpy Zipped Files", "*.npz"),
                ("CSV Files", "*.csv"),
                ("Excel Files", "*.xlsx *.xls"),
                ("All Files", "*.*")
            )
        )

        if not filepath:
            return

        ext = os.path.splitext(filepath)[1].lower()
        if ext == '.npz':
            self._load_npz(filepath)
        elif ext == '.csv':
            self._load_csv(filepath)
        elif ext in ['.xlsx', '.xls']:
            self._load_excel(filepath)
        else:
            self.context.event_bus.publish('LOG_MESSAGE', f"Unsupported file type: {ext}")

    def _load_npz(self, filepath):
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

    def _clean_and_convert_data(self, df):
        def clean_and_convert(value):
            if isinstance(value, str):
                try:
                    return float(value.replace('°C', '').strip())
                except ValueError:
                    return np.nan
            elif isinstance(value, (int, float)):
                return float(value)
            else:
                return np.nan

        if hasattr(df, 'map'):
            data = df.map(clean_and_convert).to_numpy()
        else:
            data = df.applymap(clean_and_convert).to_numpy()

        min_val = np.nanmin(data)
        if np.isnan(min_val):
            min_val = 10.0
        data = np.nan_to_num(data, nan=min_val)
        return data

    def _create_raw_buffer(self, temperature_celsius_2d):
        thermal_h, thermal_w = temperature_celsius_2d.shape
        
        raw_16bit = (temperature_celsius_2d + 273.15) * 64.0
        raw_16bit = np.ascontiguousarray(np.round(raw_16bit).astype('<u2'))
        
        height = thermal_h * 2
        width = thermal_w
        stride = width * 2
        
        frame_packed = np.zeros((height, width, 2), dtype=np.uint8)
        thdata = raw_16bit.view(np.uint8).reshape(thermal_h, thermal_w, 2)
        frame_packed[thermal_h:, :, :] = thdata
        
        raw_flat_buffer = frame_packed.flatten()
        
        return {
            'frame': raw_flat_buffer,
            'width': width,
            'height': height,
            'stride': stride,
            'timestamp': time.time()
        }

    def _load_csv(self, filepath):
        try:
            import pandas as pd
        except ImportError:
            self.context.event_bus.publish('LOG_MESSAGE', "Error: pandas is required to load CSV files.")
            return

        try:
            df = pd.read_csv(filepath, header=None)
            data = self._clean_and_convert_data(df)
            frozen_data = self._create_raw_buffer(data)
            
            self.context.state['frozen_frame_data'] = frozen_data
            self.btn_resume.config(state=tk.NORMAL)
            self.context.event_bus.publish('LOG_MESSAGE', f"Loaded CSV snapshot: {os.path.basename(filepath)}")
        except Exception as e:
            self.context.event_bus.publish('LOG_MESSAGE', f"Failed to load CSV: {e}")

    def _load_excel(self, filepath):
        try:
            import pandas as pd
        except ImportError:
            self.context.event_bus.publish('LOG_MESSAGE', "Error: pandas and openpyxl are required to load Excel files.")
            return

        try:
            import openpyxl
        except ImportError:
             self.context.event_bus.publish('LOG_MESSAGE', "Error: openpyxl is required to load .xlsx files.")
             return

        try:
            df = pd.read_excel(filepath, header=None)
            data = self._clean_and_convert_data(df)
            frozen_data = self._create_raw_buffer(data)
            
            self.context.state['frozen_frame_data'] = frozen_data
            self.btn_resume.config(state=tk.NORMAL)
            self.context.event_bus.publish('LOG_MESSAGE', f"Loaded Excel snapshot: {os.path.basename(filepath)}")
        except Exception as e:
            self.context.event_bus.publish('LOG_MESSAGE', f"Failed to load Excel: {e}")

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
