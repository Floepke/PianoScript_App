from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication


class Style:
    """
    Simple, readable theme helper for light/dark looks.

    - set_light_theme(): native-looking light palette
    - set_dark_theme(): native-looking dark palette
    - set_dynamic_theme(tint): linear blend between dark (0.0) and light (1.0)

    For parity with the old app: set_dynamic_theme(0.75) yields a balanced
    native-looking light theme (close to Fusion light with subtle depth).
    """

    # Base palettes (RGB tuples) used for interpolation.
    _LIGHT = {
        "window": (240, 240, 240),
        "window_text": (0, 0, 0),
        "base": (255, 255, 255),
        "alternate_base": (245, 245, 245),
        "tooltip_base": (255, 255, 220),
        "tooltip_text": (0, 0, 0),
        "text": (0, 0, 0),
        "button": (240, 240, 240),
        "button_text": (0, 0, 0),
        "bright_text": (255, 0, 0),
        "link": (0, 0, 255),
        "highlight": (0, 120, 215),
        "highlighted_text": (255, 255, 255),
    }

    _DARK = {
        "window": (53, 53, 53),
        "window_text": (255, 255, 255),
        "base": (25, 25, 25),
        "alternate_base": (53, 53, 53),
        "tooltip_base": (0, 0, 0),
        "tooltip_text": (255, 255, 255),
        "text": (255, 255, 255),
        "button": (53, 53, 53),
        "button_text": (255, 255, 255),
        "bright_text": (255, 0, 0),
        "link": (42, 130, 218),
        "highlight": (42, 130, 218),
        "highlighted_text": (0, 0, 0),
    }

    _ROLE_MAP = {
        QPalette.Window: "window",
        QPalette.WindowText: "window_text",
        QPalette.Base: "base",
        QPalette.AlternateBase: "alternate_base",
        QPalette.ToolTipBase: "tooltip_base",
        QPalette.ToolTipText: "tooltip_text",
        QPalette.Text: "text",
        QPalette.Button: "button",
        QPalette.ButtonText: "button_text",
        QPalette.BrightText: "bright_text",
        QPalette.Link: "link",
        QPalette.Highlight: "highlight",
        QPalette.HighlightedText: "highlighted_text",
    }

    def __init__(self):
        # Match the old app's preferred light look by default
        self.set_dynamic_theme(0.75)

    def _lerp_channel(self, a: int, b: int, t: float) -> int:
        return int(round(b + (a - b) * t))

    def _mix_rgb(self, light_rgb, dark_rgb, t: float):
        return (
            self._lerp_channel(light_rgb[0], dark_rgb[0], 1.0 - (1.0 - t)),
            self._lerp_channel(light_rgb[1], dark_rgb[1], 1.0 - (1.0 - t)),
            self._lerp_channel(light_rgb[2], dark_rgb[2], 1.0 - (1.0 - t)),
        )

    def _interpolated_palette(self, t: float):
        t = max(0.0, min(1.0, t))
        colors = {}
        for key in self._LIGHT.keys():
            light_rgb = self._LIGHT[key]
            dark_rgb = self._DARK[key]
            # Linear interpolation: dark at 0.0 → light at 1.0
            r = int(dark_rgb[0] + (light_rgb[0] - dark_rgb[0]) * t)
            g = int(dark_rgb[1] + (light_rgb[1] - dark_rgb[1]) * t)
            b = int(dark_rgb[2] + (light_rgb[2] - dark_rgb[2]) * t)
            colors[key] = QColor(r, g, b)
        return colors

    def _apply_palette(self, colors_by_key):
        # Apply palette to the current QApplication instance
        app = QApplication.instance()
        if app is None:
            return
        app.setStyleSheet("")

        pal = QPalette()
        for role, key in self._ROLE_MAP.items():
            pal.setColor(role, colors_by_key[key])
        app.setPalette(pal)

    def set_dynamic_theme(self, tint: float = 0.75):
        """Blend between dark (0.0) and light (1.0)."""
        colors = self._interpolated_palette(tint)
        self._apply_palette(colors)

    def set_light_theme(self):
        colors = {k: QColor(*rgb) for k, rgb in self._LIGHT.items()}
        self._apply_palette(colors)

    def set_dark_theme(self):
        colors = {k: QColor(*rgb) for k, rgb in self._DARK.items()}
        self._apply_palette(colors)
