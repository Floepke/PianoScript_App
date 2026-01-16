from __future__ import annotations
from PySide6 import QtCore, QtGui, QtWidgets
import cairo
import math
from typing import Optional
from editor.editor import Editor
from editor.drawers import get_all_drawers


def _make_image_and_surface(width: int, height: int):
    width = max(1, int(width))
    height = max(1, int(height))
    stride = width * 4
    buf = bytearray(height * stride)
    surface = cairo.ImageSurface.create_for_data(buf, cairo.FORMAT_ARGB32, width, height, stride)
    image = QtGui.QImage(buf, width, height, stride, QtGui.QImage.Format.Format_ARGB32_Premultiplied)
    return image, surface, buf


def _draw_editor_background(ctx: cairo.Context, w: int, h: int, color=(0.12, 0.12, 0.12)):
    # Neutral background; no demo drawings.
    ctx.set_source_rgb(*color)
    ctx.paint()


class CairoEditorWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        # Allow splitter to fully collapse this view
        self.setMinimumWidth(0)
        self.setMouseTracking(True)
        self._current_tool: str | None = None
        self._editor: Optional[Editor] = None
        self._last_pos: QtCore.QPointF | None = None

    def set_editor(self, editor: Editor) -> None:
        self._editor = editor

    def set_tool(self, tool_name: str | None) -> None:
        self._current_tool = tool_name
        self.update()

    def paintEvent(self, ev: QtGui.QPaintEvent) -> None:
        sz = self.size()
        dpr = float(self.devicePixelRatioF())
        w_px = int(max(1, sz.width() * dpr))
        h_px = int(max(1, sz.height() * dpr))
        image, surface, _buf = _make_image_and_surface(w_px, h_px)
        ctx = cairo.Context(surface)
        ctx.set_antialias(cairo.ANTIALIAS_BEST)
        # Use palette base color for neutral background
        base = self.palette().color(QtGui.QPalette.Base)
        _draw_editor_background(ctx, w_px, h_px, (base.redF(), base.greenF(), base.blueF()))
        # Draw all element drawers if an editor and score are available
        if self._editor is not None:
            score = self._editor.current_score()
            if score is not None:
                for drawer in get_all_drawers():
                    drawer.draw(ctx, score)
        image.setDevicePixelRatio(dpr)
        painter = QtGui.QPainter(self)
        painter.drawImage(0, 0, image)
        painter.end()

    def mousePressEvent(self, ev: QtGui.QMouseEvent) -> None:
        self._last_pos = ev.position()
        if self._editor:
            if ev.button() == QtCore.Qt.MouseButton.LeftButton:
                self._editor.mouse_press(1, ev.position().x(), ev.position().y())
            elif ev.button() == QtCore.Qt.MouseButton.RightButton:
                self._editor.mouse_press(2, ev.position().x(), ev.position().y())
        super().mousePressEvent(ev)

    def mouseMoveEvent(self, ev: QtGui.QMouseEvent) -> None:
        if self._editor:
            lp = self._last_pos or ev.position()
            dx = ev.position().x() - lp.x()
            dy = ev.position().y() - lp.y()
            self._editor.mouse_move(ev.position().x(), ev.position().y(), dx, dy)
        self._last_pos = ev.position()
        super().mouseMoveEvent(ev)

    def mouseReleaseEvent(self, ev: QtGui.QMouseEvent) -> None:
        if self._editor:
            if ev.button() == QtCore.Qt.MouseButton.LeftButton:
                self._editor.mouse_release(1, ev.position().x(), ev.position().y())
            elif ev.button() == QtCore.Qt.MouseButton.RightButton:
                self._editor.mouse_release(2, ev.position().x(), ev.position().y())
        super().mouseReleaseEvent(ev)

    def mouseDoubleClickEvent(self, ev: QtGui.QMouseEvent) -> None:
        if self._editor:
            if ev.button() == QtCore.Qt.MouseButton.LeftButton:
                self._editor.mouse_double_click(1, ev.position().x(), ev.position().y())
            elif ev.button() == QtCore.Qt.MouseButton.RightButton:
                self._editor.mouse_double_click(2, ev.position().x(), ev.position().y())
        super().mouseDoubleClickEvent(ev)
