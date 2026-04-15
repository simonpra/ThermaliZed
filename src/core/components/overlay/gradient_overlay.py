import tkinter as tk
from tkinter import ttk
from typing import Optional
from src.utils.constants import COLORMAPS
from src.utils.functions import to_degrees_c
from .canvas_overlay import CanvasOverlay
from .vertical_gradient import GradientLine

class GradientOverlay(CanvasOverlay):
    """Displays the active cv2 colormap as a vertical gradient.

    Listens to:
      - COLORMAP_CHANGED : updates the colormap swatch.
      - METADATA_READY   : refreshes temperature labels, gradient steps,
                           and the gamma mid-tone warp of the swatch.
    """

    def __init__(self, context, **kwargs):
        super().__init__(**kwargs)
        self._context = context
        self._gradient_line: Optional[GradientLine] = None
        self._label_canvas: Optional[tk.Canvas] = None
        context.event_bus.subscribe('COLORMAP_CHANGED', self._on_colormap_changed)
        context.event_bus.subscribe('METADATA_READY', self._on_hud_data)

    def _build_overlay_content(self, frame: ttk.Frame) -> None:
        container = ttk.Frame(frame, borderwidth=0, padding=0, border=0, relief='flat')
        container.pack(pady=0, padx=0)

        colormap_idx = self._context.state['params']['colormap_index']
        current_colormap = COLORMAPS[colormap_idx][0]

        self._gradient_line = GradientLine(
            container,
            height=200, line_width=30,
            colormap=current_colormap,
        )
        self._gradient_line.pack(side=tk.LEFT, pady=0, padx=0)

        # Canvas for temperature labels, perfectly aligned with the swatch
        self._label_canvas = tk.Canvas(
            container, width=50, height=200, highlightthickness=0, bd=0
        )
        self._label_canvas.pack(side=tk.LEFT, fill=tk.Y, padx=(4, 0))
        self._draw_labels(0.0, 0.0)

    def _draw_labels(self, min_val: float, max_val: float) -> None:
        if self._label_canvas is None:
            return

        self._label_canvas.delete('all')
        height = 200
        padding_y = 6

        temps = [
            (max_val,                              0 + padding_y),
            (min_val + (max_val - min_val) * 2/3,  height / 3),
            (min_val + (max_val - min_val) / 3,    height * 2 / 3),
            (min_val,                              height - padding_y),
        ]

        for val, y in temps:
            text_val = "--°C" if str(val) == 'nan' else f"{val:.1f}°C"
            self._label_canvas.create_text(
                0, y,
                text=text_val,
                anchor='w',
                font=("", 11),
            )

    def _on_colormap_changed(self, cv2_colormap: int) -> None:
        if self._gradient_line is not None:
            # Preserve current gamma/alpha and steps when only the colormap changes
            params = self._context.state.get('params', {})
            gamma = params.get('gamma', 1.0)
            alpha = params.get('alpha', 1.0)
            steps = getattr(self._gradient_line, '_steps', 0)
            self._gradient_line.update_colormap(cv2_colormap, gamma=gamma, alpha=alpha, steps=steps)

    def _on_hud_data(self, hud_data: dict) -> None:
        # --- Temperature labels ---
        min_raw = hud_data.get('norm_min', float('nan'))
        max_raw = hud_data.get('norm_max', float('nan'))
        min_c = to_degrees_c(min_raw)
        max_c = to_degrees_c(max_raw)
        self._draw_labels(min_c, max_c)

        # --- Gradient steps ---
        gradient_step = hud_data.get('gradient_step', 0.0)
        temp_range = max_c - min_c
        if gradient_step > 0 and temp_range > 0:
            num_steps = max(1, round(temp_range / gradient_step))
        else:
            num_steps = 0

        # --- Gamma warp and Alpha Contrast (visual feedback) ---
        params = self._context.state.get('params', {})
        gamma = params.get('gamma', 1.0)
        alpha = params.get('alpha', 1.0)

        if self._gradient_line is not None:
            self._gradient_line.set_steps(num_steps, gamma=gamma, alpha=alpha)