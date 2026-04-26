"""
HUDEngine — Tkinter HUD Drawing Engine
=======================================
A reusable helper for drawing modern, high-definition overlay elements on a
tk.Canvas without the usual Tkinter headaches:

  * Alpha transparency & rounded rectangles via Pillow (PIL).
  * Smart boundary detection so labels never bleed off the canvas edge.
  * SVG support via Tkinter 9+ native PhotoImage with built-in caching.
  * Automated cleanup: tracks every drawn canvas ID for one-shot removal.
  * update() hook: re-fires the last draw call after a resize or idle repaint.
  * Memoisation: Deduplicates identical drawing commands within the same frame.

Performance note
----------------
The RAW_FRAME_PIPELINE runs at 25-30 FPS.  PIL image generation is memoised
by (w, h, fill_rgba, outline_rgba, radius) so a new PIL image is only created
when those parameters change, not every frame. Within a single frame, identical
drawing calls return the same canvas items.
"""

from __future__ import annotations

import tkinter as tk
from typing import Callable, List, Optional, Tuple, Union

try:
    from PIL import Image, ImageDraw, ImageTk
    _PIL_AVAILABLE = True
except ImportError:
    _PIL_AVAILABLE = False


# ---------------------------------------------------------------------------
# Type aliases
# ---------------------------------------------------------------------------
RGBA = Tuple[int, int, int, int]   # (r, g, b, a)


