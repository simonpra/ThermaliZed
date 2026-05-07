import tkinter as tk

# Custom SVG path mimicking fa-circle-chevron-up
# Viewbox is 0 0 512 512
ICONS = {
    "circle-chevron": {
        "viewBox": "0 0 512 512",
        "path": "M256 512A256 256 0 1 0 256 0a256 256 0 1 0 0 512zM377 271c9.4 9.4 9.4 24.6 0 33.9s-24.6 9.4-33.9 0l-87-87-87 87c-9.4 9.4-24.6 9.4-33.9 0s-9.4-24.6 0-33.9L239 167c9.4-9.4 24.6-9.4 33.9 0L377 271z"
    },
    "play": {
        "viewBox": "0 0 384 512",
        "path": "M73 39c-14.8-9.1-33.4-9.4-48.5-.9S0 62.6 0 80V432c0 17.4 9.4 33.4 24.5 41.9s33.7 8.1 48.5-.9L361 297c14.3-8.7 23-24.2 23-41s-8.7-32.2-23-41L73 39z"
    },
    "pause": {
        "viewBox": "0 0 320 512",
        "path": "M48 64C21.5 64 0 85.5 0 112V400c0 26.5 21.5 48 48 48H80c26.5 0 48-21.5 48-48V112c0-26.5-21.5-48-48-48H48zm192 0c-26.5 0-48 21.5-48 48V400c0 26.5 21.5 48 48 48h32c26.5 0 48-21.5 48-48V112c0-26.5-21.5-48-48-48H240z"
    },
    "step-forward": {
        "viewBox": "0 0 384 512",
        "path": "M342.6 233.4c12.5 12.5 12.5 32.8 0 45.3l-192 192c-12.5 12.5-32.8 12.5-45.3 0s-12.5-32.8 0-45.3L274.7 256 105.4 86.6c-12.5-12.5-12.5-32.8 0-45.3s32.8-12.5 45.3 0l192 192z"
    },
    "step-backward": {
        "viewBox": "0 0 384 512",
        "path": "M41.4 233.4c-12.5 12.5-12.5 32.8 0 45.3l192 192c12.5 12.5 32.8 12.5 45.3 0s12.5-32.8 0-45.3L109.3 256 278.6 86.6c12.5-12.5 12.5-32.8 0-45.3s-32.8-12.5-45.3 0l-192 192z"
    }
}

class ButtonIcon(tk.Label):
    """
    A custom Label acting as a button with an SVG icon.
    Uses native tk.PhotoImage SVG format (requires Tk 9.0+).
    """
    def __init__(self, parent, icon_name="circle-chevron", color="#ffffff", size=24, bg="transparent", rotation=0, command=None, **kwargs):
        self.icon_name = icon_name
        self.color = color
        self.size = size
        self.bg_color = None if bg == "transparent" else bg
        self.rotation = rotation
        self.command = command
        
        # Pull standard tk.Label kwargs, merging our custom defaults
        lbl_kwargs = {
            'cursor': 'hand1' if command else '',
            'borderwidth': 0,
            'highlightthickness': 0
        }
        if self.bg_color:
            lbl_kwargs['bg'] = self.bg_color
        
        lbl_kwargs.update(kwargs)
        super().__init__(parent, **lbl_kwargs)

        self._image = None
        self.update_icon()

        if command:
            self.bind("<Button-1>", lambda e: self.command())
            
    def update_icon(self, icon_name=None, color=None, rotation=None, size=None):
        """Update the icon visuals dynamically."""
        if icon_name is not None: self.icon_name = icon_name
        if color is not None: self.color = color
        if rotation is not None: self.rotation = rotation
        if size is not None: self.size = size
        
        icon_data = ICONS.get(self.icon_name)
        if not icon_data:
            return

        viewbox = icon_data["viewBox"]
        path = icon_data["path"]
        
        # Calculate centers for rotation based on viewbox
        vb_parts = [int(x) for x in viewbox.split()]
        cx, cy = vb_parts[2] // 2, vb_parts[3] // 2

        # Create the raw SVG string
        svg_xml = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="{viewbox}">
            <g transform="rotate({self.rotation} {cx} {cy})">
                <path fill="{self.color}" d="{path}"/>
            </g>
        </svg>'''

        # We load without a set size, then scale
        # Native tk.PhotoImage scaling is roughly (target_size / viewbox_width)
        # Note: SVG `format` in Tkinter allows `-scale factor` but it calculates differently depending on implementation.
        # As an alternative natively in Tk 9.0, we just set `width` and `height` in the SVG root.
        
        svg_xml = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{self.size}" height="{self.size}" viewBox="{viewbox}">
            <g transform="rotate({self.rotation} {cx} {cy})">
                <path fill="{self.color}" d="{path}"/>
            </g>
        </svg>'''

        # Using Tk 9.0 native svg rendering
        try:
            self._image = tk.PhotoImage(data=svg_xml.encode('utf-8'), format="svg")
            self.config(image=self._image)
        except tk.TclError as e:
            # Fallback text if tk version doesn't support svg native (e.g. Tk 8.6)
            self.config(text="[Icon]")
            print(f"SVG load error (Requires Tk 9.0+): {e}")

