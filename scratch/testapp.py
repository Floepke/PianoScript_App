from __future__ import annotations
from PySide6 import QtCore, QtGui, QtWidgets
import cairo
import os

import sys, os
# Ensure project root is on sys.path so 'scratch' package resolves
ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
from scratch.drawutil.drawutil import DrawUtil


def _make_image_and_surface(width: int, height: int):
    width = max(1, int(width))
    height = max(1, int(height))
    stride = width * 4
    buf = bytearray(height * stride)
    surface = cairo.ImageSurface.create_for_data(buf, cairo.FORMAT_ARGB32, width, height, stride)
    image = QtGui.QImage(buf, width, height, stride, QtGui.QImage.Format.Format_ARGB32_Premultiplied)
    return image, surface, buf


class DrawViewportWidget(QtWidgets.QWidget):
    """Viewport widget that renders a long drawing in mm with a static viewport.

    - Scales horizontally to fit widget width (px_per_mm = widget_px / width_mm)
    - Uses a vertical scrollbar from parent QScrollArea
    - Renders only the viewport region with explicit per-line clipping
    """

    viewportMetricsChanged = QtCore.Signal(int, int, float, float)  # content_px, viewport_px, px_per_mm, dpr

    def __init__(self, du: DrawUtil, parent=None):
        super().__init__(parent)
        self._du = du
        self.setMinimumWidth(0)
        self.setMouseTracking(True)
        self._debug_viewport = os.getenv('DEBUG_VIEWPORT', '0') in ('1', 'true', 'True')
        # Logical-pixel inset for an inner viewport (DEBUG aid)
        try:
            self._vp_inset_logical: int = int(os.getenv('VP_INSET', '40'))
        except Exception:
            self._vp_inset_logical = 40
        self._last_px_per_mm: float = 1.0
        self._last_dpr: float = 1.0
        self._scroll_device_px: int = 0
        self._single_step_px: int = 40

    def set_scroll_device_px(self, value: int):
        self._scroll_device_px = max(0, int(value))
        self.update()

    def sizeHint(self) -> QtCore.QSize:
        return QtCore.QSize(800, 600)

    def paintEvent(self, ev: QtGui.QPaintEvent) -> None:
        painter = QtGui.QPainter(self)
        painter.fillRect(self.rect(), QtGui.QColor('#7a7a7a'))
        dpr = float(self.devicePixelRatioF())
        vp_w = self.width()
        vp_h = self.height()
        w_px = int(max(1, vp_w * dpr))
        h_px = int(max(1, vp_h * dpr))
        inset_logical = max(0, int(self._vp_inset_logical))
        inset_device = int(inset_logical * dpr)
        inner_w_px = max(1, w_px - 2 * inset_device)
        inner_h_px = max(1, h_px - 2 * inset_device)

        draw_w_mm, draw_h_mm = self._du.drawing_size_mm()
        if draw_w_mm <= 0 or draw_h_mm <= 0:
            painter.end()
            return
        # IMPORTANT: Use the actual inner viewport width for consistent scaling
        px_per_mm = inner_w_px / draw_w_mm
        self._last_px_per_mm = px_per_mm
        self._last_dpr = dpr
        content_h_px = int(draw_h_mm * px_per_mm)  # device px, matches inner viewport scaling
        # Emit metrics so the host can update scrollbar range and steps
        try:
            self.viewportMetricsChanged.emit(content_h_px, h_px, px_per_mm, dpr)
        except Exception:
            pass

        # Use px clip directly (no mm conversions)
        clip_x_px = 0
        # Convert scrollbar value (logical px) to device px for rendering
        clip_y_px = int((self._scroll_device_px * dpr))
        # Diagnostics: print viewport + clip metrics
        if os.getenv('DEBUG_CLIP', '0') in ('1', 'true', 'True'):
            try:
                print(f"[Viewport] vp_w={vp_w} vp_h={vp_h} dpr={dpr:.2f} w_px={w_px} h_px={h_px} inner_w_px={inner_w_px} inner_h_px={inner_h_px} inset_logical={inset_logical} scroll_logical={self._scroll_device_px} clip_y_px={clip_y_px} px_per_mm={px_per_mm:.4f}")
            except Exception:
                pass
        # Use inner viewport dimensions for clipping
        clip_w_px = inner_w_px
        clip_h_px = inner_h_px

        # Render only the inner viewport to an offscreen image of the same size
        image, surface, _buf = _make_image_and_surface(inner_w_px, inner_h_px)
        ctx = cairo.Context(surface)
        # White page background for clarity
        ctx.set_source_rgb(1, 1, 1)
        ctx.paint()
        # Render exactly the viewport region with explicit px clipping
        self._du.render_viewport_px(ctx, px_per_mm, (clip_x_px, clip_y_px, clip_w_px, clip_h_px))
        image.setDevicePixelRatio(dpr)
        # Draw into the inner viewport rectangle (logical px)
        dest_rect = QtCore.QRectF(float(inset_logical), float(inset_logical),
                                  float(vp_w - 2 * inset_logical), float(vp_h - 2 * inset_logical))
        painter.drawImage(dest_rect, image)

        if self._debug_viewport:
            pen = QtGui.QPen(QtGui.QColor(220, 40, 40))
            pen.setWidth(1)
            painter.setPen(pen)
            painter.setBrush(QtGui.QBrush())
            # Border around inner viewport
            painter.drawRect(QtCore.QRectF(float(inset_logical) + 0.5, float(inset_logical) + 0.5,
                                           float(vp_w - 2 * inset_logical) - 1.0,
                                           float(vp_h - 2 * inset_logical) - 1.0))
            # Overlay text with key metrics (logical px)
            painter.setPen(QtGui.QPen(QtGui.QColor(30, 30, 30)))
            font = painter.font()
            font.setPointSize(10)
            painter.setFont(font)
            overlay = f"vp_h={vp_h} h_px={h_px} inner_h_px={inner_h_px} inset_logical={inset_logical} dpr={dpr:.2f} scroll_logical={self._scroll_device_px} clip_y_px={clip_y_px}"
            painter.drawText(10, 18, overlay)

        painter.end()

    def wheelEvent(self, ev: QtGui.QWheelEvent) -> None:
        # Custom wheel scrolling: move the scroll position without moving the viewport widget
        delta_y = ev.angleDelta().y()  # positive = up
        direction = -1 if delta_y > 0 else 1
        step_px = max(1, int(self._single_step_px))
        self._scroll_device_px = max(0, self._scroll_device_px + direction * step_px)
        self.update()


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('DrawUtil Test App')
        self.resize(1200, 800)
        du = self._build_demo_drawutil()

        # Static viewport + external scrollbar
        central = QtWidgets.QWidget()
        layout = QtWidgets.QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.canvas = DrawViewportWidget(du)
        self.vscroll = QtWidgets.QScrollBar(QtCore.Qt.Orientation.Vertical)
        layout.addWidget(self.canvas, stretch=1)
        layout.addWidget(self.vscroll, stretch=0)
        self.setCentralWidget(central)

        # Connect metrics to update the scrollbar range
        self.canvas.viewportMetricsChanged.connect(self._on_viewport_metrics)
        self.vscroll.valueChanged.connect(self._on_scroll_changed)
        QtCore.QTimer.singleShot(0, self.canvas.update)

    def _build_demo_drawutil(self) -> DrawUtil:
        drawing_height_mm = 200.0

        du = DrawUtil()
        # A long timeline: 210mm wide, 5000mm tall
        du.set_drawing_size_mm(210.0, drawing_height_mm)
        # Vertical barlines: every 10mm, thicker every 50mm
        for x in range(0, 211, 10):
            color = (0.2, 0.2, 0.25, 1.0)
            width = 0.15
            if x % 50 == 0:
                color = (0.1, 0.1, 0.15, 1.0)
                width = 0.3
            du.add_line(float(x), 0.0, float(x), drawing_height_mm, color=color, width_mm=width, tags=['barline'])
        # Horizontal guide every 100mm
        for y in range(0, int(drawing_height_mm) + 1, 100):
            du.add_line(0.0, float(y), 210.0, float(y), color=(0.5, 0.5, 0.6, 0.5), width_mm=0.1, tags=['guide'])
        # Labels every 250mm
        for i, y in enumerate(range(0, int(drawing_height_mm) + 1, 250)):
            du.add_text(5.0, float(y) + 5.0, f"t={y}mm", size_pt=12, color=(0.1, 0.1, 0.1, 1.0))
        # Sample rectangles spanning viewport
        for i, y in enumerate(range(50, 450, 100)):
            du.add_rectangle(30.0, float(y), 50.0, 80.0, stroke_color=(0.2, 0.2, 0.2, 1.0), stroke_width_mm=0.2,
                             fill_color=(0.2, 0.7, 0.3, 0.2))
        return du

    @QtCore.Slot(int, int, float, float)
    def _on_viewport_metrics(self, content_px: int, viewport_px: int, px_per_mm: float, dpr: float):
        # QScrollBar works in logical pixels; metrics provided are device pixels.
        scale = max(1.0, dpr)
        max_scroll = max(0, int(round((content_px - viewport_px) / scale)))
        self.vscroll.setRange(0, max_scroll)
        # Page step ~ 80% of viewport height (logical px)
        self.vscroll.setPageStep(int(max(1, round(0.8 * viewport_px / scale))))
        # Single step ~ 40mm in logical pixels
        single_step_px = int(max(1, round(40.0 * (px_per_mm / scale))))
        self.vscroll.setSingleStep(single_step_px)
        # Also update canvas wheel step (logical px)
        self.canvas._single_step_px = single_step_px

    @QtCore.Slot(int)
    def _on_scroll_changed(self, value: int):
        self.canvas.set_scroll_device_px(value)


def main():
    app = QtWidgets.QApplication([])
    w = MainWindow()
    w.show()
    app.exec()


if __name__ == '__main__':
    main()
