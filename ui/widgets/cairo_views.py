from __future__ import annotations
from PySide6 import QtCore, QtGui, QtWidgets
import cairo
import math
from typing import Optional
from editor.editor import Editor
from editor.drawers import get_all_drawers
from ui.widgets.draw_util import DrawUtil


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
        self._du: DrawUtil | None = None
        self._last_px_per_mm: float = 1.0
        self._last_dpr: float = 1.0
        self._content_h_px: int = 0
        self._scroll_y_px: int = 0

    def set_editor(self, editor: Editor) -> None:
        self._editor = editor

    def set_tool(self, tool_name: str | None) -> None:
        self._current_tool = tool_name
        self.update()

    def paintEvent(self, ev: QtGui.QPaintEvent) -> None:
        sz = self.size()
        dpr = float(self.devicePixelRatioF())
        w_px = int(max(1, sz.width() * dpr))
        # Prepare DrawUtil with page dimensions from SCORE
        page_w_mm = 210.0
        page_h_mm = 297.0
        if self._editor is not None:
            sc = self._editor.current_score()
            if sc is not None:
                lay = getattr(sc, 'layout', None)
                if lay is not None:
                    page_w_mm = float(getattr(lay, 'page_width_mm', page_w_mm))
                    # Compute dynamic height from base_grid and editor zoom
                    ed = getattr(sc, 'editor', None)
                    zoom_mm_per_quarter = float(getattr(ed, 'zoom_mm_per_quarter', 5.0)) if ed else 5.0
                    total_mm = 0.0
                    bg_list = getattr(sc, 'base_grid', []) or []
                    for bg in bg_list:
                        num = float(getattr(bg, 'numerator', 4))
                        den = float(getattr(bg, 'denominator', 4))
                        measures = int(getattr(bg, 'measure_amount', 1))
                        quarters_per_measure = num * (4.0 / max(1.0, den))
                        total_mm += measures * quarters_per_measure * zoom_mm_per_quarter
                    # Include top/bottom margins
                    top_m = float(getattr(lay, 'page_top_margin_mm', 0.0))
                    bot_m = float(getattr(lay, 'page_bottom_margin_mm', 0.0))
                    page_h_mm = max(10.0, total_mm + top_m + bot_m)
        if self._du is None:
            self._du = DrawUtil()
        self._du.set_current_page_size_mm(page_w_mm, page_h_mm)
        # Scale to fit width: compute px_per_mm from current widget width
        px_per_mm = (w_px) / page_w_mm
        h_px_content = int(page_h_mm * px_per_mm)
        self._last_px_per_mm = px_per_mm
        self._last_dpr = dpr
        self._content_h_px = h_px_content
        # Update widget preferred height for scroll areas
        try:
            self.setMinimumHeight(int(h_px_content / max(1.0, dpr)))
        except Exception:
            pass
        # Compose page into an offscreen surface with full content height
        image, surface, _buf = _make_image_and_surface(w_px, max(1, h_px_content))
        ctx = cairo.Context(surface)
        ctx.set_antialias(cairo.ANTIALIAS_BEST)
        # Fill page background white
        ctx.save()
        ctx.scale(px_per_mm, px_per_mm)
        ctx.set_source_rgb(1, 1, 1)
        ctx.rectangle(0, 0, page_w_mm, page_h_mm)
        ctx.fill()
        ctx.restore()
        # Let drawers enqueue primitives in DrawUtil
        if self._editor is not None:
            score = self._editor.current_score()
            # Update editor layout metrics from current view width (mm)
            self._editor._calculate_layout(page_w_mm)
            if score is not None:
                for drawer in get_all_drawers():
                    drawer.draw(self._du, score, self._editor)
        # Render primitives to the Cairo surface
        self._du.render_to_cairo(ctx, page_index=self._du.current_page_index(), px_per_mm=px_per_mm)
        image.setDevicePixelRatio(dpr)
        # Paint onto the widget; the scroll area will clip/scroll naturally
        painter = QtGui.QPainter(self)
        base = self.palette().color(QtGui.QPalette.Base)
        painter.fillRect(self.rect(), base)
        painter.drawImage(QtCore.QPoint(0, 0), image)
        painter.end()

    def wheelEvent(self, ev: QtGui.QWheelEvent) -> None:
        # If embedded in a QScrollArea, let it handle scrolling naturally.
        super().wheelEvent(ev)

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
