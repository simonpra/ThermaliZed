"""
interactive_canvas — Pixel Hover & Selection Plugin
=====================================================
Makes the thermal canvas interactive by tracking the mouse position and
allowing the user to pin a pixel selection with its temperature.

Behaviour
---------
* **Hover**     — A thin border follows the mouse, snapping to the exact
                  sensor pixel under the cursor.  Clears automatically
                  when the mouse leaves the image area.
                  Redraws are driven by a self-contained ``after()`` tick
                  loop so they are *fully independent of the frame pipeline*
                  (works correctly on frozen / still frames too).

* **Selection** — Left-click pins the currently hovered pixel.  A coloured
                  border stays visible and a smart label shows the
                  temperature in degrees Celsius.  Click again anywhere to
                  move the selection; right-click to clear it.
                  Selection drawing is tied to ``HUD_DRAW`` since it needs
                  the latest raw 16-bit data for temperature look-up.

Architecture — two independent draw layers
------------------------------------------
┌─────────────────────────────────────────────────────────────┐
│  Layer A — Hover (raw canvas item, NOT in HUDEngine)        │
│  • _hover_item_id : single canvas rectangle                  │
│  • Updated by _tick() via canvas.after() at HOVER_FPS        │
│  • Only redraws when _hover_dirty flag is set by <Motion>    │
└─────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────┐
│  Layer B — Selection (HUDEngine managed)                     │
│  • Redrawn inside _on_hud_draw() — fires on new frames,      │
│    param changes, or window resize.                          │
│  • Renders border + smart temperature label.                 │
└─────────────────────────────────────────────────────────────┘

Splitting the layers avoids a "clear() war" (HUDEngine.clear would
remove hover items if they were in drawn_items) and keeps the hot
mouse-motion path as cheap as possible — just one rectangle delete +
create per tick when the cursor has actually moved.
"""
from __future__ import annotations

import tkinter as tk
from typing import Optional, Tuple

from src.core.plugin_base import SystemComponent
from src.utils.hud_engine import HUDEngine
from src.utils.functions import to_degrees_c


# ---------------------------------------------------------------------------
# Visual constants — tweak here without touching logic
# ---------------------------------------------------------------------------

HOVER_COLOR   = "white"         # hover border colour
HOVER_WIDTH   = 1               # hover border stroke width (px)

SELECT_COLOR  = "#FFD700"       # gold — visible on all colormaps
SELECT_WIDTH  = 2               # selection border stroke width (px)

LABEL_FONT    = ("Helvetica", 10, "bold")
LABEL_BG      = (0, 0, 0, 180) # semi-transparent black RGBA
LABEL_FG      = "#FFD700"

