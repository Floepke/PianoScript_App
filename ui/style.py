import sys
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication
from settings_manager import get_preferences


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
    # The theme is driven by four colors:
    # - bg_color: window/dialog/dropdown backgrounds
    # - text_color: all text color
    # - color3: buttons and widget entry/list backgrounds
    # - accent_color: selection and emphasis highlights
    _LIGHT = {
        "bg_color": (240, 240, 240),
        "text_color": (0, 0, 0),
        "color3": (245, 255, 255),
        "accent_color": (0, 120, 215),
    }

    _DARK = {
        "bg_color": (60, 60, 70),
        "text_color": (250, 200, 210),
        "color3": (53, 53, 63),
        "accent_color": (42, 130, 218),
    }

    # Palette role → dict key mapping using the four-theme colors above.
    _ROLE_MAP = {
        QPalette.Window: "bg_color",
        QPalette.WindowText: "text_color",
        QPalette.Base: "color3",
        QPalette.AlternateBase: "color3",
        QPalette.ToolTipBase: "bg_color",
        QPalette.ToolTipText: "text_color",
        QPalette.Text: "text_color",
        QPalette.Button: "color3",
        QPalette.ButtonText: "text_color",
        QPalette.BrightText: "text_color",
        QPalette.Link: "accent_color",
        QPalette.Highlight: "accent_color",
        QPalette.HighlightedText: "text_color",
    }

    def __init__(self):
        # Match the old app's preferred light look by default
        self.set_dynamic_theme(0.75)
        self.editor_background_color = self.get_editor_background_color()
        self._sync_editor_named_color()

    # Named custom colors registry
    _NAMED: dict[str, tuple[int, int, int]] = {
        # Print view (DrawUtilView): white by default
        'draw_util': (255, 255, 255),
        # Editor background: initialized/synced at runtime
        'editor': (255, 255, 255),
        # Theme colors (synced at runtime)
        'bg': (240, 240, 240),
        'text': (0, 0, 0),
        'alternate_background_color': (240, 240, 240),
        'accent': (0, 120, 215),
    }

    @classmethod
    def set_named_color(cls, name: str, rgb: tuple[int, int, int]) -> None:
        cls._NAMED[name] = tuple(int(max(0, min(255, c))) for c in rgb)

    @classmethod
    def get_named_qcolor(cls, name: str, fallback: tuple[int, int, int] = (240, 240, 240)) -> QColor:
        rgb = cls._NAMED.get(name, fallback)
        return QColor(*rgb)

    @classmethod
    def get_named_rgb(cls, name: str, fallback: tuple[int, int, int] = (240, 240, 240)) -> tuple[int, int, int]:
        return cls._NAMED.get(name, fallback)

    def _sync_editor_named_color(self) -> None:
        rgb = self.get_editor_background_color()
        self.editor_background_color = rgb
        Style._NAMED['editor'] = tuple(int(c) for c in rgb)

    def _sync_named_theme_colors(self, colors_by_key) -> None:
        try:
            bg = colors_by_key["bg_color"]
            text = colors_by_key["text_color"]
            alternate_background_color = colors_by_key["alternate_background_color"]
            accent = colors_by_key["accent_color"]
            Style._NAMED['bg'] = (bg.red(), bg.green(), bg.blue())
            Style._NAMED['text'] = (text.red(), text.green(), text.blue())
            Style._NAMED['alternate_background_color'] = (alternate_background_color.red(), alternate_background_color.green(), alternate_background_color.blue())
            Style._NAMED['accent'] = (accent.red(), accent.green(), accent.blue())
            Style._NAMED['editor'] = Style._NAMED['bg']
        except Exception:
            pass

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
        # Clear any previous global stylesheet; we may set a Windows-specific one below
        app.setStyleSheet("")

        pal = QPalette()
        for role, key in self._ROLE_MAP.items():
            pal.setColor(role, colors_by_key[key])
        app.setPalette(pal)

        self._sync_named_theme_colors(colors_by_key)

        # Windows-specific fix: ensure QMenu background matches the window color
        # Some Windows themes/hardware drivers render menus with mismatched dark backgrounds.
        if sys.platform == 'win32':
            try:
                window_hex = colors_by_key["bg_color"].name()
                text_hex = colors_by_key["text_color"].name()
                highlight_hex = colors_by_key["accent_color"].name()
                highlighted_text_hex = text_hex

                win_menu_css = f"""
                QMenu {{
                    background-color: {window_hex};
                    color: {text_hex};
                }}
                QMenu::item {{
                    background-color: transparent;
                    color: {text_hex};
                }}
                QMenu::item:selected {{
                    background-color: {highlight_hex};
                    color: {highlighted_text_hex};
                }}
                QMenu::separator {{
                    background-color: {highlight_hex};
                    height: 1px;
                    margin: 4px 6px;
                }}
                """
                app.setStyleSheet(win_menu_css)
            except Exception:
                # Silently ignore stylesheet issues; palette is still applied
                pass

    def set_dynamic_theme(self, tint: float = 0.75):
        """Blend between dark (0.0) and light (1.0)."""
        colors = self._interpolated_palette(tint)
        self._apply_palette(colors)
        self._sync_editor_named_color()

    def set_light_theme(self):
        colors = {k: QColor(*rgb) for k, rgb in self._LIGHT.items()}
        self._apply_palette(colors)
        self._sync_editor_named_color()

    def set_dark_theme(self):
        colors = {k: QColor(*rgb) for k, rgb in self._DARK.items()}
        self._apply_palette(colors)
        self._sync_editor_named_color()

    def get_editor_background_color(self) -> tuple[int, int, int]:
        """Get the appropriate editor background color based on current theme."""
        return Style._NAMED.get('bg', (240, 240, 240))