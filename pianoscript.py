import os
from PySide6 import QtCore, QtWidgets
from ui.main_window import MainWindow
from ui.style import Style
from settings_manager import get_settings
from icons.icons import get_qicon


def main():
    # Load settings and apply UI scale before creating QApplication
    settings = get_settings()
    ui_scale = float(settings.get("ui_scale", 1.0))

    os.environ.setdefault("QT_ENABLE_HIGHDPI_SCALING", "1")
    os.environ["QT_SCALE_FACTOR"] = str(ui_scale)
    # In Qt 6, AA_EnableHighDpiScaling is deprecated; high DPI is enabled by default.
    # Ensure Qt uses high-DPI pixmaps for crisp icons
    try:
        QtCore.QCoreApplication.setAttribute(QtCore.Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)
    except Exception:
        pass
    app = QtWidgets.QApplication([])
    # Set application window icon from icons package
    icon = get_qicon('pianoscript')
    if icon:
        app.setWindowIcon(icon)
    # Apply application palette (balanced native-like light look)
    Style().set_dynamic_theme(0.75)

    win = MainWindow()
    # Ensure clean shutdown of background threads on app exit
    app.aboutToQuit.connect(win.prepare_close)
    win.show()
    app.exec()


if __name__ == "__main__":
    main()
