from __future__ import annotations
from PySide6 import QtCore, QtGui, QtWidgets
import cairo
from ui.widgets.draw_util import DrawUtil
from ui.style import Style
from utils.CONSTANT import ENGRAVER_LAYERING
from engraver.engraver import do_engrave


def _make_image_and_surface(width: int, height: int):
    width = max(1, int(width))
    height = max(1, int(height))
    stride = width * 4
    buf = bytearray(height * stride)
    surface = cairo.ImageSurface.create_for_data(buf, cairo.FORMAT_ARGB32, width, height, stride)
    image = QtGui.QImage(buf, width, height, stride, QtGui.QImage.Format.Format_ARGB32_Premultiplied)
    return image, surface, buf


class RenderEmitter(QtCore.QObject):
    rendered = QtCore.Signal(QtGui.QImage, int)


class RenderTask(QtCore.QRunnable):
    def __init__(self, draw_util: DrawUtil, w_px: int, h_px: int, px_per_mm: float, dpr: float, page_index: int, emitter: RenderEmitter, score: dict | None = None, perform_engrave: bool = False):
        super().__init__()
        self.setAutoDelete(True)
        self._du = draw_util
        self._w_px = w_px
        self._h_px = h_px
        self._px_per_mm = px_per_mm
        self._dpr = dpr
        self._page_index = page_index
        self._emitter = emitter
        self._score = score
        self._perform_engrave = perform_engrave

    def run(self) -> None:
        # Optionally run engraving to update DrawUtil from score before rendering.
        if self._perform_engrave and self._score is not None:
            try:
                do_engrave(self._score, self._du)
            except Exception as e:
                # Fail engraving silently for now; could emit an error signal if desired.
                print(f"Engrave error: {e}")
        image, surface, _buf = _make_image_and_surface(self._w_px, self._h_px)
        ctx = cairo.Context(surface)
        self._du.render_to_cairo(ctx, self._page_index, self._px_per_mm, layering=ENGRAVER_LAYERING)
        image.setDevicePixelRatio(self._dpr)
        # Emit back to the UI thread
        self._emitter.rendered.emit(image.copy(), self._page_index)


