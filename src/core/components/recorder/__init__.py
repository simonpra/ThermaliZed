import tkinter as tk
from tkinter import filedialog
import os
import time

from src.core.plugin_base import SystemComponent
from src.core.components.recorder.engine import RecordingEngine
from src.core.components.recorder.player import RecordingPlayer
from src.core.components.recorder.ui import RecorderFrame, PlaybackOverlay

class PluginClass(SystemComponent):
    """Video Recorder plugin."""
    
    def on_load(self, context):
        self.context = context
        self.ui_components = []
        
        self.engine = None
        self.player = None
        self.overlay = None
        
        self.context.event_bus.subscribe('FRAME_READY', self._on_frame_ready)
        
    def get_ui(self, parent_widget, zone):
        if zone == 'left_sidebar':
            wrapper = tk.Frame(parent_widget)
            ui = RecorderFrame(wrapper, self.context, controller=self)
            ui.pack(fill=tk.BOTH, expand=False, pady=0, padx=0)
            self.ui_components.append(ui)
            return wrapper
        return None

    def on_unload(self, context):
        self.context.event_bus.unsubscribe('FRAME_READY', self._on_frame_ready)
        if self.engine and self.engine.is_recording:
            self.engine.stop_recording()
        if self.player and self.player.is_playing:
            self.player.stop_playback()
        if self.overlay:
            self.overlay.hide()

    def _on_frame_ready(self, frame_data):
        # We only record LIVE frames, not frozen/playback frames.
        if 'frozen_frame_data' in self.context.state and self.context.state['frozen_frame_data'] is not None:
             return
             
        if self.engine and self.engine.is_recording:
            self.engine.enqueue_frame(frame_data)

    def toggle_recording(self):
        if self.engine and self.engine.is_recording:
            # Stop recording
            self.engine.stop_recording()
            self.context.event_bus.publish('LOG_MESSAGE', f"Recording saved: {os.path.basename(self.engine.filepath)}")
            self.engine = None
        else:
            # Start recording
            if self.player and self.player.is_playing:
                 self.stop_playback()
                 
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
                self.context.event_bus.publish('LOG_MESSAGE', f"Started recording to: {os.path.basename(filepath)}")

    def load_recording(self):
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
                self.stop_playback()
                
            self.player = RecordingPlayer(filepath, self.context)
            self.player.start()
            
            # Show overlay
            if not self.overlay:
                self.overlay = PlaybackOverlay(controller=self)
            
            # Find canvas (it's injected in hud_context or we can get it from app context services if exposed)
            # Actually, standard plugin way to get canvas is via hud_context in HUD_DRAW or 
            # if we have a service. We can subscribe to HUD_DRAW once just to get the canvas,
            # or we can get it from a known service.
            # Let's subscribe to HUD_DRAW to attach the overlay safely.
            self.context.event_bus.subscribe('HUD_DRAW', self._attach_overlay)
            
            # Update UI state
            for ui in self.ui_components:
                if isinstance(ui, RecorderFrame):
                    ui.btn_play.config(state=tk.DISABLED)
                    ui.btn_stop_play.config(state=tk.NORMAL)
                    
            self.context.event_bus.publish('LOG_MESSAGE', f"Playing recording: {os.path.basename(filepath)}")

    def _attach_overlay(self, hud_context):
        canvas = hud_context.get('canvas')
        if canvas and self.overlay and not self.overlay.visible:
            self.overlay.show(canvas)
            # Unsubscribe once attached
            self.context.event_bus.unsubscribe('HUD_DRAW', self._attach_overlay)

    def stop_playback(self):
        if self.player:
            self.player.stop_playback()
            self.player = None
            
        if self.overlay:
            self.overlay.hide()
            self.overlay = None
            try:
                self.context.event_bus.unsubscribe('HUD_DRAW', self._attach_overlay)
            except ValueError:
                pass
            
        self.context.state['frozen_frame_data'] = None
        
        for ui in self.ui_components:
            if isinstance(ui, RecorderFrame):
                ui.btn_play.config(state=tk.NORMAL)
                ui.btn_stop_play.config(state=tk.DISABLED)
                
        self.context.event_bus.publish('LOG_MESSAGE', "Stopped playback. Resumed live feed.")
