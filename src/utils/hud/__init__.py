"""
src/utils/hud — HUD Drawing Engine Package
==========================================
Public entry point.  Import :class:`HUDEngine` from here:

    from src.utils.hud import HUDEngine

Layer constants are also re-exported for plugin authors:

    from src.utils.hud import LAYER_BACKGROUND, LAYER_MAIN, LAYER_INTERACTION, LAYER_TOP
"""
from src.utils.hud.core import (
    HUDEngine,
    LAYER_BACKGROUND,
    LAYER_MAIN,
    LAYER_INTERACTION,
    LAYER_TOP,
)
from src.utils.hud.mapper import CoordMapper
from src.utils.hud.interaction import TickEngine

__all__ = [
    "HUDEngine",
    "CoordMapper",
    "TickEngine",
    "LAYER_BACKGROUND",
    "LAYER_MAIN",
    "LAYER_INTERACTION",
    "LAYER_TOP",
]
