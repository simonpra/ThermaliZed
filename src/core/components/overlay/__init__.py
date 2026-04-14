import tkinter as tk
from tkinter import ttk
from typing import Optional
import numpy as np

from src.core.plugin_base import SystemComponent
from .base_controls import BaseOverlayControl
from .gradient_overlay import GradientOverlay


class OverlayControls(BaseOverlayControl):
    """Sidebar panel for the gradient canvas overlay.

    Inherits the "Show Overlay" checkbutton + canvas wiring from
    :class:`BaseOverlayControl`.  Only the gradient-step spinbox is added
    here via :meth:`_build_controls`.
    """

    def __init__(self, parent, context, **kwargs):
        super().__init__(
            parent,
            context,
            overlay=GradientOverlay(context=context, x=10, y=10, anchor='ne'),
            title="Overlay",
            param_key="overlay_gradient_visible",
            **kwargs,
        )

    # ------------------------------------------------------------------
    # Feature-specific controls (called automatically by BaseOverlayControl)
    # ------------------------------------------------------------------

    def _build_controls(self) -> None:
        self._step_var = tk.DoubleVar(value=self.params.get('gradient_step', 0.0))
        self.add_label_slider(self.current_row, "Gradient Step (°C):", self._step_var, 0.0, 10.0, 0.1, self._on_step_changed)

    def _on_step_changed(self, event=None) -> None:
        try:
            val = float(self._step_var.get())
            val = max(0.0, round(val, 1))
            self.params['gradient_step'] = val
        except ValueError:
            pass


class PluginClass(SystemComponent):
    """Overlay plugin: provides the gradient HUD and gradient-step pipeline processing."""

    def on_load(self, context):
        self.context = context
        # Register as a RAW_FRAME_PIPELINE stage (fires after 16-bit array is assembled in processor.py)
        context.event_bus.subscribe('RAW_FRAME_PIPELINE', self._on_raw_frame_pipeline)

    def _on_raw_frame_pipeline(self, raw_thermal_16bit: np.ndarray, raw: np.ndarray) -> Optional[np.ndarray]:
        """
        Quantize the 16-bit thermal array into discrete temperature steps.

        Called by processor.py immediately after raw_thermal_16bit is assembled,
        before normalization or colormap are applied. All downstream processing
        (min/max stats, normalization, colormap, scaling) will use the returned array.

        Args:
            raw_thermal_16bit: 2D uint16 array, shape (thermal_h, thermal_w).
            raw: Original flat uint8 camera buffer — do not modify.

        Returns:
            Quantized uint16 array of the same shape, or None to pass through unchanged.
        """
        params = self.context.state.get('params', {})
        gradient_step = params.get('gradient_step', 0.0)

        if gradient_step <= 0.0:
            return None  # Pass-through: no quantization

        try:
            # Step size in raw units (64 raw units = 1°C for the TC001)
            step_raw = 64.0 * gradient_step

            # Quantize: round every raw value to the nearest step boundary.
            # Using float32 for intermediate math to avoid uint16 overflow.
            data = raw_thermal_16bit.astype(np.float32)
            quantized = np.round(data / step_raw) * step_raw
            quantized = np.clip(quantized, 0, 65535).astype(np.uint16)

            return quantized

        except Exception as e:
            print(f"[GradientStep] Pipeline error: {e}")
            return None

    def get_ui(self, parent_widget, zone):
        if zone == 'left_sidebar':
            self.ui = OverlayControls(parent_widget, self.context)
            self.ui.pack(fill=tk.X, expand=False)
            return self.ui
        return None