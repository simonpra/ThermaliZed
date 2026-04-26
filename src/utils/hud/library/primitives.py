"""
Drawing Primitives
==================
Low-level canvas creation functions.  Each function creates one or more
canvas items and returns the item ID(s).  They do **not** perform
deduplication or lifecycle tracking — that is the responsibility of
:class:`~src.utils.hud.core.HUDEngine`.

Functions accept explicit ``rect_cache`` / ``image_cache`` dicts so they
remain stateless and can be driven by the engine without coupling.
"""
from __future__ import annotations

import tkinter as tk
from typing import Dict, Optional, Tuple, Union

try:
    from PIL import Image, ImageDraw, ImageTk
    _PIL_AVAILABLE = True
except ImportError:
    _PIL_AVAILABLE = False

# Type alias
RGBA = Tuple[int, int, int, int]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _rgba_key(color: Union[RGBA, str]) -> Union[tuple, str]:
    """Hashable representation of a color for cache keys."""
    return tuple(color) if isinstance(color, (list, tuple)) else str(color)


def _to_rgba(color: Union[RGBA, str]) -> RGBA:
    """
    Coerce a color value to an RGBA tuple.

    String shortcuts: ``"black"`` → ``(0,0,0,180)``,
    ``"white"`` → ``(255,255,255,180)``.  Unknown strings fall back to
    opaque black.

    Args:
        color: An ``(r, g, b, a)`` tuple or a colour string.

    Returns:
        An ``(r, g, b, a)`` tuple.
    """
    if isinstance(color, (list, tuple)) and len(color) >= 4:
        return tuple(int(c) for c in color[:4])  # type: ignore[return-value]
    _map = {
        "black":  (0,   0,   0,   180),
        "white":  (255, 255, 255, 180),
    }
    return _map.get(str(color), (0, 0, 0, 180))  # type: ignore[return-value]


# ---------------------------------------------------------------------------
# Primitive creators
# ---------------------------------------------------------------------------

def create_text(
    canvas: tk.Canvas,
    x: int,
    y: int,
    text: str,
    color: str,
    anchor: str = "center",
    font: tuple = ("Helvetica", 10, "bold"),
) -> int:
    """
    Create a text item on *canvas*.

    Args:
        canvas: Target Tkinter canvas.
        x: Canvas x coordinate.
        y: Canvas y coordinate.
        text: The string to display.
        color: Text fill colour (Tkinter colour string).
        anchor: Tkinter anchor (e.g. ``"center"``, ``"sw"``).
        font: Tkinter font tuple.

    Returns:
        Canvas item ID.
    """
    return canvas.create_text(x, y, text=text, fill=color, anchor=anchor, font=font)


def create_rounded_rect(
    canvas: tk.Canvas,
    x1: int,
    y1: int,
    x2: int,
    y2: int,
    radius: int,
    fill_rgba: Union[RGBA, str],
    outline_rgba: Optional[Union[RGBA, str]],
    rect_cache: Dict,
    image_cache: Dict,
) -> int:
    """
    Create a rounded rectangle with per-pixel alpha via Pillow.

    Falls back to a plain Tkinter rectangle when Pillow is unavailable or
    the dimensions are degenerate.

    Args:
        canvas: Target Tkinter canvas.
        x1, y1, x2, y2: Bounding box in canvas pixels.
        radius: Corner radius in pixels.
        fill_rgba: Fill colour as ``(r, g, b, a)`` or colour string.
        outline_rgba: Outline colour or ``None`` for no outline.
        rect_cache: Cross-frame PIL image cache (mutated in place).
        image_cache: Per-frame PhotoImage reference cache (mutated in place).

    Returns:
        Canvas item ID.
    """
    w, h = x2 - x1, y2 - y1

    if not _PIL_AVAILABLE or w <= 0 or h <= 0:
        # Graceful fallback — plain rectangle, no alpha
        fill_hex = (
            "#{:02x}{:02x}{:02x}".format(*fill_rgba[:3])
            if isinstance(fill_rgba, (list, tuple))
            else str(fill_rgba)
        )
        return canvas.create_rectangle(x1, y1, x2, y2, fill=fill_hex, outline="")

    fill_key    = _rgba_key(fill_rgba)
    outline_key = _rgba_key(outline_rgba) if outline_rgba is not None else None
    cache_key   = (w, h, radius, fill_key, outline_key)
    photo = rect_cache.get(cache_key)

    if photo is None:
        img      = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        draw_ctx = ImageDraw.Draw(img)
        draw_ctx.rounded_rectangle(
            [(0, 0), (w - 1, h - 1)],
            radius=radius,
            fill=_to_rgba(fill_rgba) if isinstance(fill_rgba, str) else fill_rgba,
            outline=(_to_rgba(outline_rgba) if isinstance(outline_rgba, str) else outline_rgba)
            if outline_rgba is not None else None,
        )
        photo = ImageTk.PhotoImage(img)
        rect_cache[cache_key] = photo

    # Keep PhotoImage alive for this frame
    image_cache[f"rect_{x1}_{y1}_{w}_{h}_{id(photo)}"] = photo
    return canvas.create_image(x1, y1, image=photo, anchor="nw")


def create_svg_icon(
    canvas: tk.Canvas,
    x: int,
    y: int,
    filepath: str,
    anchor: str = "center",
    image_cache: Optional[Dict] = None,
) -> int:
    """
    Create an SVG icon using Tkinter 9+ native SVG support.

    Args:
        canvas: Target Tkinter canvas.
        x: Canvas x coordinate.
        y: Canvas y coordinate.
        filepath: Absolute path to the ``.svg`` file.
        anchor: Tkinter anchor.
        image_cache: Optional shared cache dict to avoid reloading.

    Returns:
        Canvas item ID, or ``-1`` on load failure.
    """
    cache = image_cache if image_cache is not None else {}
    photo = cache.get(filepath)
    if photo is None:
        try:
            photo = tk.PhotoImage(file=filepath)
            cache[filepath] = photo
        except tk.TclError as exc:
            print(f"[HUD/primitives] SVG load failed for {filepath!r}: {exc}")
            return -1
    return canvas.create_image(x, y, image=photo, anchor=anchor)
