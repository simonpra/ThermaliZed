import tkinter as tk
from tkinter import ttk
import numpy as np

from src.core.plugin_base import SystemComponent
from src.core.components.overlay.canvas_overlay import CanvasOverlay
from src.core.components.overlay.base_controls import BaseOverlayControl


class HudOverlay(CanvasOverlay):
    """
    Thermal HUD rendered as a ttk.Frame window on the canvas.
    Subscribes to METADATA_READY and updates label widgets in-place.
    Positioned at the top-left corner of the renderer canvas.
    """

    # Ordered field definitions: (dict_key, label_prefix, format_fn)
    _FIELDS = [
        ('fps',           'FPS',         lambda v: f"{v:.1f}"),
        ('proc_time_ms',  'Proc',        lambda v: f"{v:.1f} ms"),
        ('min_raw',       'Raw',         lambda v, d: f"{v} – {d.get('max_raw', '?')}"),
        ('norm_min',      'Norm',        lambda v, d: "{:.0f} – {:.0f} ({})".format(
                                              v, d.get('norm_max', 0),
                                              'Man' if d.get('manual_leveling') else 'Auto')),
        ('min_c',         'Est °C',      lambda v, d: f"{v:.1f} – {d.get('max_c', float('nan')):.1f}"
                                              if not np.isnan(v) else None),
        ('colormap_name', 'Map',         lambda v: v),
        ('blur',          'Blur',        lambda v: str(v)),
        ('alpha',         'Contrast',    lambda v: f"{v:.1f}"),
        ('gamma',         'Texture',     lambda v: f"{v:.1f}"),
    ]


    def __init__(self, **kwargs):
        super().__init__(x=10, y=10, anchor='nw', **kwargs)
        self._labels: dict[str, ttk.Label] = {}

    def _build_overlay_content(self, frame: ttk.Frame) -> None:
        frame.configure(padding=(6, 4))
        # Create one label per field; we update their text on every METADATA_READY.
        for key, prefix, _ in self._FIELDS:
            lbl = ttk.Label(
                frame,
                text=f"{prefix}: —",
                font=("", 11, "normal"),
                foreground="white",
                background="#1a1a1a",
                anchor="w",
            )
            lbl.pack(fill=tk.X, padx=2, pady=1)
            self._labels[key] = lbl

    def update(self, infos: dict) -> None:
        """Refresh all label texts from the latest METADATA_READY payload."""
        for key, prefix, fmt in self._FIELDS:
            lbl = self._labels.get(key)
            if lbl is None:
                continue
            val = infos.get(key)
            if val is None:
                continue
            try:
                import inspect
                sig = inspect.signature(fmt)
                if len(sig.parameters) == 1:
                    text = fmt(val)
                else:
                    text = fmt(val, infos)
            except Exception:
                text = str(val)

            # None means "skip / hide this field" (e.g. NaN celsius)
            if text is None:
                lbl.configure(text="")
            else:
                lbl.configure(text=f"{prefix}: {text}")


class HudControls(BaseOverlayControl):
    """Sidebar panel for the thermal HUD overlay.

    Wires the "Show HUD" checkbox to :class:`HudOverlay`, persists the
    visibility flag to ``params['overlay_hud_visible']``, and subscribes to
    ``METADATA_READY`` to forward data to the overlay while it is visible.
    """

    def __init__(self, parent, context, overlay: HudOverlay, **kwargs):
        super().__init__(
            parent,
            context,
            overlay=overlay,
            title="HUD",
            param_key="overlay_hud_visible",
            **kwargs,
        )
        # Forward thermal metadata to the overlay whenever it is visible.
        context.event_bus.subscribe('METADATA_READY', self._on_metadata)

    def _on_metadata(self, infos: dict) -> None:
        """Update HUD labels; auto-show on first data if params flag is set."""
        canvas = self._get_canvas()
        if canvas is None:
            return

        # Auto-show on startup if the saved param says it was visible.
        if not self._overlay.visible and self.params.get(self._param_key, False):
            self._overlay.show(canvas)
            self.overlay_visible.set(True)

        if self._overlay.visible:
            self._overlay.update(infos)


class PluginClass(SystemComponent):
    """Core plugin for the thermal HUD overlay."""

    def on_load(self, context):
        self.context = context
        self._overlay = HudOverlay()

    def get_ui(self, parent_widget, zone):
        if zone == 'left_sidebar':
            self.ui = HudControls(parent_widget, self.context, self._overlay)
            self.ui.pack(fill=tk.X, expand=False)
            return self.ui
        return None