# Tick rate for the hover redraw loop.  30 FPS is plenty smooth and
# generates only ~0.03 ms of canvas work per tick when nothing changed.
HOVER_FPS     = 30
_TICK_MS      = max(1, 1000 // HOVER_FPS)


class PluginClass(SystemComponent):
    """
    Interactive pixel selector for the thermal canvas.
    Auto-discovered and loaded by ``AppContext``.
    """

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------

    def __init__(self):
        super().__init__()
        self.context = None

        # ── Layer A: hover state ──────────────────────────────────────
        # Raw canvas item ID — NOT tracked by HUDEngine so clear() never
        # removes it.
        self._hover_item_id: Optional[int]         = None
        self._hovered:        Optional[Tuple[int, int]] = None
        # Set True by <Motion> when the pixel under the cursor changed.
        # Cleared by the tick after a redraw.
        self._hover_dirty:    bool                  = False
        # Guards against spawning multiple after() chains.
        self._tick_running:   bool                  = False

        # ── Layer B: selection state ──────────────────────────────────
        self._selected:  Optional[Tuple[int, int]] = None
        # HUDEngine instance — only used for selection rendering.
        self._hud:       Optional[HUDEngine]        = None

        # ── Shared state ──────────────────────────────────────────────
        # Reference to the canvas widget (set on first HUD_DRAW).
        self._canvas:    Optional[tk.Canvas]        = None
        # Latest 16-bit sensor frame for temperature look-up.
        self._raw_16bit = None

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def on_load(self, context):
        self.context = context
        context.event_bus.subscribe("HUD_DRAW", self._on_hud_draw)

    def on_unload(self, context):
        # Stop the tick loop on shutdown.
        self._tick_running = False
        self._unbind_canvas()

    # ------------------------------------------------------------------
    # Canvas binding helpers
    # ------------------------------------------------------------------

    def _bind_canvas(self, canvas: tk.Canvas) -> None:
        """Attach mouse events; idempotent — only acts when canvas changes."""
        if self._canvas is canvas:
            return

        self._unbind_canvas()
        self._canvas = canvas
        canvas.bind("<Motion>",   self._on_motion)
        canvas.bind("<Button-1>", self._on_click)
        canvas.bind("<Button-3>", self._on_right_click)
        canvas.bind("<Leave>",    self._on_leave)

    def _unbind_canvas(self) -> None:
        if self._canvas is None:
            return
        try:
            self._canvas.unbind("<Motion>")
            self._canvas.unbind("<Button-1>")
            self._canvas.unbind("<Button-3>")
            self._canvas.unbind("<Leave>")
        except tk.TclError:
            pass
        self._canvas = None

    # ------------------------------------------------------------------
    # Mouse event handlers  (Layer A)
    # ------------------------------------------------------------------

    def _on_motion(self, event: tk.Event) -> None:
        """
        Translate canvas coords → sensor pixel and set dirty flag.
        The actual redraw happens in the tick loop, not here.
        """
        if self._hud is None:
            return
        new_pixel = self._hud.canvas_to_sensor(event.x, event.y)
        if new_pixel != self._hovered:
            self._hovered = new_pixel
            self._hover_dirty = True   # signal tick to redraw

    def _on_click(self, event: tk.Event) -> None:
        """Pin/move the selection to the currently hovered pixel."""
        if self._hud is None:
            return
        result = self._hud.canvas_to_sensor(event.x, event.y)
        if result is not None:
            self._selected = result
            # Force an immediate redraw — HUD_DRAW may not fire on still frames.
            self._draw_selection()

    def _on_right_click(self, event: tk.Event) -> None:
        """Clear the pinned selection and force an immediate redraw."""
        self._selected = None
        self._draw_selection()

    def _on_leave(self, event: tk.Event) -> None:
        """Hide hover when the mouse leaves the canvas."""
        if self._hovered is not None:
            self._hovered = None
            self._hover_dirty = True

    # ------------------------------------------------------------------
    # Hover tick loop  (Layer A — independent of the frame pipeline)
    # ------------------------------------------------------------------

    def _start_tick(self) -> None:
        """Kick off the after() loop if not already running."""
        if not self._tick_running and self._canvas is not None:
            self._tick_running = True
            self._canvas.after(_TICK_MS, self._tick)

    def _tick(self) -> None:
        """
        Lightweight periodic callback (~30 FPS).
        Redraws the hover border only when the cursor has moved to a new
        sensor pixel since the last tick (_hover_dirty flag).
        """
        canvas = self._canvas
        if canvas is None:
            self._tick_running = False
            return

        try:
            if not canvas.winfo_exists():
                self._tick_running = False
                return
        except tk.TclError:
            self._tick_running = False
            return

        # Redraw only when something changed — zero overhead otherwise.
        if self._hover_dirty:
            self._redraw_hover(canvas)
            self._hover_dirty = False

        # Re-schedule unconditionally while the plugin is alive.
        if self._tick_running:
            canvas.after(_TICK_MS, self._tick)

    def _redraw_hover(self, canvas: tk.Canvas) -> None:
        """
        Delete the old hover rectangle and draw a new one for the
        current hovered pixel.  This is a direct canvas call — no
        HUDEngine involved — to keep it as cheap as possible.
        """
        # ── Remove old hover item ─────────────────────────────────────
        if self._hover_item_id is not None:
            try:
                canvas.delete(self._hover_item_id)
            except tk.TclError:
                pass
            self._hover_item_id = None

        # ── Draw new hover item ───────────────────────────────────────
        hud = self._hud
        if self._hovered is None or hud is None:
            return
        if not hud._image_bbox or not hud._sensor_shape:
            return

        sx, sy = self._hovered
        x1_img, y1_img, _, _ = hud._image_bbox
        px  = x1_img + sx  * hud._scale_x
        py  = y1_img + sy  * hud._scale_y
        px2 = px + hud._scale_x
        py2 = py + hud._scale_y

        self._hover_item_id = canvas.create_rectangle(
            px, py, px2, py2,
            outline=HOVER_COLOR,
            fill="",
            width=HOVER_WIDTH,
        )
        # Always keep the hover rect on top of the image and other HUD items.
        canvas.tag_raise(self._hover_item_id)

    # ------------------------------------------------------------------
    # HUD_DRAW callback — Selection layer (Layer B)
    # ------------------------------------------------------------------

    def _on_hud_draw(self, hud_context: dict) -> None:
        """
        Called by the renderer after each frame is placed on the canvas.
        Manages canvas binding, HUDEngine init, and selection drawing.

        hud_context keys
        ----------------
        canvas      : tk.Canvas
        bbox        : (x1, y1, x2, y2) bounding box of the rendered image
        raw_payload : dict with '16bit' → np.ndarray[uint16]
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

        # ── Init HUDEngine for selection (Layer B) ────────────────────
        if self._hud is None or self._hud.canvas is not canvas:
            self._hud = HUDEngine(canvas)

        # ── Bind canvas + start tick on first valid frame ─────────────
        self._bind_canvas(canvas)
        self._start_tick()

        # ── Keep coordinate mapping current (image may have moved) ────
        self._hud.set_sensor_mapping(bbox, raw_16bit.shape)

        # ── Draw selection border + temperature label ─────────────────
        self._draw_selection()

        # ── After HUD items are drawn, raise hover on top ─────────────
        if self._hover_item_id is not None:
            try:
                canvas.tag_raise(self._hover_item_id)
            except tk.TclError:
                self._hover_item_id = None

    # ------------------------------------------------------------------
    # Selection drawing  (Layer B)
    # ------------------------------------------------------------------

    def _draw_selection(self) -> None:
        """Clear and redraw the selection border and temperature label."""
        hud = self._hud
        hud.clear()  # removes only items owned by this HUDEngine instance

        if self._selected is None:
            return

        sx, sy = self._selected

        # Border
        hud.draw_sensor_pixel_rect(sx, sy, color=SELECT_COLOR, width=SELECT_WIDTH)

        # Temperature label
        raw = self._raw_16bit
        if raw is not None:
            raw_val = int(raw[sy, sx])
            temp_c  = to_degrees_c(raw_val)
            hud.draw_sensor_smart_text(
                sx, sy,
                text=f"{temp_c:.1f} °C",
                color=LABEL_FG,
                font=LABEL_FONT,
                bg_color=LABEL_BG,
            )
