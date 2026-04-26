"""
CoordMapper — Sensor ↔ Canvas Coordinate Transformation
=========================================================
Pure-Python class with zero Tkinter dependency so it can be
instantiated and unit-tested independently of a running GUI.
"""
from __future__ import annotations

from typing import Optional, Tuple


class CoordMapper:
    """
    Maps coordinates between raw sensor pixel space and the Tkinter canvas.

    The sensor image is rendered at an arbitrary scale and offset on the
    canvas (centred, letterboxed).  This class encapsulates all maths
    required to convert between the two spaces.

    Attributes
    ----------
    image_bbox : tuple or None
        ``(x1, y1, x2, y2)`` bounding box of the rendered image on the canvas.
    sensor_shape : tuple or None
        ``(height, width)`` of the raw sensor data, e.g. ``(192, 256)``.
    scale_x : float
        Canvas pixels per sensor column.
    scale_y : float
        Canvas pixels per sensor row.
    """

    def __init__(self) -> None:
        self._image_bbox: Optional[Tuple[int, int, int, int]] = None
        self._sensor_shape: Optional[Tuple[int, int]] = None
        self._scale_x: float = 1.0
        self._scale_y: float = 1.0

    # ------------------------------------------------------------------
    # Configuration
    # ------------------------------------------------------------------

    def set_mapping(
        self,
        image_bbox: Tuple[int, int, int, int],
        sensor_shape: Tuple[int, int],
    ) -> None:
        """
        Configure the coordinate mapping from new frame geometry.

        Args:
            image_bbox: ``(x1, y1, x2, y2)`` bounding box of the rendered
                image on the Tkinter canvas (canvas pixels).
            sensor_shape: ``(height, width)`` of the raw sensor data
                (e.g. ``(192, 256)`` for the TC001).
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

    # ------------------------------------------------------------------
    # Transforms
    # ------------------------------------------------------------------

    def sensor_to_canvas(self, sx: float, sy: float) -> Tuple[float, float]:
        """
        Transform a sensor-space coordinate to canvas space.

        Adds 0.5 to ``sx`` / ``sy`` so the result lands at the *centre*
        of the sensor pixel rather than its top-left corner.

        Args:
            sx: Sensor column index (float OK for sub-pixel precision).
            sy: Sensor row index.

        Returns:
            ``(cx, cy)`` in canvas pixels.
        """
        if not self._image_bbox:
            return sx, sy
        x1, y1, _, _ = self._image_bbox
        cx = x1 + (sx + 0.5) * self._scale_x
        cy = y1 + (sy + 0.5) * self._scale_y
        return cx, cy

    def canvas_to_sensor(self, cx: float, cy: float) -> Optional[Tuple[int, int]]:
        """
        Transform a canvas coordinate to the integer sensor pixel index.

        Args:
            cx: Canvas x coordinate (e.g. from a mouse event).
            cy: Canvas y coordinate.

        Returns:
            ``(col, row)`` sensor indices, or ``None`` when the point lies
            outside the rendered image area or when mapping is unconfigured.
        """
        if not self._image_bbox or not self._sensor_shape:
            return None
        x1, y1, x2, y2 = self._image_bbox
        if not (x1 <= cx < x2 and y1 <= cy < y2):
            return None
        raw_h, raw_w = self._sensor_shape
        sx = int((cx - x1) / self._scale_x)
        sy = int((cy - y1) / self._scale_y)
        sx = max(0, min(sx, raw_w - 1))
        sy = max(0, min(sy, raw_h - 1))
        return sx, sy

    def get_pixel_bounds(
        self, sx: int, sy: int
    ) -> Optional[Tuple[float, float, float, float]]:
        """
        Return the canvas bounding box of the sensor pixel at ``(sx, sy)``.

        Args:
            sx: Sensor column index.
            sy: Sensor row index.

        Returns:
            ``(px, py, px2, py2)`` in canvas coordinates, or ``None`` if
            the mapping has not been configured yet.
        """
        if not self._image_bbox:
            return None
        x1, y1, _, _ = self._image_bbox
        px  = x1 + sx * self._scale_x
        py  = y1 + sy * self._scale_y
        px2 = px + self._scale_x
        py2 = py + self._scale_y
        return px, py, px2, py2

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def image_bbox(self) -> Optional[Tuple[int, int, int, int]]:
        """Bounding box ``(x1, y1, x2, y2)`` of the rendered image on the canvas."""
        return self._image_bbox

    @property
    def sensor_shape(self) -> Optional[Tuple[int, int]]:
        """``(height, width)`` of the raw sensor data."""
        return self._sensor_shape

    @property
    def scale_x(self) -> float:
        """Canvas pixels per sensor column."""
        return self._scale_x

    @property
    def scale_y(self) -> float:
        """Canvas pixels per sensor row."""
        return self._scale_y
