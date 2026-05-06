import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
import os
import time

from src.core.plugin_base import SystemComponent
from src.core.components.recorder.engine import RecordingEngine
from src.core.components.recorder.player import RecordingPlayer

class RecorderFrame(ttk.LabelFrame):
    """
    Recorder plugin UI component. Provides tools for saving the raw thermal
    stream to disk as a compressed .trv file.
    """
    def __init__(self, parent, context, **kwargs):
        super().__init__(parent, text="Video Recorder", padding=10, **kwargs)
        self.context = context
        
        self.engine = None
        self.player = None
        
        self._build_ui()
        
        # Subscribe to frames for recording
        self.context.event_bus.subscribe('FRAME_READY', self._on_frame_ready)
        
        # UI Update loop
        self.after(500, self._update_ui_stats)
        
    def cleanup(self):
        """Unsubscribe from events and stop active processes."""
        self.context.event_bus.unsubscribe('FRAME_READY', self._on_frame_ready)
        if self.engine and self.engine.is_recording:
            self.engine.stop_recording()
        if self.player and self.player.is_playing:
            self.player.stop_playback()
            
    def _build_ui(self):
        tools_frame = ttk.Frame(self)
        tools_frame.pack(fill=tk.X, expand=True)

        # Record Button
        self.btn_record = ttk.Button(tools_frame, text="Start Recording", command=self._toggle_recording)
        self.btn_record.pack(side=tk.TOP, fill=tk.X, pady=2)
        
        # Stats Label
        self.lbl_stats = ttk.Label(tools_frame, text="Ready", font=("Arial", 10))
        self.lbl_stats.pack(side=tk.TOP, fill=tk.X, pady=2)
        
        ttk.Separator(tools_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=5)
        
        # Play Button
        self.btn_play = ttk.Button(tools_frame, text="Load Recording", command=self._load_recording)
        self.btn_play.pack(side=tk.TOP, fill=tk.X, pady=2)
        
        # Stop Playback Button
        self.btn_stop_play = ttk.Button(tools_frame, text="Stop Playback / Resume Live", command=self._stop_playback, state=tk.DISABLED)
        self.btn_stop_play.pack(side=tk.TOP, fill=tk.X, pady=2)

    def _toggle_recording(self):
        if self.engine and self.engine.is_recording:
            # Stop recording
            self.engine.stop_recording()
            self.btn_record.config(text="Start Recording")
            self.lbl_stats.config(text="Recording stopped.")
            self.context.event_bus.publish('LOG_MESSAGE', f"Recording saved: {os.path.basename(self.engine.filepath)}")
            self.engine = None
        else:
            # Start recording
            # Ensure we are not playing back
            if self.player and self.player.is_playing:
                 self._stop_playback()
                 
            # Get latest frame info to initialize the engine
            camera = self.context.get_service('camera')
            latest_frame = camera.get_latest_frame() if camera else None
            
            if not latest_frame:
                self.context.event_bus.publish('LOG_MESSAGE', "Error: No camera feed available to record.")
                return

            initial_dir = os.path.expanduser("~/Pictures/TC001_Recordings")
            if not os.path.exists(initial_dir):
                try:
                    os.makedirs(initial_dir)
                except OSError:
                    initial_dir = os.path.expanduser("~")

            timestamp_str = time.strftime("%Y%m%d_%H%M%S")
            default_name = f"tc001_vid_{timestamp_str}.trv"

            filepath = filedialog.asksaveasfilename(
                initialdir=initial_dir,
                title="Save Recording",
                initialfile=default_name,
                defaultextension=".trv",
                filetypes=(("Thermal Raw Video", "*.trv"), ("All Files", "*.*"))
            )

            if filepath:
                self.engine = RecordingEngine(
                    filepath, 
                    width=latest_frame['width'], 
                    height=latest_frame['height'], 
                    fps=30.0
                )
                self.engine.start_recording()
                self.btn_record.config(text="Stop Recording")
                self.context.event_bus.publish('LOG_MESSAGE', f"Started recording to: {os.path.basename(filepath)}")

    def _on_frame_ready(self, frame_data):
        # We only record LIVE frames, not frozen/playback frames.
        # If 'frozen_frame_data' is active, we don't record it to avoid loops,
        # unless we explicitly want to record a processed stream (but here we record raw).
        if 'frozen_frame_data' in self.context.state and self.context.state['frozen_frame_data'] is not None:
             return
             
        if self.engine and self.engine.is_recording:
            self.engine.enqueue_frame(frame_data)

    def _update_ui_stats(self):
        if self.engine and self.engine.is_recording:
            elapsed = time.time() - self.engine.start_time
            mb_written = self.engine.bytes_written / (1024 * 1024)
            self.lbl_stats.config(
                text=f"{int(elapsed)}s | {self.engine.frames_written} frames | {mb_written:.1f} MB"
            )
            
        if self.winfo_exists():
            self.after(500, self._update_ui_stats)

    def _load_recording(self):
        initial_dir = os.path.expanduser("~/Pictures/TC001_Recordings")
        if not os.path.exists(initial_dir):
             initial_dir = os.path.expanduser("~")

        filepath = filedialog.askopenfilename(
            initialdir=initial_dir,
            title="Load Recording",
            filetypes=(("Thermal Raw Video", "*.trv"), ("All Files", "*.*"))
        )

        if filepath:
            if self.player and self.player.is_playing:
                self.player.stop_playback()
                
            self.player = RecordingPlayer(filepath, self.context)
            self.player.start()
            
            self.btn_play.config(state=tk.DISABLED)
            self.btn_stop_play.config(state=tk.NORMAL)
            self.context.event_bus.publish('LOG_MESSAGE', f"Playing recording: {os.path.basename(filepath)}")

    def _stop_playback(self):
        if self.player:
            self.player.stop_playback()
            self.player = None
            
        self.context.state['frozen_frame_data'] = None
        self.btn_play.config(state=tk.NORMAL)
        self.btn_stop_play.config(state=tk.DISABLED)
        self.context.event_bus.publish('LOG_MESSAGE', "Stopped playback. Resumed live feed.")


class PluginClass(SystemComponent):
    """Video Recorder plugin."""
    
    def on_load(self, context):
        self.context = context
        self.ui_components = []
        
    def get_ui(self, parent_widget, zone):
        if zone == 'left_sidebar':
            wrapper = ttk.Frame(parent_widget, padding=5)
            ui = RecorderFrame(wrapper, self.context)
            ui.pack(fill=tk.BOTH, expand=False, pady=0, padx=0)
            self.ui_components.append(ui)
            return wrapper
        return None

    def on_unload(self, context):
        for ui in self.ui_components:
            if hasattr(ui, 'cleanup'):
                ui.cleanup()
        self.ui_components.clear()
