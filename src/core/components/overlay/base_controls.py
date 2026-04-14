import tkinter as tk
from tkinter import ttk
from typing import Optional

from .canvas_overlay import CanvasOverlay
from src.core.components.controls.base import BaseControlFrame


class BaseOverlayControl(BaseControlFrame):
    """
    Base class for sidebar panels that manage a :class:`CanvasOverlay`.

    Responsibilities
    ----------------
    - Creates a "Show <title>" checkbutton bound to a ``tk.BooleanVar``.
    - Acquires the renderer canvas lazily via
      ``context.get_service('renderer_canvas')``.
    - Keeps ``context.state['params'][param_key]`` in sync with the
      checkbox so the value is available for future save/load of params.
    - Calls :meth:`_build_controls` **after** the checkbutton so subclasses
      can append their own widgets without touching ``__init__``.

    Parameters
    ----------
    parent:
        Parent Tkinter widget.
    context:
        Application ``AppContext`` instance.
    overlay:
        A :class:`CanvasOverlay` (or subclass) that this panel controls.
    title:
        Human-readable name used in the checkbox label ("Show <title>").
    param_key:
        Key in ``context.state['params']`` where visibility is stored.
        Registered with a default of ``False`` if absent.
    """

    def __init__(
        self,
        parent,
        context,
        overlay: CanvasOverlay,
        title: str,
        param_key: str,
        **kwargs,
    ):
        super().__init__(parent, context=context, **kwargs)
        self._overlay = overlay
        self._param_key = param_key
        self._canvas: Optional[tk.Canvas] = None

        # Register the key in params if not present yet.
        if param_key not in self.params:
            self.params[param_key] = False

        # Initialise the BooleanVar from whatever is currently in params.
        self.overlay_visible = tk.BooleanVar(value=bool(self.params[param_key]))

        row = 0
        self.add_section_header(row, f"{title} Controls")
        row += 1

        ttk.Checkbutton(
            self,
            text=f"Show {title}",
            variable=self.overlay_visible,
            command=self._toggle_overlay,
        ).grid(row=row, column=0, sticky=tk.W, pady=0, padx=0)
        row += 1
        self.current_row = row

        # Let subclasses add their own widgets below the checkbutton.
        self._build_controls()

    # ------------------------------------------------------------------
    # Override in subclasses
    # ------------------------------------------------------------------

    def _build_controls(self) -> None:
        """Add feature-specific widgets below the visibility checkbutton.

        Called automatically at the end of ``__init__``.  Override in
        subclasses — no need to call ``super()._build_controls()``.
        """

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_canvas(self) -> Optional[tk.Canvas]:
        """Return the renderer canvas, resolving it lazily if needed."""
        if not self._canvas:
            self._canvas = self.context.get_service('renderer_canvas')
        return self._canvas

    def _toggle_overlay(self) -> None:
        """Called when the user clicks the visibility checkbutton."""
        canvas = self._get_canvas()
        if canvas is None:
            self.context.event_bus.publish('LOG_MESSAGE', "Error: Renderer canvas not found.")
            self.overlay_visible.set(False)
            return

        visible = self.overlay_visible.get()
        # Persist to params so future save/load can restore the value.
        self.params[self._param_key] = visible

        if visible:
            self._overlay.show(canvas)
            self.context.event_bus.publish('LOG_MESSAGE', "Overlay shown.")
        else:
            self._overlay.hide()
            self.context.event_bus.publish('LOG_MESSAGE', "Overlay hidden.")