class HUDEngine:
    """
    Drawing engine that wraps a ``tk.Canvas`` and provides high-level HUD
    primitives with automatic cleanup, smart edge clamping, alpha blending,
    and an ``update()`` hook for resize / post-draw repaints.
    """

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------

    def __init__(self, canvas: tk.Canvas) -> None:
        self.canvas: tk.Canvas = canvas

        # All canvas item IDs created in the *current* frame.
        self.drawn_items: List[int] = []

        # Deduplication registry for the *current* frame.
        # Key: A tuple representing the drawing operation
        # Value: The canvas item ID(s)
        self._frame_registry: dict = {}

        # Persistent PIL/PhotoImage cache shared across frames.
        # Keys are arbitrary strings; values are ImageTk.PhotoImage objects.
        # CRITICAL: Tkinter drops images that lose their last Python reference.
        self.image_cache: dict = {}

        # Rounded-rect PIL memoisation cache.
        # Key: (w, h, radius, fill_rgba, outline_rgba) → ImageTk.PhotoImage
        self._rect_cache: dict = {}

        # Callable stored by finalize() so update() can replay the last draw.
        self._draw_fn: Optional[Callable] = None

        # --- Sensor-to-Canvas Mapping State ---
        self._image_bbox: Optional[Tuple[int, int, int, int]] = None
        self._sensor_shape: Optional[Tuple[int, int]] = None
        self._scale_x: float = 1.0
        self._scale_y: float = 1.0

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------

    def clear(self) -> None:
        """
        Remove all canvas items created in the previous frame and release the
        image cache so PIL objects are garbage-collected.
        """
        for item in self.drawn_items:
            try:
                self.canvas.delete(item)
            except tk.TclError:
                pass  # canvas may have been destroyed
        self.drawn_items.clear()
        self._frame_registry.clear()
        self.image_cache.clear()

    # ------------------------------------------------------------------
    # Sensor-to-Canvas Mapping
    # ------------------------------------------------------------------

    def set_sensor_mapping(self, image_bbox: Tuple[int, int, int, int], sensor_shape: Tuple[int, int]) -> None:
        """
        Configure the coordinate mapping from the raw sensor data to the displayed canvas image.
        
        Args:
            image_bbox: (x1, y1, x2, y2) bounding box of the rendered image on the Tkinter canvas.
            sensor_shape: (height, width) of the original unscaled sensor data (e.g. 192, 256).
        """
        self._image_bbox = image_bbox
        self._sensor_shape = sensor_shape
        
        if image_bbox and sensor_shape:
            x1, y1, x2, y2 = image_bbox
            img_w = x2 - x1
            img_h = y2 - y1
            raw_h, raw_w = sensor_shape
            
            self._scale_x = img_w / max(raw_w, 1)
            self._scale_y = img_h / max(raw_h, 1)
        else:
            self._scale_x = 1.0
            self._scale_y = 1.0

    def sensor_to_canvas(self, sx: float, sy: float) -> Tuple[float, float]:
        """
        Transform a coordinate from sensor space to canvas space.
        Adds 0.5 to align to the centre of the sensor pixel.
        """
        if not self._image_bbox:
            return sx, sy
            
        x1, y1, _, _ = self._image_bbox
        cx = x1 + (sx + 0.5) * self._scale_x
        cy = y1 + (sy + 0.5) * self._scale_y
        return cx, cy

    def canvas_to_sensor(self, cx: float, cy: float) -> Optional[Tuple[int, int]]:
        """
        Transform a canvas coordinate (e.g. from a mouse event) back to the
        integer sensor pixel index ``(col, row)``.

        Returns ``None`` when the canvas point lies outside the rendered
        image area, or when the sensor mapping has not been configured yet.
        """
        if not self._image_bbox or not self._sensor_shape:
            return None

        x1, y1, x2, y2 = self._image_bbox
        if not (x1 <= cx < x2 and y1 <= cy < y2):
            return None  # outside the image

        raw_h, raw_w = self._sensor_shape
        sx = int((cx - x1) / self._scale_x)
        sy = int((cy - y1) / self._scale_y)
        # Clamp to valid sensor indices
        sx = max(0, min(sx, raw_w - 1))
        sy = max(0, min(sy, raw_h - 1))
        return sx, sy

    # ------------------------------------------------------------------
    # Internal Helpers
    # ------------------------------------------------------------------

    def _draw_cached(self, token: tuple, create_fn: Callable) -> List[int]:
        """
        Deduplicate drawing calls within the same frame.
        If the token exists in the registry, return the existing IDs.
        Otherwise, call create_fn() to create them, add to drawn_items & registry.
        """
        if token in self._frame_registry:
            return self._frame_registry[token]
        
        created = create_fn()
        if not isinstance(created, list):
            created = [created]
            
        self.drawn_items.extend(created)
        self._frame_registry[token] = created
        return created

    # ------------------------------------------------------------------
    # Core Primitive Geometries
    # ------------------------------------------------------------------

    def draw_text(
        self,
        x: int,
        y: int,
        text: str,
        color: str,
        anchor: str = "center",
        font: tuple = ("Helvetica", 10, "bold")
    ) -> int:
        """
        Primitive: Draw text on the canvas.
        """
        token = ("text", x, y, text, color, anchor, font)
        
        def _create():
            return self.canvas.create_text(
                x, y,
                text=text,
                fill=color,
                anchor=anchor,
                font=font,
            )
            
        return self._draw_cached(token, _create)[0]

    def draw_rounded_rect(
        self,
        x1: int,
        y1: int,
        x2: int,
        y2: int,
        radius: int,
        fill_rgba: Union[RGBA, str],
        outline_rgba: Optional[Union[RGBA, str]] = None,
    ) -> int:
        """
        Primitive: Draw a rounded rectangle with per-pixel alpha transparency.
        Requires Pillow. Falls back to tk rectangle if unavailable.
        """
        # Normalise strings vs tuples for hashing
        def _key(c): return tuple(c) if isinstance(c, (list, tuple)) else str(c)
        token = ("rect", x1, y1, x2, y2, radius, _key(fill_rgba), _key(outline_rgba))

        def _create():
            w = x2 - x1
            h = y2 - y1

            if not _PIL_AVAILABLE or w <= 0 or h <= 0:
                # Graceful fallback — plain Tkinter rectangle, no alpha
                if isinstance(fill_rgba, (tuple, list)):
                    fill_hex = "#{:02x}{:02x}{:02x}".format(
                        int(fill_rgba[0]), int(fill_rgba[1]), int(fill_rgba[2])
                    )
                else:
                    fill_hex = str(fill_rgba)
                return self.canvas.create_rectangle(
                    x1, y1, x2, y2, fill=fill_hex, outline=""
                )

            # Memoisation key for PIL image cross-frame
            cache_key = (w, h, radius, _key(fill_rgba), _key(outline_rgba))
            photo = self._rect_cache.get(cache_key)

            if photo is None:
                img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
                draw_ctx = ImageDraw.Draw(img)
                draw_ctx.rounded_rectangle(
                    [(0, 0), (w - 1, h - 1)],
                    radius=radius,
                    fill=fill_rgba,
                    outline=outline_rgba,
                )
                photo = ImageTk.PhotoImage(img)
                self._rect_cache[cache_key] = photo

            # Keep PhotoImage alive for this frame via image_cache
            self.image_cache[f"rect_{x1}_{y1}_{w}_{h}_{id(photo)}"] = photo

            return self.canvas.create_image(x1, y1, image=photo, anchor="nw")

        return self._draw_cached(token, _create)[0]

    def draw_svg_icon(
        self,
        x: int,
        y: int,
        filepath: str,
        anchor: str = "center",
    ) -> int:
        """
        Primitive: Draw an SVG icon using Tkinter 9+ native SVG support.
        """
        token = ("svg", x, y, filepath, anchor)

        def _create():
            photo = self.image_cache.get(filepath)
            if photo is None:
                try:
                    photo = tk.PhotoImage(file=filepath)
                    self.image_cache[filepath] = photo
                except tk.TclError as exc:
                    print(f"[HUDEngine] SVG load failed for {filepath!r}: {exc}")
                    return -1
            return self.canvas.create_image(x, y, image=photo, anchor=anchor)

        res = self._draw_cached(token, _create)[0]
        # Since _create might return -1 on error, we handle it but it still goes into drawn_items
        return res

    # ------------------------------------------------------------------
    # Composite Geometries
    # ------------------------------------------------------------------

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
        outline_color: Optional[Union[RGBA, str]] = None
    ) -> List[int]:
        """
        Composite: Draw text with an automatically sized rounded rectangle background.
        """
        # We can use a composite token to avoid redrawing both elements entirely
        token = ("text_rect", x, y, text, color, bg_color, anchor, font, bg_padding, radius, outline_color)
        
        def _create():
            # First, draw the text to get its bounding box
            text_id = self.draw_text(x, y, text, color, anchor, font)
            
            created = [text_id]
            bbox = self.canvas.bbox(text_id)
            if bbox:
                bx1, by1, bx2, by2 = bbox
                
                # Convert string colors to RGBA for PIL if needed
                fill_rgba = bg_color
                if isinstance(fill_rgba, str):
                    _str_to_rgba = {
                        "black": (0, 0, 0, 180),
                        "white": (255, 255, 255, 180),
                    }
                    fill_rgba = _str_to_rgba.get(fill_rgba, (0, 0, 0, 180))
                    
                outline_rgba = outline_color
                if outline_rgba is None and color:
                    outline_rgba = color # Default outline to text color
                    
                rect_id = self.draw_rounded_rect(
                    bx1 - bg_padding,
                    by1 - bg_padding,
                    bx2 + bg_padding,
                    by2 + bg_padding,
                    radius=radius,
                    fill_rgba=fill_rgba,
                    outline_rgba=outline_rgba,
                )
                
                # Ensure the rectangle is behind the text
                self.canvas.tag_lower(rect_id, text_id)
                # Note: drawn_items was already populated by draw_text and draw_rounded_rect
                # We return an empty list here to avoid the _draw_cached appending them AGAIN
                # But we actually bypass _draw_cached for composites if we want to avoid double-appending.
                # Since we use draw_text and draw_rounded_rect (which manage drawn_items), 
                # we don't need _draw_cached for the composite itself!
                return [] 
            return []
            
        if token in self._frame_registry:
            # For composites, just return the list of component IDs if we already did it
            return self._frame_registry[token]
            
        # Draw the components (they manage their own drawn_items arrays via primitives)
        text_id = self.draw_text(x, y, text, color, anchor, font)
        bbox = self.canvas.bbox(text_id)
        
        items = [text_id]
        if bbox:
            bx1, by1, bx2, by2 = bbox
            fill_rgba = bg_color
            if isinstance(fill_rgba, str):
                _str_to_rgba = {
                    "black": (0, 0, 0, 180),
                    "white": (255, 255, 255, 180),
                }
                fill_rgba = _str_to_rgba.get(fill_rgba, (0, 0, 0, 180))
                
            outline_rgba = outline_color
            if outline_rgba is None and color:
                outline_rgba = color
                
            rect_id = self.draw_rounded_rect(
                bx1 - bg_padding,
                by1 - bg_padding,
                bx2 + bg_padding,
                by2 + bg_padding,
                radius=radius,
                fill_rgba=fill_rgba,
                outline_rgba=outline_rgba,
            )
            self.canvas.tag_lower(rect_id, text_id)
            items.insert(0, rect_id)
            
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
        bg_color=None,
        bg_padding: int = 4,
    ) -> List[int]:
        """
        Composite: Draw *text* at canvas position *(x, y)* with automatic edge clamping.
        """
        # Because the logic depends on canvas.winfo_width/height, the token must include them
        cw = self.canvas.winfo_width()
        ch = self.canvas.winfo_height()
        token = ("smart_text", x, y, text, color, offset, font, bg_color, bg_padding, cw, ch)

        if token in self._frame_registry:
            return self._frame_registry[token]

        # Determine horizontal anchor & offset direction
        edge_threshold_x = cw * 0.75
        if x > edge_threshold_x:
            anchor_h = "e"
            tx = x - offset
        else:
            anchor_h = "w"
            tx = x + offset

        # Determine vertical anchor & offset direction
        edge_threshold_y = ch * 0.20
        if y < edge_threshold_y:
            anchor_v = "n"
            ty = y + offset
        else:
            anchor_v = "s"
            ty = y - offset

        anchor = anchor_v + anchor_h  # e.g. "sw", "ne"

        if bg_color is not None:
            items = self.draw_text_rect(tx, ty, text, color, bg_color, anchor, font, bg_padding)
        else:
            text_id = self.draw_text(tx, ty, text, color, anchor, font)
            items = [text_id]
            
        self._frame_registry[token] = items
        return items

    def draw_crosshair(
        self,
        cx: float,
        cy: float,
        color: str,
        gap: int = 3,
        arm: int = 12,
        width: int = 2,
    ) -> List[int]:
        """
        Composite: Draw a four-arm crosshair centred on *(cx, cy)*.
        """
        token = ("crosshair", cx, cy, color, gap, arm, width)

        def _create():
            return [
                self.canvas.create_line(cx - arm, cy, cx - gap, cy, fill=color, width=width),
                self.canvas.create_line(cx + gap, cy, cx + arm, cy, fill=color, width=width),
                self.canvas.create_line(cx, cy - arm, cx, cy - gap, fill=color, width=width),
                self.canvas.create_line(cx, cy + gap, cx, cy + arm, fill=color, width=width),
            ]

        return self._draw_cached(token, _create)

    # ------------------------------------------------------------------
    # Sensor-Mapped Composites
    # ------------------------------------------------------------------

    def draw_sensor_pixel_rect(
        self,
        sx: int,
        sy: int,
        color: str = "white",
        width: int = 2,
    ) -> int:
        """
        Draw a rectangle border that exactly covers the canvas area occupied by
        the sensor pixel at column *sx*, row *sy*.

        The rectangle is aligned to the pixel grid of the rendered image, so it
        snaps perfectly regardless of the zoom / scale factor.
        """
        if not self._image_bbox or not self._sensor_shape:
            return -1

        x1_img, y1_img, _, _ = self._image_bbox
        # Top-left canvas corner of the sensor pixel
        px = x1_img + sx * self._scale_x
        py = y1_img + sy * self._scale_y
        # Bottom-right canvas corner
        px2 = px + self._scale_x
        py2 = py + self._scale_y

        token = ("sensor_pixel_rect", sx, sy, color, width,
                 self._scale_x, self._scale_y, x1_img, y1_img)

        def _create():
            return self.canvas.create_rectangle(
                px, py, px2, py2,
                outline=color,
                fill="",          # transparent fill
                width=width,
            )

        return self._draw_cached(token, _create)[0]

    def draw_sensor_crosshair(
        self,
        sx: float,
        sy: float,
        color: str,
        gap: int = 3,
        arm: int = 12,
        width: int = 2,
    ) -> List[int]:
        """
        Draw a crosshair using sensor coordinates. The crosshair visual size
        (gap, arm, width) remains constant regardless of sensor zoom level.
        """
        cx, cy = self.sensor_to_canvas(sx, sy)
        return self.draw_crosshair(cx, cy, color, gap, arm, width)

    def draw_sensor_smart_text(
        self,
        sx: float,
        sy: float,
        text: str,
        color: str,
        offset: int = 15,
        font: tuple = ("Helvetica", 10, "bold"),
        bg_color=None,
        bg_padding: int = 4,
    ) -> List[int]:
        """
        Draw smart text using sensor coordinates. The font size and padding
        remain constant regardless of sensor zoom level.
        """
        cx, cy = self.sensor_to_canvas(sx, sy)
        return self.draw_smart_text(cx, cy, text, color, offset, font, bg_color, bg_padding)

    # ------------------------------------------------------------------
    # Update / resize hook
    # ------------------------------------------------------------------

    def finalize(self, draw_fn: Optional[Callable] = None) -> None:
        """
        Call at the end of a draw pass to register the draw function that
        should be re-invoked by ``update()``.
        """
        self._draw_fn = draw_fn

    def update(self) -> None:
        """
        Trigger a full redraw.
        """
        if self._draw_fn is not None:
            try:
                self._draw_fn()
            except Exception as exc:  # pragma: no cover
                print(f"[HUDEngine] update() draw_fn raised: {exc}")

    # ------------------------------------------------------------------
    # Context-manager support (optional convenience)
    # ------------------------------------------------------------------

    def __enter__(self) -> "HUDEngine":
        self.clear()
        return self

    def __exit__(self, *_) -> None:
        pass
