"""
Utility mathematical functions for thermal data conversion.
"""

import numpy as np


def to_degrees_c(raw):
    """
    Convert TC001/TS001 raw 16-bit thermal values to degrees Celsius.

    Scalars are returned as ``float`` values while NumPy arrays retain their
    shape. The processor passes a complete sensor frame here, so converting the
    result directly to ``float`` would fail and hide all temperature readings.

    Note: Formula assumes (raw / 64) = Kelvin.
    """
    temps_celsius = np.asarray(raw, dtype=np.float64) / 64.0 - 273.15
    rounded = np.round(temps_celsius, 1)
    return float(rounded) if rounded.ndim == 0 else rounded

def to_raw(celsius):
    """
    Convert a temperature in degrees Celsius back to a TC001 raw 16-bit uint.
    Note: Formula assumes (Celsius + 273.15) * 64 = raw.
    """
    raw = (celsius + 273.15) * 64.0
    return int(round(raw))
