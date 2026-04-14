import tkinter as tk
from tkinter import ttk
from typing import Literal, Optional

_Anchor = Literal['nw', 'n', 'ne', 'w', 'center', 'e', 'sw', 's', 'se']


class CanvasOverlay:
    """
    Reusable base class that embeds a ttk.Frame onto a tk.Canvas via create_window.

    Position is expressed as a pixel offset (x, y) relative to the chosen anchor corner:
        'nw'     → offset from top-left
        'ne'     → offset from top-right      (x = distance from right edge)
        'sw'     → offset from bottom-left    (y = distance from bottom edge)
        'se'     → offset from bottom-right
        'center' → (x, y) are added to canvas centre

    Two ways to provide content
    ---------------------------
    1. **Subclass** and override ``_build_overlay_content(frame)``::

        class MyOverlay(CanvasOverlay):
            def _build_overlay_content(self, frame: ttk.Frame) -> None:
                ttk.Label(frame, text="Hello").pack()

        overlay = MyOverlay(x=10, y=10, anchor='ne')
        overlay.show(canvas)

    2. **Supply a pre-built frame** via the constructor or attribute::

        frame = ttk.Frame(canvas)
        ttk.Label(frame, text="Hello").pack()
        overlay = CanvasOverlay(x=10, y=10, anchor='ne', overlay_frame=frame)
        overlay.show(canvas)

    The canvas ``<Configure>`` event is handled automatically to keep the overlay
    in the correct corner when the window is resized.
    Multiple ``CanvasOverlay`` instances on the same canvas are fully independent.
    """

    def __init__(
        self,
        x: int = 10,
        y: int = 10,
        anchor: _Anchor = 'ne',
        overlay_frame: Optional[ttk.Frame] = None,
    ):
        self._x = x
        self._y = y
        self._anchor: _Anchor = anchor
        # Keep track of the user-supplied frame so we never destroy it on hide().
        self._given_frame: Optional[ttk.Frame] = overlay_frame
        self.overlay_frame: Optional[ttk.Frame] = overlay_frame
        self._window_id: Optional[int] = None
        self._canvas: Optional[tk.Canvas] = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def show(self, canvas: tk.Canvas) -> None:
        """Embed the overlay onto *canvas*. No-op if already visible."""
        if self._window_id:
            return

        self._canvas = canvas

        if self.overlay_frame is None:
            self.overlay_frame = ttk.Frame(canvas, padding=2, relief='flat', borderwidth=1)
            self._build_overlay_content(self.overlay_frame)

        cx, cy = self._compute_canvas_xy(canvas.winfo_width(), canvas.winfo_height())
        self._window_id = canvas.create_window(
            cx, cy, window=self.overlay_frame, anchor=self._anchor
        )
        # add='+' so multiple overlays on the same canvas don't overwrite each other's binding.
        canvas.bind("<Configure>", self._on_canvas_resize, add='+')

    def hide(self) -> None:
        """Remove the overlay from the canvas."""
        if self._window_id and self._canvas:
            self._canvas.delete(self._window_id)
            self._window_id = None

            # Only destroy the frame if we created it ourselves.
            if self._given_frame is None and self.overlay_frame is not None:
                self.overlay_frame.destroy()
                self.overlay_frame = None

    @property
    def visible(self) -> bool:
        return self._window_id is not None

    # ------------------------------------------------------------------
    # Override in subclasses
    # ------------------------------------------------------------------

    def _build_overlay_content(self, frame: ttk.Frame) -> None:
        """Populate *frame* with widgets.  Override in subclasses."""

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _compute_canvas_xy(self, w: int, h: int) -> tuple[int, int]:
        if self._anchor == 'center':
            return w // 2 + self._x, h // 2 + self._y
        cx = (w - self._x) if 'e' in self._anchor else self._x
        cy = (h - self._y) if 's' in self._anchor else self._y
        return cx, cy

    def _on_canvas_resize(self, event: tk.Event) -> None:
        if self._window_id and self._canvas:
            cx, cy = self._compute_canvas_xy(event.width, event.height)
            self._canvas.coords(self._window_id, cx, cy)
