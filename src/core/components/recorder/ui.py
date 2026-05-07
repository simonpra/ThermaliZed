import tkinter as tk
from tkinter import ttk
import os
import time

from src.gui.components import LabelFrame, Button, Label, Frame, ButtonIcon, Slider
from src.core.components.overlay.canvas_overlay import CanvasOverlay

class RecorderFrame(LabelFrame):
    """
    Recorder plugin UI component. Provides tools for saving the raw thermal
    stream to disk as a compressed .trv file.
    """
    def __init__(self, parent, context, controller, **kwargs):
        super().__init__(parent, text="Video Recorder", padding=10, **kwargs)
        self.context = context
        self.controller = controller
        
        self._build_ui()
        
        # Start UI Update loop
        self.after(500, self._update_ui_stats)

    def _build_ui(self):
        tools_frame = Frame(self)
        tools_frame.pack(fill=tk.X, expand=True)

        # Record Button
        self.btn_record = Button(tools_frame, text="Start Recording", command=self.controller.toggle_recording)
        self.btn_record.pack(side=tk.TOP, fill=tk.X, pady=2)
        
        # Stats Label
        self.lbl_stats = Label(tools_frame, text="Ready", font=("Arial", 10))
        self.lbl_stats.pack(side=tk.TOP, fill=tk.X, pady=2)
        
        ttk.Separator(tools_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=5)
        
        # Play Button
        self.btn_play = Button(tools_frame, text="Load Recording", command=self.controller.load_recording)
        self.btn_play.pack(side=tk.TOP, fill=tk.X, pady=2)
        
        # Stop Playback Button
        self.btn_stop_play = Button(tools_frame, text="Stop Playback / Resume Live", command=self.controller.stop_playback, state=tk.DISABLED)
        self.btn_stop_play.pack(side=tk.TOP, fill=tk.X, pady=2)

    def _update_ui_stats(self):
        engine = self.controller.engine
        if engine and engine.is_recording:
            elapsed = time.time() - engine.start_time
            mb_written = engine.bytes_written / (1024 * 1024)
            self.lbl_stats.config(
                text=f"{int(elapsed)}s | {engine.frames_written} frames | {mb_written:.1f} MB"
            )
            self.btn_record.config(text="Stop Recording")
        else:
            self.btn_record.config(text="Start Recording")
            
        # Conditionally show/hide Start Recording button based on camera connection
        devices = self.context.state.get('devices', [])
        if not devices:
            # No camera connected, hide record button
            if self.btn_record.winfo_viewable():
                self.btn_record.pack_forget()
                self.lbl_stats.config(text="No camera connected")
        else:
            # Camera connected, show record button
            if not self.btn_record.winfo_viewable():
                self.btn_record.pack(side=tk.TOP, fill=tk.X, pady=2, before=self.lbl_stats)
                if not (engine and engine.is_recording):
                     self.lbl_stats.config(text="Ready")
                
        if self.winfo_exists():
            self.after(500, self._update_ui_stats)


class PlaybackOverlay(CanvasOverlay):
    """
    Overlay that appears on the canvas during playback to provide transport controls.
    """
    def __init__(self, controller, **kwargs):
        super().__init__(x=20, y=20, anchor='se', **kwargs)
        self.controller = controller
        
    def _build_overlay_content(self, frame: ttk.Frame) -> None:
        # Container for buttons
        buttons_frame = Frame(frame)
        buttons_frame.pack(side=tk.TOP, fill=tk.X, pady=(0, 5))

        # Step Backward Button
        self.btn_step_back = ButtonIcon(
            buttons_frame, 
            icon_name="step-backward", 
            size=32, 
            color="#ffffff", 
            command=self._step_backward
        )
        self.btn_step_back.pack(side=tk.LEFT, padx=5, expand=True)
        
        # Play/Pause Button
        self.btn_play_pause = ButtonIcon(
            buttons_frame, 
            icon_name="pause", 
            size=32, 
            color="#ffffff", 
            command=self._toggle_play_pause
        )
        self.btn_play_pause.pack(side=tk.LEFT, padx=5, expand=True)
        
        # Step Forward Button
        self.btn_step_fwd = ButtonIcon(
            buttons_frame, 
            icon_name="step-forward", 
            size=32, 
            color="#ffffff", 
            command=self._step_forward
        )
        self.btn_step_fwd.pack(side=tk.LEFT, padx=5, expand=True)

        # Timeline Slider
        self.timeline_slider = Slider(
            frame,
            from_=0,
            to=100, # Will be updated dynamically
            command=self._on_slider_change
        )
        self.timeline_slider.pack(side=tk.TOP, fill=tk.X, padx=5, pady=(0, 5))

        # Start the loop to keep the slider in sync
        self._slider_update_loop()

        # Initial state setup
        self._update_button_states()

    def _on_slider_change(self, value):
        if self.controller.player:
            new_frame_idx = int(float(value))
            # Seek if it's a manual change (to avoid feedback loop)
            if abs(self.controller.player.current_frame_idx - new_frame_idx) > 1:
                self.controller.player.seek_frame(new_frame_idx)

    def _slider_update_loop(self):
        if self.controller.player and hasattr(self, 'timeline_slider') and self.timeline_slider.winfo_exists():
            player = self.controller.player
            total_frames = max(1, len(player.frame_offsets) - 1)
            
            if self.timeline_slider.cget("to") != total_frames:
                self.timeline_slider.config(to=total_frames)

            current_idx = player.current_frame_idx
            # Only update if difference is meaningful
            if abs(int(float(self.timeline_slider.get())) - current_idx) >= 1:
                self.timeline_slider.set(current_idx)

        # Loop
        if self.overlay_frame and self.overlay_frame.winfo_exists():
             self.overlay_frame.after(100, self._slider_update_loop)

    def _toggle_play_pause(self):
        if self.controller.player:
            self.controller.player.toggle_pause()
            self._update_button_states()

    def _step_backward(self):
        if self.controller.player:
            self.controller.player.step_frame(-1)

    def _step_forward(self):
        if self.controller.player:
            self.controller.player.step_frame(1)

    def _update_button_states(self):
        if self.controller.player:
            if self.controller.player.is_paused:
                self.btn_play_pause.update_icon(icon_name="play")
            else:
                self.btn_play_pause.update_icon(icon_name="pause")
