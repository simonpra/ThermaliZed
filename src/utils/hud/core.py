"""
HUDEngine — Tkinter HUD Drawing Engine (Core)
==============================================
Orchestrates the drawing library, coordinate mapper, and layer registry.

Architecture
------------
* **Layer Registry** — canvas items are stored by integer layer (multiples of
  100).  ``clear(layer=None)`` removes all layers or a single one.
  Standard layers:

  =========  ======================================================
  Layer 0    Background elements.
  Layer 100  Main HUD (default).  Temperature labels, crosshairs.
  Layer 200  Interaction / selection borders.
  Layer 300  Top-most overlays (always raised above everything else).
  =========  ======================================================

* **Memoisation** — ``_frame_registry`` deduplicates identical drawing calls
  within the same frame.  ``_rect_cache`` caches PIL images across frames so
  new PIL objects are only created when geometry or colour changes.

* **Coordinate Mapping** — delegated to a :class:`~src.utils.hud.mapper.CoordMapper`
  instance exposed as the public ``mapper`` attribute.

Performance note
----------------
The RAW_FRAME_PIPELINE runs at 25-30 FPS.  PIL image generation is memoised
by ``(w, h, radius, fill_rgba, outline_rgba)`` so a new PIL image is only
created when those parameters change, not every frame.
"""
from __future__ import annotations

import tkinter as tk
from typing import Callable, Dict, List, Optional, Tuple, Union

from src.utils.hud.mapper import CoordMapper
from src.utils.hud.library import primitives, composites, thermal

# Re-export RGBA for convenience
from src.utils.hud.library.primitives import RGBA


# ---------------------------------------------------------------------------
# Default layer constants
# ---------------------------------------------------------------------------

LAYER_BACKGROUND  = 0
LAYER_MAIN        = 100   # default drawing layer
LAYER_INTERACTION = 200
LAYER_TOP         = 300


