"""
src/utils/hud_engine.py — import entry point
=============================================
The HUD engine has been refactored into the ``src/utils/hud/`` package.
This module re-exports the public API so existing import paths continue
to work without modification.

Preferred import::

    from src.utils.hud import HUDEngine
"""
# Re-export everything from the package for convenience
from src.utils.hud import (  # noqa: F401
    HUDEngine,
    CoordMapper,
    TickEngine,
    LAYER_BACKGROUND,
    LAYER_MAIN,
    LAYER_INTERACTION,
    LAYER_TOP,
)