class DrawUtilView(QtWidgets.QWidget):
    def __init__(self, draw_util: DrawUtil, parent=None):
        super().__init__(parent)
        self._du = draw_util
        self._image: QtGui.QImage | None = None
        self._page_index = max(0, self._du.current_page_index())
        self._pool = QtCore.QThreadPool.globalInstance()
        self._emitter = RenderEmitter()
        self._emitter.rendered.connect(self._on_rendered)
        # Allow splitter to fully collapse this view
        self.setMinimumWidth(0)
        self._last_px_per_mm: float = 1.0  # device px per mm
        self._last_widget_px_per_mm: float = 1.0  # widget px per mm
        self._last_dpr: float = 1.0
        self._last_h_px: int = 0
        self._scroll_px: float = 0.0
        self._score: dict | None = None
        self._page_prev_cb = None
        self._page_next_cb = None
        # Apply a dedicated background color for DrawUtil views
        try:
            color = Style.get_named_qcolor('draw_util')
            pal = self.palette()
            pal.setColor(QtGui.QPalette.Window, color)
            self.setPalette(pal)
            self.setAutoFillBackground(True)
        except Exception:
            pass

    def set_page(self, index: int):
        self._page_index = index
        self._scroll_px = 0.0
        self.request_render()

    def set_page_turn_callbacks(self, prev_cb, next_cb) -> None:
        self._page_prev_cb = prev_cb
        self._page_next_cb = next_cb

    def sizeHint(self) -> QtCore.QSize:
        return QtCore.QSize(600, 800)

    @QtCore.Slot()
    def request_render(self):
        w = max(1, self.width())
        dpr = float(self.devicePixelRatioF())
        page_count = self._du.page_count()
        if page_count <= 0:
            return
        if self._page_index >= page_count:
            self._page_index = max(0, page_count - 1)
        page_w_mm, page_h_mm = self._du.current_page_size_mm()
        if page_w_mm <= 0 or page_h_mm <= 0:
            return
        px_per_mm = (w * dpr) / page_w_mm
        h_px = int(page_h_mm * px_per_mm)
        w_px = int(w * dpr)
        # Store metrics for hit-testing
        self._last_px_per_mm = px_per_mm
        self._last_widget_px_per_mm = (w) / page_w_mm
        self._last_dpr = dpr
        self._last_h_px = h_px
        task = RenderTask(self._du, w_px, h_px, px_per_mm, dpr, self._page_index, self._emitter, self._score, False)
        self._pool.start(task)

    @QtCore.Slot()
    def request_engrave_and_render(self):
        """Deprecated: engraving is managed by Engraver. Kept for compatibility."""
        self.request_render()

    def resizeEvent(self, ev: QtGui.QResizeEvent) -> None:
        super().resizeEvent(ev)
        self.request_render()

    def paintEvent(self, ev: QtGui.QPaintEvent) -> None:
        painter = QtGui.QPainter(self)
        if self._image is not None:
            x = 0
            img_h = int(self._image.height() / self._image.devicePixelRatio())
            if img_h <= self.height():
                y = (self.height() - img_h) // 2
            else:
                max_scroll = max(0, img_h - self.height())
                self._scroll_px = max(0.0, min(float(max_scroll), float(self._scroll_px)))
                y = -int(round(self._scroll_px))
            painter.drawImage(QtCore.QPoint(x, y), self._image)
        painter.end()

    def wheelEvent(self, ev: QtGui.QWheelEvent) -> None:
        if self._image is None:
            return
        img_h = int(self._image.height() / self._image.devicePixelRatio())
        if img_h <= self.height():
            return
        delta = ev.pixelDelta().y()
        if delta == 0:
            delta = ev.angleDelta().y() / 2
        if delta == 0:
            return
        max_scroll = max(0, img_h - self.height())
        self._scroll_px = max(0.0, min(float(max_scroll), float(self._scroll_px - delta)))
        self.update()
        ev.accept()

    def mousePressEvent(self, ev: QtGui.QMouseEvent) -> None:
        if ev.button() == QtCore.Qt.MouseButton.LeftButton and callable(self._page_prev_cb):
            self._page_prev_cb()
            return
        if ev.button() == QtCore.Qt.MouseButton.RightButton and callable(self._page_next_cb):
            self._page_next_cb()
            return
        if self._image is None:
            return
        # Convert from widget px to page mm
        img_h = int(self._image.height() / self._last_dpr)
        if img_h <= self.height():
            y_offset_px = (self.height() - img_h) // 2
        else:
            y_offset_px = -int(round(self._scroll_px))
        x_px = ev.position().x()
        y_px = ev.position().y() - y_offset_px
        if y_px < 0 or y_px > (self._last_h_px / self._last_dpr) or x_px < 0:
            return
        # Use widget px per mm for conversion (since event positions are in widget px)
        x_mm = float(x_px) / self._last_widget_px_per_mm
        y_mm = float(y_px) / self._last_widget_px_per_mm
        hit = self._du.hit_test_point_mm(x_mm, y_mm, self._page_index)
        if hit is not None:
            # Simple console feedback for now
            hit_id = getattr(hit, "id", 0)
            hit_tags = getattr(hit, "tags", [])
            hit_rect = getattr(hit, "hit_rect_mm", None)
            print(f"Hit: type={type(hit).__name__} id={hit_id} tags={hit_tags} rect_mm={hit_rect}")
        else:
            print("Hit: none")

    def document_changed(self) -> None:
        # Convenience for callers after mutating the DrawUtil
        self.request_render()

    def set_score(self, score: dict | None) -> None:
        self._score = score
        # Reflect paper size from file model layout into DrawUtil
        try:
            layout = (score or {}).get('layout', {}) or {}
            w_mm = float(layout.get('page_width_mm', 0.0) or 0.0)
            h_mm = float(layout.get('page_height_mm', 0.0) or 0.0)
            if w_mm > 0 and h_mm > 0:
                self._du.set_current_page_size_mm(w_mm, h_mm)
                # Trigger rerender with new dimensions
                self.request_render()
        except Exception:
            pass

    @QtCore.Slot(QtGui.QImage, int)
    def _on_rendered(self, image: QtGui.QImage, page_index: int):
        if page_index != self._page_index:
            return
        self._image = image
        self.update()

    def closeEvent(self, ev: QtGui.QCloseEvent) -> None:
        # No persistent threads; nothing special to stop.
        super().closeEvent(ev)

    def shutdown(self) -> None:
        # Using QThreadPool tasks that finish automatically; nothing to do.
        pass
