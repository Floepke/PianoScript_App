from typing import Optional

try:
    from PySide6.QtCore import QByteArray
    from PySide6.QtGui import QFontDatabase, QFont
    from PySide6.QtWidgets import QApplication
except Exception:
    QByteArray = None
    QFontDatabase = None
    QFont = None
    QApplication = None

# Lazy import of generated base64 mapping
try:
    from .fonts_byte64 import FONTS  # type: ignore
except Exception:
    FONTS = {}


def register_font_from_bytes(name: str) -> Optional[str]:
    """Register the embedded font by `name` and return the primary family name.

    Returns None if registration fails or PySide6 is unavailable.
    """
    if QFontDatabase is None:
        return None
    try:
        import base64
        b64 = FONTS.get(name)
        if not b64:
            return None
        raw = base64.b64decode(b64)
        if QByteArray is not None:
            data = QByteArray(raw)
        else:
            data = raw
        fid = QFontDatabase.addApplicationFontFromData(data)
        if fid < 0:
            return None
        fams = QFontDatabase.applicationFontFamilies(fid)
        return fams[0] if fams else None
    except Exception:
        return None


def install_default_ui_font(app: Optional[QApplication] = None, name: str = 'FiraCode-SemiBold', point_size: int = 11) -> bool:
    """Install the embedded font and set it as the QApplication default.

    - Tries to register the font from embedded base64 (fonts_byte64.py).
    - If embedded font is missing, tries to use system-installed font by name.
    - Returns True if the app font was set; False otherwise.
    """
    if QApplication is None:
        return False
    if app is None:
        app = QApplication.instance()
    if app is None:
        return False

    family = register_font_from_bytes(name)
    try:
        if family:
            f = QFont(family, point_size)
            app.setFont(f)
            return True
        # Fallback: try system font
        f = QFont(name, point_size)
        if f and f.family():
            app.setFont(f)
            return True
    except Exception:
        return False
    return False
