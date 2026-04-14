"""
Utility mathematical functions for thermal data conversion.
"""

def to_degrees_c(raw):
    """
    Convert a TC001 raw 16-bit thermal uint to degrees Celsius.
    Note: Formula assumes (raw / 64) = Kelvin.
    """
    temps_celsius = (raw / 64.0) - 273.15
    return round(float(temps_celsius), 1)

def to_raw(celsius):
    """
    Convert a temperature in degrees Celsius back to a TC001 raw 16-bit uint.
    Note: Formula assumes (Celsius + 273.15) * 64 = raw.
    """
    raw = (celsius + 273.15) * 64.0
    return int(round(raw))

