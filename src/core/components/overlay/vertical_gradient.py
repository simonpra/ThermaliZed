import tkinter as tk
from tkinter import ttk
import numpy as np
import cv2

def hex_to_rgb(hex_color: str) -> tuple:
    h = hex_color.lstrip('#')
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

def rgb_to_hex(r: int, g: int, b: int) -> str:
    return f"#{r:02x}{g:02x}{b:02x}"

class GradientLine(ttk.Frame):
    def __init__(self, parent, height=200, line_width=8,
                 color_top="#0000ff", color_bottom="#ff0000",
                 colormap=None, **kwargs):
        super().__init__(parent, **kwargs)
        self._height = height
        self._line_width = line_width
        self._cv2_colormap = colormap if colormap is not None else 0
        self._steps = 0
        self._gamma = 1.0

        self._canvas = tk.Canvas(self, width=line_width, height=height,
                                 highlightthickness=0, bd=0)
        self._canvas.pack()
        if colormap is not None:
            self._draw_colormap(colormap)
        else:
            self._draw(height, line_width, color_top, color_bottom)

    def _draw(self, height: int, width: int, c1: str, c2: str) -> None:
        r1, g1, b1 = hex_to_rgb(c1)
        r2, g2, b2 = hex_to_rgb(c2)
        for i in range(height):
            t = i / max(height - 1, 1)
            color = rgb_to_hex(
                int(r1 + (r2 - r1) * t),
                int(g1 + (g2 - g1) * t),
                int(b1 + (b2 - b1) * t),
            )
            self._canvas.create_line(0, i, width, i, fill=color)

    def _draw_colormap(self, cv2_colormap: int, steps: int = 0, gamma: float = 1.0, alpha: float = 1.0) -> None:
        """Redraw by sampling a cv2 colormap. Top = high value (255), bottom = low (0).

        Args:
            cv2_colormap: OpenCV colormap constant.
            steps: Number of discrete color bands. 0 means smooth gradient.
            gamma: Mid-tone warp exponent. 1.0 = linear (no warp).
                   > 1 lifts shadows (matches Texture > 1 in the pipeline).
            alpha: Contrast multiplier. Stretches values around the midpoint.
        """
        self._canvas.delete('all')
        self._cv2_colormap = cv2_colormap
        self._steps = steps
        self._gamma = gamma
        self._alpha = alpha

        ramp = np.arange(256, dtype=np.uint8).reshape(1, 256)
        colored = cv2.applyColorMap(ramp, cv2_colormap)  # (1, 256, 3) BGR
        height, width = self._height, self._line_width

        for i in range(height):
            # Normalized pos: 1.0 at top (hot/bright), 0.0 at bottom (cold/dark)
            t = 1.0 - i / max(height - 1, 1)

            # 1. Apply Alpha contrast
            if alpha != 1.0:
                t = 0.5 + (t - 0.5) * alpha

            # 2. Apply Gamma warp to match the pipeline's texture transformation.
            if gamma != 1.0:
                t = np.clip(t, 0.0, 1.0)
                t = t ** (1.0 / gamma)

            # Snap to discrete steps if requested (gradient_step feature)
            if steps > 0:
                t = round(t * steps) / steps

            idx = int(np.clip(t * 255, 0, 255))
            b, g, r = int(colored[0, idx, 0]), int(colored[0, idx, 1]), int(colored[0, idx, 2])
            self._canvas.create_line(0, i, width, i, fill=rgb_to_hex(r, g, b))

    def update_colormap(self, cv2_colormap: int, gamma: float = 1.0, alpha: float = 1.0, steps: int | None = None) -> None:
        """Redraw the gradient to reflect a new cv2 colormap, preserving current steps/gamma/alpha
        unless explicitly overridden."""
        _steps = steps if steps is not None else getattr(self, '_steps', 0)
        self._draw_colormap(cv2_colormap, steps=_steps, gamma=gamma, alpha=alpha)

    def set_steps(self, steps: int, gamma: float = 1.0, alpha: float = 1.0) -> None:
        """Update the number of discrete steps and/or gamma/alpha, then redraw."""
        self._draw_colormap(
            getattr(self, '_cv2_colormap', 0),
            steps=steps,
            gamma=gamma,
            alpha=alpha,
        )