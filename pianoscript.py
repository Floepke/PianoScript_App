import os
import sys
from PySide6 import QtCore, QtWidgets, QtGui
from ui.main_window import MainWindow
from ui.style import Style
from settings_manager import get_preferences
from appdata_manager import get_appdata_manager
from icons.icons import get_qicon
from fonts import install_default_ui_font


def main():
    # Load settings and apply UI scale before creating QApplication
    preferences = get_preferences()
    ui_scale = float(preferences.get("ui_scale", 1.0))
    
    # Initialize appdata to ensure ~/.keyTAB/appdata.py exists
    get_appdata_manager()

    # Platform-specific DPI handling:
    # - On Linux, use Qt env vars to scale UI.
    # - On macOS, explicitly clear Qt scaling and plugin env to avoid Cocoa issues.
    if sys.platform.startswith("linux"):
        os.environ.setdefault("QT_ENABLE_HIGHDPI_SCALING", "1")
        os.environ["QT_SCALE_FACTOR"] = str(ui_scale)
    elif sys.platform == "darwin":
        ...
    
    # In Qt 6, high DPI handling is enabled by default; avoid deprecated attributes
    # to prevent warnings and potential initialization issues.
    
    # On macOS, force menus to render inside the window instead of the global menu bar
    if sys.platform == "darwin":
        try:
            QtCore.QCoreApplication.setAttribute(
                QtCore.Qt.ApplicationAttribute.AA_DontUseNativeMenuBar, True
            )
        except Exception:
            # Fallback will be applied per-window in MainWindow if this attribute is unavailable
            pass
    # Create QApplication with argv to ensure proper initialization paths on macOS
    app = QtWidgets.QApplication(sys.argv)
    
    # Enforce arrow cursor globally: app never changes the mouse pointer
    QtGui.QGuiApplication.setOverrideCursor(QtGui.QCursor(QtCore.Qt.CursorShape.ArrowCursor))
    
    # Install and apply embedded UI font (FiraCode-SemiBold) globally
    try:
        install_default_ui_font(app, name='FiraCode-SemiBold', point_size=int(10))
    except Exception:
        # Proceed with default font if installation fails
        pass

    # Set application window icon from icons package
    # Scale window icon slightly smaller for the title bar
    icon = get_qicon('keyTAB', size=(64, 64))
    if icon:
        app.setWindowIcon(icon)
    
    # Apply application palette based on preferences
    theme = str(preferences.get('theme', 'light')).lower()
    sty = Style()
    if theme == 'dark':
        sty.set_dark_theme()
    else:
        sty.set_dynamic_theme(0.75)

    win = MainWindow()
    
    # Ensure clean shutdown of background threads on app exit
    app.aboutToQuit.connect(win.prepare_close)
    
    # Restore window geometry or start maximized based on appdata
    try:
        adm = get_appdata_manager()
        start_max = bool(adm.get("window_maximized", True))
        if not start_max:
            geom_b64 = str(adm.get("window_geometry", ""))
            try:
                if geom_b64:
                    win.restoreGeometry(QtCore.QByteArray.fromBase64(geom_b64.encode("ascii")))
            except Exception:
                pass
            win.show()
        else:
            win.showMaximized()
    except Exception:
        # Fallback: show maximized
        win.showMaximized()
    app.exec()


if __name__ == "__main__":
    main()
