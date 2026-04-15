"""
Global constants and default initial state variables.
"""
import cv2

# Configuration Colormaps for OpenCV
COLORMAPS = [
    (cv2.COLORMAP_INFERNO, "Inferno"),
    (cv2.COLORMAP_JET, "Jet"),
    (cv2.COLORMAP_HOT, "Hot"),
    (cv2.COLORMAP_PLASMA, "Plasma"),
    (cv2.COLORMAP_VIRIDIS, "Viridis"),
    (cv2.COLORMAP_MAGMA, "Magma"),
    (cv2.COLORMAP_TURBO, "Turbo"),
    (cv2.COLORMAP_RAINBOW, "Rainbow")
]

# Default processing parameters
DEFAULT_PARAMS = {
    'colormap_index': 0,
    'manual_leveling': False,
    'manual_min_raw': 18122,
    'manual_max_raw': 20682,
    'blur': 0,
    'alpha': 1.0,
    'gamma': 1.0,
    'gradient_step': 0.0,
    'overlay_gradient_visible': True,
    'overlay_hud_visible': False,
}
