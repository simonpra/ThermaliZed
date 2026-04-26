import cv2
import tkinter as tk
from src.core.plugin_base import SystemComponent
from src.utils.functions import to_degrees_c
from src.utils.hud import HUDEngine, LAYER_MAIN


class PluginClass(SystemComponent):
    """
    Temperature-overlay plugin.

    Draws crosshairs and smart labels at the MIN / MAX temperature spots
    using HUDEngine so labels never bleed off the canvas edge and memory is
    managed automatically.
    """

    def __init__(self):
        super().__init__()
        self.context = None
        # HUDEngine instance — created once the canvas is available.
        self._hud: HUDEngine | None = None
        # Keep a snapshot of the last draw args so update() can redraw.
        self._last_draw_args = None

    def on_load(self, context):
        self.context = context
        if hasattr(self.context, 'event_bus'):
            # Draw HUD after the canvas image has been placed at its final position
            self.context.event_bus.subscribe('HUD_DRAW', self._on_hud_draw)

    # ------------------------------------------------------------------
    # Pipeline callback
    # ------------------------------------------------------------------

    def _on_hud_draw(self, hud_context: dict):
        """
        HUD_DRAW callback — fired by the renderer *after* the canvas
        image is placed/repositioned.

        Parameters
        ----------
        hud_context : dict
            Contains ``'canvas'``, ``'bbox'``, and ``'raw_payload'``.
        """
        canvas      = hud_context.get('canvas')
        bbox        = hud_context.get('bbox')
        raw_payload = hud_context.get('raw_payload')

        if not canvas or not bbox or not raw_payload:
            return

        raw_16bit = raw_payload.get('16bit')
        if raw_16bit is None:
            return

        self._last_draw_args = (canvas, bbox, raw_16bit)
        self._draw(*self._last_draw_args)

    # ------------------------------------------------------------------
    # Update hook — re-draws the last frame
    # ------------------------------------------------------------------

    def update(self):
        """Trigger a redraw using the most recently cached args."""
        if self._last_draw_args is not None:
            self._draw(*self._last_draw_args)

    # ------------------------------------------------------------------
    # Internal drawing implementation
    # ------------------------------------------------------------------

    def _draw(self, canvas: tk.Canvas, bbox: tuple, raw_16bit) -> None:
        """Perform the full HUD draw pass for one frame."""

        # Lazy-init or re-init the HUDEngine if the canvas changed
        if self._hud is None or self._hud.canvas is not canvas:
            self._hud = HUDEngine(canvas)
            # Register update() as the draw-fn so resize triggers a redraw
            self._hud.finalize(self.update)

        hud = self._hud
        hud.clear()

        # Configure sensor mapping from the image bounding box
        hud.set_sensor_mapping(bbox, raw_16bit.shape)

        # Compute min / max temperature values
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(raw_16bit)
        min_temp_c = to_degrees_c(min_val)
        max_temp_c = to_degrees_c(max_val)

        # Draw MAX hotspot — red crosshair + smart label
        hud.draw_sensor_crosshair(max_loc[0], max_loc[1], color="red", layer=LAYER_MAIN)
        hud.draw_sensor_smart_text(
            max_loc[0], max_loc[1],
            text=f"MAX: {max_temp_c} °C",
            color="red",
            bg_color="black",
            layer=LAYER_MAIN,
        )

        # Draw MIN coldspot — cyan crosshair + smart label
        hud.draw_sensor_crosshair(min_loc[0], min_loc[1], color="#00FFFF", layer=LAYER_MAIN)
        hud.draw_sensor_smart_text(
            min_loc[0], min_loc[1],
            text=f"MIN: {min_temp_c} °C",
            color="#00FFFF",
            bg_color="black",
            layer=LAYER_MAIN,
        )
