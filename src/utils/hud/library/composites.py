"""
Drawing Composites
==================
Higher-level UI elements built from multiple primitives.  Like the
primitives module, these are stateless creator functions — no
deduplication or lifecycle tracking.
"""
from __future__ import annotations

import tkinter as tk
from typing import Dict, List, Optional, Union

from src.utils.hud.library.primitives import (
    RGBA,
    _to_rgba,
    create_text,
    create_rounded_rect,
)


def create_crosshair(
    canvas: tk.Canvas,
    cx: float,
    cy: float,
    color: str,
    gap: int = 3,
    arm: int = 12,
    width: int = 2,
) -> List[int]:
    """
    Create a four-arm crosshair centred on *(cx, cy)*.

    Args:
        canvas: Target Tkinter canvas.
        cx: Centre x in canvas pixels.
        cy: Centre y in canvas pixels.
        color: Line colour string.
        gap: Distance from centre to the start of each arm (pixels).
        arm: Length of each arm from the gap outward (pixels).
        width: Line stroke width (pixels).

    Returns:
        List of four canvas item IDs (one per arm).
    """
    return [
        canvas.create_line(cx - arm, cy, cx - gap, cy, fill=color, width=width),
        canvas.create_line(cx + gap, cy, cx + arm, cy, fill=color, width=width),
        canvas.create_line(cx, cy - arm, cx, cy - gap, fill=color, width=width),
        canvas.create_line(cx, cy + gap, cx, cy + arm, fill=color, width=width),
    ]


def create_text_rect(
    canvas: tk.Canvas,
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
    rect_cache: Optional[Dict] = None,
    image_cache: Optional[Dict] = None,
) -> List[int]:
    """
    Create text with an automatically sized rounded rectangle background.

    The background rectangle is sized to fit the text bounding box plus
    *bg_padding* on every side and is z-ordered below the text.

    Args:
        canvas: Target Tkinter canvas.
        x, y: Anchor point in canvas pixels.
        text: The string to display.
        color: Text colour string.
        bg_color: Background fill as ``(r, g, b, a)`` or colour string.
        anchor: Tkinter anchor for the text item.
        font: Tkinter font tuple.
        bg_padding: Extra space (pixels) around the text on each side.
        radius: Background rounded-corner radius (pixels).
        outline_color: Outline colour for the background rect, or ``None``
            to use *color* as the outline.
        rect_cache: Cross-frame PIL cache dict (passed through to primitive).
        image_cache: Per-frame PhotoImage reference cache.

    Returns:
        ``[rect_id, text_id]`` — rect first so callers can easily z-lower it.
    """
    rc = rect_cache if rect_cache is not None else {}
    ic = image_cache if image_cache is not None else {}

    text_id = create_text(canvas, x, y, text, color, anchor, font)
    items   = [text_id]

    bbox = canvas.bbox(text_id)
    if bbox:
        bx1, by1, bx2, by2 = bbox
        fill_rgba    = bg_color if isinstance(bg_color, (list, tuple)) else _to_rgba(bg_color)
        out_rgba     = outline_color if outline_color is not None else color

        rect_id = create_rounded_rect(
            canvas,
            bx1 - bg_padding, by1 - bg_padding,
            bx2 + bg_padding, by2 + bg_padding,
            radius, fill_rgba, out_rgba, rc, ic,
        )
        canvas.tag_lower(rect_id, text_id)
        items.insert(0, rect_id)

    return items


def create_smart_text(
    canvas: tk.Canvas,
    x: int,
    y: int,
    text: str,
    color: str,
    canvas_w: int,
    canvas_h: int,
    offset: int = 15,
    font: tuple = ("Helvetica", 10, "bold"),
    bg_color: Optional[Union[RGBA, str]] = None,
    bg_padding: int = 4,
    rect_cache: Optional[Dict] = None,
    image_cache: Optional[Dict] = None,
) -> List[int]:
    """
    Create text at *(x, y)* with automatic edge clamping.

    The label is positioned so it never bleeds off the canvas edge —
    the anchor and offset direction are chosen based on proximity to the
    right edge and the top edge.

    Args:
        canvas: Target Tkinter canvas.
        x, y: Reference point (typically a crosshair centre).
        text: The string to display.
        color: Text colour string.
        canvas_w: Current canvas width (pixels) — used for clamping logic.
        canvas_h: Current canvas height (pixels) — used for clamping logic.
        offset: Distance (pixels) from *(x, y)* to the text anchor.
        font: Tkinter font tuple.
        bg_color: Background fill, or ``None`` for plain text.
        bg_padding: Background padding in pixels.
        rect_cache: Cross-frame PIL cache dict.
        image_cache: Per-frame PhotoImage reference cache.

    Returns:
        List of canvas item IDs.
    """
    # Horizontal anchor + offset
    if x > canvas_w * 0.75:
        anchor_h, tx = "e", x - offset
    else:
        anchor_h, tx = "w", x + offset

    # Vertical anchor + offset
    if y < canvas_h * 0.20:
        anchor_v, ty = "n", y + offset
    else:
        anchor_v, ty = "s", y - offset

    anchor = anchor_v + anchor_h  # e.g. "sw", "ne"

    if bg_color is not None:
        return create_text_rect(
            canvas, tx, ty, text, color, bg_color, anchor, font,
            bg_padding, rect_cache=rect_cache, image_cache=image_cache,
        )
    return [create_text(canvas, tx, ty, text, color, anchor, font)]
