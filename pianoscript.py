import os
import sys
from PySide6 import QtCore, QtWidgets, QtGui
from ui.main_window import MainWindow
from ui.style import Style
from settings_manager import get_preferences
from appdata_manager import get_appdata_manager
from icons.icons import get_qicon


def main():
    # Load settings and apply UI scale before creating QApplication
    preferences = get_preferences()
    ui_scale = float(preferences.get("ui_scale", 1.0))
    # Initialize appdata to ensure ~/.pianoscript/appdata.py exists
    get_appdata_manager()

    os.environ.setdefault("QT_ENABLE_HIGHDPI_SCALING", "1")
    os.environ["QT_SCALE_FACTOR"] = str(ui_scale)
    # In Qt 6, AA_EnableHighDpiScaling is deprecated; high DPI is enabled by default.
    # Ensure Qt uses high-DPI pixmaps for crisp icons
    try:
        QtCore.QCoreApplication.setAttribute(QtCore.Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)
    except Exception:
        pass
    # On macOS, force menus to render inside the window instead of the global menu bar
    if sys.platform == "darwin":
        try:
            QtCore.QCoreApplication.setAttribute(
                QtCore.Qt.ApplicationAttribute.AA_DontUseNativeMenuBar, True
            )
        except Exception:
            # Fallback will be applied per-window in MainWindow if this attribute is unavailable
            pass
    app = QtWidgets.QApplication([])
    # Enforce arrow cursor globally: app never changes the mouse pointer
    QtGui.QGuiApplication.setOverrideCursor(QtGui.QCursor(QtCore.Qt.CursorShape.ArrowCursor))
    # Set application window icon from icons package
    # Scale window icon slightly smaller for the title bar
    icon = get_qicon('pianoscript', size=(64, 64))
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
    win.show()
    app.exec()


if __name__ == "__main__":
    main()
