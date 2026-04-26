"""
Thermal Drawing Elements
========================
Specialised composites that work in **sensor pixel space** rather than
canvas space.  They require a :class:`~src.utils.hud.mapper.CoordMapper`
instance for coordinate translation.
"""
from __future__ import annotations

import tkinter as tk
from typing import Dict, List, Optional, Union

from src.utils.hud.mapper import CoordMapper
from src.utils.hud.library.primitives import RGBA
from src.utils.hud.library.composites import (
    create_crosshair,
    create_smart_text,
)


def create_sensor_pixel_rect(
    canvas: tk.Canvas,
    mapper: CoordMapper,
    sx: int,
    sy: int,
    color: str = "white",
    width: int = 2,
) -> int:
    """
    Create a rectangle border that exactly covers the canvas area of
    the sensor pixel at column *sx*, row *sy*.

    The rectangle snaps to the pixel grid of the rendered image regardless
    of the current zoom / scale factor.

    Args:
        canvas: Target Tkinter canvas.
        mapper: Configured :class:`CoordMapper` instance.
        sx: Sensor column index.
        sy: Sensor row index.
        color: Outline colour string.
        width: Border stroke width (pixels).

    Returns:
        Canvas item ID, or ``-1`` if the mapper is not configured.
    """
    bounds = mapper.get_pixel_bounds(sx, sy)
    if bounds is None:
        return -1
    px, py, px2, py2 = bounds
    return canvas.create_rectangle(
        px, py, px2, py2,
        outline=color,
        fill="",
        width=width,
    )


def create_sensor_crosshair(
    canvas: tk.Canvas,
    mapper: CoordMapper,
    sx: float,
    sy: float,
    color: str,
    gap: int = 3,
    arm: int = 12,
    width: int = 2,
) -> List[int]:
    """
    Create a crosshair at sensor coordinates *(sx, sy)*.

    The visual size (gap, arm, width) remains constant regardless of
    the sensor zoom level.

    Args:
        canvas: Target Tkinter canvas.
        mapper: Configured :class:`CoordMapper` instance.
        sx: Sensor column index (float OK).
        sy: Sensor row index (float OK).
        color: Line colour string.
        gap: Distance from centre to arm start (pixels).
        arm: Arm length from gap outward (pixels).
        width: Stroke width (pixels).

    Returns:
        List of four canvas item IDs.
    """
    cx, cy = mapper.sensor_to_canvas(sx, sy)
    return create_crosshair(canvas, cx, cy, color, gap, arm, width)


def create_sensor_smart_text(
    canvas: tk.Canvas,
    mapper: CoordMapper,
    sx: float,
    sy: float,
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
    Create edge-clamped text anchored at sensor coordinates *(sx, sy)*.

    Args:
        canvas: Target Tkinter canvas.
        mapper: Configured :class:`CoordMapper` instance.
        sx: Sensor column index.
        sy: Sensor row index.
        text: The string to display.
        color: Text colour string.
        canvas_w: Current canvas width for clamping.
        canvas_h: Current canvas height for clamping.
        offset: Label offset from the anchor point (pixels).
        font: Tkinter font tuple.
        bg_color: Background fill or ``None``.
        bg_padding: Background padding (pixels).
        rect_cache: Cross-frame PIL cache dict.
        image_cache: Per-frame PhotoImage reference cache.

    Returns:
        List of canvas item IDs.
    """
    cx, cy = mapper.sensor_to_canvas(sx, sy)
    return create_smart_text(
        canvas, cx, cy, text, color,
        canvas_w, canvas_h,
        offset, font, bg_color, bg_padding,
        rect_cache, image_cache,
    )