class HUDEngine:
    """
    Drawing engine that wraps a ``tk.Canvas`` and provides high-level HUD
    primitives with automatic cleanup, smart edge clamping, alpha blending,
    and an ``update()`` hook for resize / post-draw repaints.

    Args:
        canvas: The Tkinter canvas to draw on.

    Attributes:
        canvas: The underlying ``tk.Canvas``.
        mapper: :class:`~src.utils.hud.mapper.CoordMapper` — sensor ↔ canvas
            coordinate transform.  Configure via :meth:`set_sensor_mapping`.
        image_cache: Per-frame ``PhotoImage`` reference dict.  Keeps PIL
            objects alive so Tkinter doesn't garbage-collect them.
    """

    def __init__(self, canvas: tk.Canvas) -> None:
        self.canvas: tk.Canvas = canvas

        # Coordinate mapper — no Tkinter dependency
        self.mapper: CoordMapper = CoordMapper()

        # Layer registry: layer_number → [canvas_item_id, ...]
        self._layers: Dict[int, List[int]] = {}

        # Deduplication registry for the *current* frame.
        # Key: tuple representing the drawing operation → List[item_id]
        self._frame_registry: Dict[tuple, List[int]] = {}

        # Persistent PIL/PhotoImage cache shared across frames.
        # Values must be kept alive so Tkinter doesn't drop them.
        self.image_cache: Dict[str, object] = {}

        # Rounded-rect PIL memoisation cache (cross-frame).
        # Key: (w, h, radius, fill_key, outline_key) → ImageTk.PhotoImage
        self._rect_cache: Dict[tuple, object] = {}

        # Callable stored by finalize() so update() can replay the last draw.
        self._draw_fn: Optional[Callable] = None

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------

    def clear(self, layer: Optional[int] = None) -> None:
        """
        Remove canvas items and release caches.

        Args:
            layer: If given, only items on that layer are removed.
                Pass ``None`` (default) to clear **all** layers.
        """
        if layer is None:
            # Clear every layer
            for items in self._layers.values():
                for item in items:
                    try:
                        self.canvas.delete(item)
                    except tk.TclError:
                        pass
            self._layers.clear()
            self._frame_registry.clear()
            self.image_cache.clear()
        else:
            items = self._layers.pop(layer, [])
            for item in items:
                try:
                    self.canvas.delete(item)
                except tk.TclError:
                    pass
            # Invalidate the full frame_registry so dedup tokens are not
            # stale for re-draws on cleared layers.
            self._frame_registry.clear()

    # ------------------------------------------------------------------
    # Sensor-to-Canvas Mapping  (delegates to self.mapper)
    # ------------------------------------------------------------------

    def set_sensor_mapping(
        self,
        image_bbox: Tuple[int, int, int, int],
        sensor_shape: Tuple[int, int],
    ) -> None:
        """
        Configure the coordinate mapping from raw sensor data to canvas.

        Args:
            image_bbox: ``(x1, y1, x2, y2)`` bounding box of the rendered
                image on the canvas.
            sensor_shape: ``(height, width)`` of the sensor data,
                e.g. ``(192, 256)``.
        """
        self.mapper.set_mapping(image_bbox, sensor_shape)

    def sensor_to_canvas(self, sx: float, sy: float) -> Tuple[float, float]:
        """Transform sensor → canvas.  See :meth:`CoordMapper.sensor_to_canvas`."""
        return self.mapper.sensor_to_canvas(sx, sy)

    def canvas_to_sensor(self, cx: float, cy: float) -> Optional[Tuple[int, int]]:
        """Transform canvas → sensor.  See :meth:`CoordMapper.canvas_to_sensor`."""
        return self.mapper.canvas_to_sensor(cx, cy)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _register_items(self, items: List[int], layer: int) -> None:
        """Add *items* to the layer registry."""
        if layer not in self._layers:
            self._layers[layer] = []
        self._layers[layer].extend(items)

    def _draw_cached(
        self,
        token: tuple,
        create_fn: Callable[[], Union[int, List[int]]],
        layer: int = LAYER_MAIN,
    ) -> List[int]:
        """
        Deduplicate drawing calls within the same frame.

        If *token* is already in the registry, the existing item IDs are
        returned immediately.  Otherwise *create_fn* is called, its result
        normalised to a list, registered, and returned.

        Args:
            token: A hashable tuple that uniquely identifies the drawing call.
            create_fn: Zero-argument callable that creates canvas items and
                returns a single ID or a list of IDs.
            layer: Layer number for the registry.

        Returns:
            List of canvas item IDs.
        """
        if token in self._frame_registry:
            return self._frame_registry[token]

        created = create_fn()
        if not isinstance(created, list):
            created = [created]

        self._register_items(created, layer)
        self._frame_registry[token] = created
        return created

    # ------------------------------------------------------------------
    # Primitives
    # ------------------------------------------------------------------

    def draw_text(
        self,
        x: int,
        y: int,
        text: str,
        color: str,
        anchor: str = "center",
        font: tuple = ("Helvetica", 10, "bold"),
        layer: int = LAYER_MAIN,
    ) -> int:
        """
        Draw text on the canvas.

        Args:
            x: Canvas x coordinate.
            y: Canvas y coordinate.
            text: String to display.
            color: Tkinter colour string.
            anchor: Tkinter anchor (e.g. ``"center"``, ``"sw"``).
            font: Tkinter font tuple.
            layer: Drawing layer (default: ``LAYER_MAIN = 100``).

        Returns:
            Canvas item ID.
        """
        token = ("text", x, y, text, color, anchor, font)

        def _create():
            return primitives.create_text(self.canvas, x, y, text, color, anchor, font)

        return self._draw_cached(token, _create, layer)[0]

    def draw_rounded_rect(
        self,
        x1: int,
        y1: int,
        x2: int,
        y2: int,
        radius: int,
        fill_rgba: Union[RGBA, str],
        outline_rgba: Optional[Union[RGBA, str]] = None,
        layer: int = LAYER_MAIN,
    ) -> int:
        """
        Draw a rounded rectangle with per-pixel alpha transparency.

        Requires Pillow.  Falls back to a plain Tkinter rectangle if
        Pillow is unavailable or dimensions are degenerate.

        Args:
            x1, y1, x2, y2: Bounding box in canvas pixels.
            radius: Corner radius in pixels.
            fill_rgba: Fill colour as ``(r, g, b, a)`` or colour string.
            outline_rgba: Outline colour or ``None`` for no outline.
            layer: Drawing layer.

        Returns:
            Canvas item ID.
        """
        def _key(c):
            return tuple(c) if isinstance(c, (list, tuple)) else str(c)

        token = ("rect", x1, y1, x2, y2, radius, _key(fill_rgba), _key(outline_rgba))

        def _create():
            return primitives.create_rounded_rect(
                self.canvas, x1, y1, x2, y2, radius,
                fill_rgba, outline_rgba, self._rect_cache, self.image_cache,
            )

        return self._draw_cached(token, _create, layer)[0]

    def draw_svg_icon(
        self,
        x: int,
        y: int,
        filepath: str,
        anchor: str = "center",
        layer: int = LAYER_MAIN,
    ) -> int:
        """
        Draw an SVG icon using Tkinter 9+ native SVG support.

        Args:
            x: Canvas x coordinate.
            y: Canvas y coordinate.
            filepath: Absolute path to the ``.svg`` file.
            anchor: Tkinter anchor.
            layer: Drawing layer.

        Returns:
            Canvas item ID, or ``-1`` on load failure.
        """
        token = ("svg", x, y, filepath, anchor)

        def _create():
            return primitives.create_svg_icon(
                self.canvas, x, y, filepath, anchor, self.image_cache
            )

        return self._draw_cached(token, _create, layer)[0]

    # ------------------------------------------------------------------
    # Composites
    # ------------------------------------------------------------------

    def draw_crosshair(
        self,
        cx: float,
        cy: float,
        color: str,
        gap: int = 3,
        arm: int = 12,
        width: int = 2,
        layer: int = LAYER_MAIN,
    ) -> List[int]:
        """
        Draw a four-arm crosshair centred on *(cx, cy)*.

        Args:
            cx: Centre x in canvas pixels.
            cy: Centre y in canvas pixels.
            color: Line colour string.
            gap: Gap between centre and arm start (pixels).
            arm: Arm length from gap outward (pixels).
            width: Stroke width (pixels).
            layer: Drawing layer.

        Returns:
            List of four canvas item IDs.
        """
        token = ("crosshair", cx, cy, color, gap, arm, width)

        def _create():
            return composites.create_crosshair(self.canvas, cx, cy, color, gap, arm, width)

        return self._draw_cached(token, _create, layer)

    def draw_text_rect(
        self,
        x: int,
        y: int,
        text: str,
        color: str,
        bg_color: Union[RGBA, str],
        anchor: str = "center",
        font: tuple = ("Helvetica", 10, "bold"),
        bg_padding: int = 4,
        radius: int = 5,
        outline_color: Optional[Union[RGBA, str]] = None,
        layer: int = LAYER_MAIN,
    ) -> List[int]:
        """
        Draw text with an automatically sized rounded rectangle background.

        Args:
            x, y: Anchor point in canvas pixels.
            text: String to display.
            color: Text colour string.
            bg_color: Background fill as ``(r, g, b, a)`` or colour string.
            anchor: Tkinter anchor for the text.
            font: Tkinter font tuple.
            bg_padding: Extra padding around the text on each side (pixels).
            radius: Background corner radius (pixels).
            outline_color: Outline colour for the background or ``None``
                to use *color*.
            layer: Drawing layer.

        Returns:
            ``[rect_id, text_id]``.
        """
        def _key(c):
            return tuple(c) if isinstance(c, (list, tuple)) else str(c)

        token = ("text_rect", x, y, text, color, _key(bg_color), anchor,
                 font, bg_padding, radius, _key(outline_color))

        if token in self._frame_registry:
            return self._frame_registry[token]

        items = composites.create_text_rect(
            self.canvas, x, y, text, color, bg_color, anchor, font,
            bg_padding, radius, outline_color,
            self._rect_cache, self.image_cache,
        )
        self._register_items(items, layer)
        self._frame_registry[token] = items
        return items

    def draw_smart_text(
        self,
        x: int,
        y: int,
        text: str,
        color: str,
        offset: int = 15,
        font: tuple = ("Helvetica", 10, "bold"),
        bg_color: Optional[Union[RGBA, str]] = None,
        bg_padding: int = 4,
        layer: int = LAYER_MAIN,
    ) -> List[int]:
        """
        Draw text at *(x, y)* with automatic edge clamping.

        The label is placed so it never bleeds off the canvas edge — the
        anchor and offset direction are chosen based on proximity to the
        right and top edges.

        Args:
            x, y: Reference point (typically a crosshair centre).
            text: String to display.
            color: Text colour string.
            offset: Distance from *(x, y)* to the text anchor (pixels).
            font: Tkinter font tuple.
            bg_color: Background fill or ``None`` for plain text.
            bg_padding: Background padding (pixels).
            layer: Drawing layer.

        Returns:
            List of canvas item IDs.
        """
        cw = self.canvas.winfo_width()
        ch = self.canvas.winfo_height()

        def _key(c):
            return tuple(c) if isinstance(c, (list, tuple)) else str(c)

        token = ("smart_text", x, y, text, color, offset, font,
                 _key(bg_color), bg_padding, cw, ch)

        if token in self._frame_registry:
            return self._frame_registry[token]

        items = composites.create_smart_text(
            self.canvas, x, y, text, color, cw, ch,
            offset, font, bg_color, bg_padding,
            self._rect_cache, self.image_cache,
        )
        self._register_items(items, layer)
        self._frame_registry[token] = items
        return items

    # ------------------------------------------------------------------
    # Sensor-Mapped Composites
    # ------------------------------------------------------------------

    def draw_sensor_pixel_rect(
        self,
        sx: int,
        sy: int,
        color: str = "white",
        width: int = 2,
        layer: int = LAYER_MAIN,
    ) -> int:
        """
        Draw a border around the canvas area occupied by sensor pixel *(sx, sy)*.

        Args:
            sx: Sensor column index.
            sy: Sensor row index.
            color: Outline colour string.
            width: Stroke width (pixels).
            layer: Drawing layer.

        Returns:
            Canvas item ID, or ``-1`` if the mapper is not configured.
        """
        if not self.mapper.image_bbox or not self.mapper.sensor_shape:
            return -1

        token = ("sensor_pixel_rect", sx, sy, color, width,
                 self.mapper.scale_x, self.mapper.scale_y,
                 self.mapper.image_bbox[0], self.mapper.image_bbox[1])

        def _create():
            return thermal.create_sensor_pixel_rect(
                self.canvas, self.mapper, sx, sy, color, width
            )

        return self._draw_cached(token, _create, layer)[0]

    def draw_sensor_crosshair(
        self,
        sx: float,
        sy: float,
        color: str,
        gap: int = 3,
        arm: int = 12,
        width: int = 2,
        layer: int = LAYER_MAIN,
    ) -> List[int]:
        """
        Draw a crosshair at sensor coordinates *(sx, sy)*.

        Args:
            sx: Sensor column index.
            sy: Sensor row index.
            color: Line colour string.
            gap: Gap from centre (pixels).
            arm: Arm length (pixels).
            width: Stroke width (pixels).
            layer: Drawing layer.

        Returns:
            List of four canvas item IDs.
        """
        cx, cy = self.mapper.sensor_to_canvas(sx, sy)
        return self.draw_crosshair(cx, cy, color, gap, arm, width, layer)

    def draw_sensor_smart_text(
        self,
        sx: float,
        sy: float,
        text: str,
        color: str,
        offset: int = 15,
        font: tuple = ("Helvetica", 10, "bold"),
        bg_color: Optional[Union[RGBA, str]] = None,
        bg_padding: int = 4,
        layer: int = LAYER_MAIN,
    ) -> List[int]:
        """
        Draw edge-clamped text anchored at sensor coordinates *(sx, sy)*.

        Args:
            sx: Sensor column index.
            sy: Sensor row index.
            text: String to display.
            color: Text colour string.
            offset: Label offset from the anchor point (pixels).
            font: Tkinter font tuple.
            bg_color: Background fill or ``None``.
            bg_padding: Background padding (pixels).
            layer: Drawing layer.

        Returns:
            List of canvas item IDs.
        """
        cx, cy = self.mapper.sensor_to_canvas(sx, sy)
        return self.draw_smart_text(cx, cy, text, color, offset, font,
                                    bg_color, bg_padding, layer)

    # ------------------------------------------------------------------
    # Resize / update hook
    # ------------------------------------------------------------------

    def finalize(self, draw_fn: Optional[Callable] = None) -> None:
        """
        Register the draw function to be replayed by :meth:`update`.

        Args:
            draw_fn: Zero-argument callable to invoke on :meth:`update`.
        """
        self._draw_fn = draw_fn

    def update(self) -> None:
        """Trigger a full redraw by replaying the registered draw function."""
        if self._draw_fn is not None:
            try:
                self._draw_fn()
            except Exception as exc:
                print(f"[HUDEngine] update() draw_fn raised: {exc}")

    # ------------------------------------------------------------------
    # Context-manager support (optional convenience)
    # ------------------------------------------------------------------

    def __enter__(self) -> "HUDEngine":
        self.clear()
        return self

    def __exit__(self, *_) -> None:
        pass

    # ------------------------------------------------------------------
    # Legacy property shims (for internal tooling / debugging)
    # ------------------------------------------------------------------

    @property
    def drawn_items(self) -> List[int]:
        """Flat list of all canvas item IDs across all layers."""
        return [item for items in self._layers.values() for item in items]
