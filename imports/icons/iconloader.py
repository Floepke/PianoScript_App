# This file contains base64 encoded png images.
# It is meant to be imported in another python file and the
# base64 strings can be converted into QIcons with the
# 'base64_to_qicon' function defined below.

from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtCore import QByteArray, QBuffer, QIODevice
import base64


def base64_to_qicon(base64_str):
    data = base64.b64decode(base64_str)
    pixmap = QPixmap()
    buf = QByteArray(data)
    buffer = QBuffer(buf)
    buffer.open(QIODevice.ReadOnly)
    pixmap.loadFromData(buffer.data())
    icon = QIcon(pixmap)
    return icon

# Example usage:
# base64_icon = 'iVBORw0KGgoAAAANSUhEUgAAA...'  # Base64 encoded png
# icon = base64_to_qicon(base64_icon)
# window.setWindowIcon(icon)
