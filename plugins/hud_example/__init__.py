from __future__ import annotations

import tkinter as tk
from typing import Optional

from src.core.plugin_base import SystemComponent
from src.utils.hud import HUDEngine, LAYER_MAIN

class PluginClass(SystemComponent):
    """
    Simple HUD example plugin.
    Auto-discovered and loaded by ``AppContext``.
    """

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------
    def __init__(self):
        super().__init__()
        # everything will be INIT in on_load()
        self.context = None

        # HUDEngine instance — only used for selection rendering.
        self._hud:       Optional[HUDEngine]          = None

        # ── Shared state ──────────────────────────────────────────────
        # Reference to the canvas widget (set on first HUD_DRAW).
        self._canvas:    Optional[tk.Canvas]          = None
        # Latest 16-bit sensor frame for temperature look-up.
        self._raw_16bit = None

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------
    def on_load(self, context):
        self.context = context
        # SUBSCRIBE on the HUD_DRAW hook
        context.event_bus.subscribe("HUD_DRAW", self._on_hud_draw)

    def on_unload(self, context):
        if context is not None and getattr(context, "event_bus", None) is not None:
            context.event_bus.unsubscribe("HUD_DRAW", self._on_hud_draw)
        self._unbind_canvas()
        self.context = None

    # ------------------------------------------------------------------
    # Canvas binding helpers
    # ------------------------------------------------------------------
    def _bind_canvas(self, canvas: tk.Canvas) -> None:
        """Attach mouse events; idempotent — only acts when canvas changes."""
        if self._canvas is canvas:
            return

        self._unbind_canvas()
        self._canvas = canvas
        # Use tKinter Events to bind your functions
        # canvas.bind("<Motion>",   self._on_motion)

    def _unbind_canvas(self) -> None:
        if self._canvas is None:
            return
        # try:
        #     # If tKinter Events are bind, don't forget to unbind them
        #     # self._canvas.unbind("<Motion>")
        # except tk.TclError:
        #     pass
        self._canvas = None

    # ------------------------------------------------------------------
    # HUD_DRAW callback — Called from on_load() with the "HUD_DRAW" subscription
    # ------------------------------------------------------------------
    def _on_hud_draw(self, hud_context: dict) -> None:
        """
        Called when HUD is being drawn. From HUD_DRAW subscription.

        Parameters
        ----------
        hud_context : dict
            ``canvas``      — tk.Canvas
            ``bbox``        — (x1, y1, x2, y2) bounding box of the rendered image
            ``raw_payload`` — dict with ``'16bit'`` → np.ndarray[uint16]
        """
        canvas      = hud_context.get("canvas")
        bbox        = hud_context.get("bbox")
        raw_payload = hud_context.get("raw_payload")

        if canvas is None or bbox is None or raw_payload is None:
            return

        raw_16bit = raw_payload.get("16bit")
        if raw_16bit is None:
            return

        self._raw_16bit = raw_16bit

        # INIT HUDEngine with the tKinter Canvas object
        if self._hud is None or self._hud.canvas is not canvas:
            self._hud = HUDEngine(canvas)

        # Bind canvas
        self._bind_canvas(canvas)

        # MAP the sensor space to the canvas space (user screen)
        self._hud.set_sensor_mapping(bbox, raw_16bit.shape)

        # Draw selection border + temperature label
        self._draw()
    
    def _draw(self) -> None:
        hud = self._hud
        if hud is None:
            return
        
        # CLEAR the background layer on wich we will draw
        LAYER = LAYER_MAIN
        hud.clear(layer=LAYER)
        
        # Draw a crosshair at the center of the sensor (128, 96) on the selected LAYER (background)
        hud.draw_sensor_crosshair(sx=128, sy=96, color="salmon", width=3, arm=30, layer=LAYER)
        hud.draw_sensor_smart_text(sx=128, sy=96, text="Center", color="white", bg_color=(0,0,0,50), layer=LAYER)
        hud.draw_sensor_pixel_rect(sx=128, sy=96, color="lime green", layer=LAYER, width=5)