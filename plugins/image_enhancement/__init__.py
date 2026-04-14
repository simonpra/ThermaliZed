import tkinter as tk
from tkinter import ttk
from typing import Optional

import cv2
import numpy as np

from src.core.plugin_base import SystemComponent
from src.core.components.controls.base import BaseControlFrame


class ImageEnhancementFrame(BaseControlFrame):
    """Sidebar control panel for the image enhancement pipeline plugin."""

    def __init__(self, parent, context, **kwargs):
        # call the BaseControlFrame constructor that initializes the Context and Params
        # give access to method add_section_header() and add_label_slider() for easy UI intergration
        super().__init__(parent, context=context, **kwargs)

        row = 0
        self.add_section_header(row, "Image Enhancement")
        row += 1

        ##################################################
        ### Init tk Var for responsivness with UI,     ###
        ### with self.params.get(key, default_value)   ###
        ### to initialize the variable into the        ###
        ### context.state['params'] dictionary         ###
        ### making it available accross the app.       ###  
        ##################################################

        # --- Contrast (Alpha) ---
        self.alpha_var = tk.DoubleVar(value=self.params.get('alpha', 1.0))
        self.add_label_slider(row, "Contrast (Alpha):", self.alpha_var, 0.5, 3.0, 0.1, self._on_alpha_changed)
        row += 2

        # --- Texture (Gamma) ---
        self.gamma_var = tk.DoubleVar(value=self.params.get('gamma', 1.0))
        self.add_label_slider(row, "Texture (Gamma):", self.gamma_var, 0.1, 3.0, 0.1, self._on_gamma_changed)
        row += 2

        # --- Blur Radius ---
        self.blur_var = tk.IntVar(value=self.params.get('blur', 0))
        self.add_label_slider(row, "Blur Radius:", self.blur_var, 0, 10, 1.0, self._on_blur_changed)
        row += 2

    def _on_alpha_changed(self, _event=None):
        self.params['alpha'] = round(float(self.alpha_var.get()), 1)

    def _on_gamma_changed(self, _event=None):
        self.params['gamma'] = round(float(self.gamma_var.get()), 2)

    def _on_blur_changed(self, _event=None):
        self.params['blur'] = int(float(self.blur_var.get()))


class PluginClass(SystemComponent):
    """
    Image Enhancement plugin: applies Contrast → Texture → Blur to the
    raw 16-bit thermal array via the RAW_FRAME_PIPELINE event bus.

    Processing order (all on uint16 data, before normalization/colormap):
        1. Contrast (Alpha) — histogram squeeze: narrows the effective norm range
                              so the auto-scaler amplifies the remaining detail.
        2. Texture  (Gamma) — power-law mid-tone shift; leaves absolute
                              min/max boundaries intact.
        3. Blur             — spatial smoothing via cv2.blur.
    """

    # NEEDED : this function is called when the plugin is loaded
    def on_load(self, context):
        self.context = context
        # subscribe to the RAW_FRAME_PIPELINE event/stream to hook our image processing function
        context.event_bus.subscribe('RAW_FRAME_PIPELINE', self._on_raw_frame_pipeline)

    # Data processor function: called whenever the RAW_FRAME_PIPELINE event is emitted
    def _on_raw_frame_pipeline(
        self,
        raw_thermal_16bit: np.ndarray,
        raw: np.ndarray,
    ) -> Optional[np.ndarray]:
        """
        Pipeline stage: applies contrast, gamma, and blur to the 16-bit array.

        Args:
            raw_thermal_16bit: Current 2-D uint16 array (may already be modified
                               by prior pipeline stages, e.g. gradient-step).
            raw: Original unmodified 16-bit array — do not mutate.

        Returns:
            Modified uint16 array, or None for pass-through.
        """
        # Retrieve the plugin's parameters from the context's state
        params = self.context.state.get('params', {})
        alpha = params.get('alpha', 1.0)
        gamma = params.get('gamma', 1.0)
        blur  = params.get('blur',  0)

        # Fast path: nothing to do
        if alpha == 1.0 and gamma == 1.0 and blur == 0:
            return None

        data = raw_thermal_16bit.astype(np.float32)

        # ------------------------------------------------------------------
        # 1. Contrast (Alpha) — Midpoint linear stretching
        #    Because downstream auto-normalization is now locked to the original
        #    raw scene bounds, simply stretching values around the midpoint creates
        #    proper visible contrast changes without being undone by the normalizer.
        # ------------------------------------------------------------------
        if alpha != 1.0:
            p_low  = float(np.percentile(data, 1))
            p_high = float(np.percentile(data, 99))
            mid    = (p_low + p_high) / 2.0
            data   = mid + (data - mid) * alpha


        # ------------------------------------------------------------------
        # 2. Texture (Gamma) — power-law mid-tone transformation
        #    Normalizes to [0, 1] against the *current* data's min/max so
        #    the absolute temperature boundaries are preserved.
        #    gamma > 1 → lifts shadows (more visible cool detail)
        #    gamma < 1 → crushes highlights (suppresses noise in hot areas)
        # ------------------------------------------------------------------
        if gamma != 1.0:
            f_min = float(np.min(data))
            f_max = float(np.max(data))
            span  = f_max - f_min
            if span > 0:
                normalized = (data - f_min) / span
                normalized = np.power(np.clip(normalized, 0.0, 1.0), 1.0 / gamma)
                data = normalized * span + f_min

        # Clip and convert back to uint16 before optional blur
        data = np.clip(data, 0, 65535).astype(np.uint16)

        # ------------------------------------------------------------------
        # 3. Blur — spatial smoothing applied last
        # ------------------------------------------------------------------
        if blur > 0:
            data = cv2.blur(data, (blur, blur))

        return data

    # Instanciate the sliders UI into a ttk.Frame() onto the left_sidebar area
    def get_ui(self, parent_widget, zone):
        if zone == 'left_sidebar':
            wrapper = ttk.Frame(parent_widget, padding=0)
            self.ui = ImageEnhancementFrame(wrapper, self.context)
            self.ui.pack(fill=tk.BOTH, expand=False, pady=0, padx=0)
            return wrapper
        return None
