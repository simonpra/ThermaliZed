"""
TickEngine — High-Frequency Async Redraw Pipeline
==================================================
Drives a ``canvas.after()`` loop for hover effects, animations, and
UI feedback that must remain fluid independently of the camera frame rate.

Typical usage
-------------
>>> tick = TickEngine(canvas, fps=30)
>>> tick.on_tick(my_redraw_callback)
>>> tick.start()

>>> # From a mouse-motion handler:
>>> tick.mark_dirty()

>>> # On plugin teardown:
>>> tick.stop()
"""
from __future__ import annotations

import tkinter as tk
from typing import Callable, List, Optional


class TickEngine:
    """
    Drives a periodic ``canvas.after()`` loop for async redraw pipelines.

    The engine only invokes registered callbacks when the ``dirty`` flag
    has been set via :meth:`mark_dirty`, keeping CPU overhead essentially
    zero when nothing has changed.

    Args:
        canvas: The Tkinter canvas to schedule ``after()`` calls on.
        fps: Target tick rate in frames per second (default: 30).
        event_bus: Optional event bus.  Reserved for future ``HUD_PIXEL_HOVER``
            emission; has no effect in the current version.
    """

    def __init__(
        self,
        canvas: tk.Canvas,
        fps: int = 30,
        event_bus=None,
    ) -> None:
        self._canvas: tk.Canvas = canvas
        self._tick_ms: int = max(1, 1000 // fps)
        self._event_bus = event_bus
        self._running: bool = False
        self._dirty: bool = False
        self._callbacks: List[Callable[[], None]] = []

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def start(self) -> None:
        """Kick off the tick loop if not already running."""
        if not self._running and self._canvas is not None:
            self._running = True
            self._canvas.after(self._tick_ms, self._tick)

    def stop(self) -> None:
        """Signal the tick loop to stop on its next iteration."""
        self._running = False

    def mark_dirty(self) -> None:
        """Request a redraw on the next tick."""
        self._dirty = True

    @property
    def is_dirty(self) -> bool:
        """``True`` if a redraw has been requested since the last tick."""
        return self._dirty

    def on_tick(self, callback: Callable[[], None]) -> None:
        """
        Register a callback to be invoked each tick when the engine is dirty.

        Args:
            callback: Zero-argument callable, invoked on the main Tkinter thread.
        """
        if callback not in self._callbacks:
            self._callbacks.append(callback)

    def remove_tick(self, callback: Callable[[], None]) -> None:
        """
        Unregister a previously registered tick callback.

        Args:
            callback: The callable to remove.  Silent no-op if not found.
        """
        try:
            self._callbacks.remove(callback)
        except ValueError:
            pass

    # ------------------------------------------------------------------
    # Internal loop
    # ------------------------------------------------------------------

    def _tick(self) -> None:
        """Periodic callback — fires registered callbacks when dirty."""
        canvas = self._canvas
        if canvas is None:
            self._running = False
            return
        try:
            if not canvas.winfo_exists():
                self._running = False
                return
        except tk.TclError:
            self._running = False
            return

        if self._dirty:
            for cb in self._callbacks:
                try:
                    cb()
                except Exception as exc:
                    print(f"[TickEngine] callback raised: {exc}")
            self._dirty = False

        if self._running:
            canvas.after(self._tick_ms, self._tick)
