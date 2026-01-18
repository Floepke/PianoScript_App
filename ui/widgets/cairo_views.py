from __future__ import annotations
from PySide6 import QtCore, QtGui, QtWidgets
import os
import cairo
import math
from typing import Optional
from editor.editor import Editor
from ui.widgets.draw_util import DrawUtil
from ui.style import Style
# Stripped renderer, tile cache, and spatial index for static viewport simplicity


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
    # Signal: inform container to adjust external scrollbar
    viewportMetricsChanged = QtCore.Signal(int, int, float, float)
    # Signal: emit logical pixel scroll value when wheel scrolling changes it
    scrollLogicalPxChanged = QtCore.Signal(int)
    def __init__(self, parent=None):
        super().__init__(parent)
        # Allow splitter to fully collapse this view
        self.setMinimumWidth(0)
        self.setMouseTracking(True)
        # Apply the dedicated DrawUtil background color to the editor widget, too
        try:
            color = Style.get_named_qcolor('editor')
            pal = self.palette()
            pal.setColor(QtGui.QPalette.Window, color)
            self.setPalette(pal)
            self.setAutoFillBackground(True)
        except Exception:
            pass
        self._current_tool: str | None = None
        self._editor: Optional[Editor] = None
        self._last_pos: QtCore.QPointF | None = None
        self._du: DrawUtil | None = None
        self._last_px_per_mm: float = 1.0
        self._last_dpr: float = 1.0
        self._content_h_px: int = 0
        # External scroll (logical px), controlled by an external QScrollBar
        self._scroll_logical_px: int = 0
        # Cached static layers for current viewport
        self._grid_cache_image: QtGui.QImage | None = None
        self._grid_cache_px_per_mm: float = 0.0
        self._grid_cache_dims_mm: tuple[float, float] = (0.0, 0.0)
        self._grid_cache_clip_mm: tuple[float, float, float, float] | None = None

        self._guides_cache_image: QtGui.QImage | None = None
        self._guides_cache_px_per_mm: float = 0.0
        self._guides_cache_dims_mm: tuple[float, float] = (0.0, 0.0)
        self._guides_cache_clip_mm: tuple[float, float, float, float] | None = None
        # Debug logging toggle (env: PIANOSCRIPT_DEBUG_SCROLL=1)
        self._debug_scroll: bool = os.getenv('PIANOSCRIPT_DEBUG_SCROLL', '0') in ('1', 'true', 'True')
        self._last_debug_key: tuple | None = None
        # Static viewport: no tiling/cache/renderer state
        self._last_cache_params: tuple[float, float, float] | None = None
        # (Signal defined at class level)

    def set_editor(self, editor: Editor) -> None:
        self._editor = editor

    def set_tool(self, tool_name: str | None) -> None:
        self._current_tool = tool_name
        self.update()

    def set_scroll_logical_px(self, value: int) -> None:
        """Set external logical pixel scroll offset and repaint."""
        self._scroll_logical_px = max(0, int(value))
        self.update()

    def paintEvent(self, ev: QtGui.QPaintEvent) -> None:
        # Use widget size as static viewport; do not rely on QScrollArea.
        vp = self
        dpr = float(self.devicePixelRatioF())
        vp_w = self.size().width()
        vp_h = self.size().height()
        w_px = int(max(1, vp_w * dpr))
        # Prepare DrawUtil with page dimensions from SCORE/layout and Editor layout
        page_w_mm = 210.0
        page_h_mm = 297.0
        if self._editor is not None:
            sc = self._editor.current_score()
            if sc is not None:
                lay = getattr(sc, 'layout', None)
                if lay is not None:
                    page_w_mm = float(getattr(lay, 'page_width_mm', page_w_mm))
            # Calculate editor layout metrics (margin, stave_width, editor_height)
            self._editor._calculate_layout(page_w_mm)
            try:
                page_h_mm = float(getattr(self._editor, 'editor_height', page_h_mm) or page_h_mm)
            except Exception:
                page_h_mm = page_h_mm
        # Invalidate cache when scale or page dimensions change
        px_per_mm = (w_px) / page_w_mm
        h_px_content = int(page_h_mm * px_per_mm)
        cache_params = (round(px_per_mm, 6), round(page_w_mm, 3), round(page_h_mm, 3))
        if self._last_cache_params is None or self._last_cache_params != cache_params:
            self._last_cache_params = cache_params

        # Always use fresh DrawUtils to avoid item accumulation
        self._last_px_per_mm = px_per_mm
        self._last_dpr = dpr
        self._content_h_px = h_px_content
        # Keep widget height independent from content to maintain a static viewport

        # Visible region equals viewport; use external scroll for offset (logical px)
        vis_w_px = max(1, int(vp_w * dpr))
        vis_h_px = max(1, int(vp_h * dpr))
        # No overscan/bleed: viewport is strictly the visible area.
        bleed_px = 0
        vis_h_px_bleed = vis_h_px
        scroll_val_px = int(self._scroll_logical_px)  # logical px
        # Compute clip rectangle in mm using device px per mm (honors zoom)
        clip_x_mm = 0.0
        clip_y_mm = float(scroll_val_px) * dpr / max(1e-6, px_per_mm)
        clip_w_mm = page_w_mm
        clip_h_mm = float(vp_h) * dpr / max(1e-6, px_per_mm)
        # No bleed: clip is exactly the viewport size in mm
        clip_y_mm_bleed = clip_y_mm
        clip_h_mm_bleed = float(vis_h_px_bleed) / max(1e-6, px_per_mm)

        # Debug logging (only when values change)
        if self._debug_scroll:
            dbg_key = (scroll_val_px, round(dpr, 3), round(px_per_mm, 6), int(vp_w), int(vp_h),
                       int(vis_w_px), int(vis_h_px), round(clip_y_mm, 3), round(clip_h_mm, 3))
            if dbg_key != self._last_debug_key:
                self._last_debug_key = dbg_key
                print(f"[ScrollDbg] scroll_px={scroll_val_px} dpr={dpr:.3f} px_per_mm={px_per_mm:.6f} "
                      f"vp=({vp_w}x{vp_h}) vis=({vis_w_px}x{vis_h_px}) clip_y_mm={clip_y_mm:.3f} clip_h_mm={clip_h_mm:.3f}")
        # Static viewport: tiling disabled and not used

        # Emit metrics so a container can configure an external scrollbar
        try:
            self.viewportMetricsChanged.emit(h_px_content, vis_h_px, px_per_mm, dpr)
        except Exception:
            pass

        painter = QtGui.QPainter(self)
        try:
            # Use the widget's palette/background; do not force a grey fill

            if self._editor is not None:
                # Layout was already calculated above to provide up-to-date editor_height
                pass

            # Build all layers once using the editor controller
            # Use a pure viewport clip rect (no bleed). Overscan is applied in DrawUtil for Cairo clip only.
            clip_mm = (clip_x_mm, clip_y_mm, clip_w_mm, clip_h_mm)
            du_all = DrawUtil()
            # Use the editor-provided height so scrolling matches drawer layout
            du_all.set_current_page_size_mm(page_w_mm, page_h_mm)
            if self._editor is not None:
                self._editor.draw_all(du_all)

            # Offscreen buffer sized exactly to the viewport
            img, surf, _buf = _make_image_and_surface(vis_w_px, vis_h_px)
            ctx = cairo.Context(surf)
            # Static viewport rendering: no overscan; draw items as-is with culling.
            du_all.render_to_cairo(ctx, du_all.current_page_index(), px_per_mm, clip_mm, overscan_mm=0.0)
            img.setDevicePixelRatio(dpr)
            painter.drawImage(QtCore.QRectF(0.0, 0.0, float(vp_w), float(vp_h)), img)

            # Optional viewport debug overlay: draw a red border around viewport
            if os.getenv('PIANOSCRIPT_DEBUG_VIEWPORT', '0') in ('1', 'true', 'True'):
                pen = QtGui.QPen(QtGui.QColor(220, 40, 40))
                pen.setWidth(1)
                painter.setPen(pen)
                painter.setBrush(QtGui.QBrush())
                painter.drawRect(QtCore.QRectF(0.5, 0.5, float(vp_w) - 1.0, float(vp_h) - 1.0))
        finally:
            painter.end()

    def wheelEvent(self, ev: QtGui.QWheelEvent) -> None:
        # Ctrl+Wheel: adjust vertical zoom via SCORE.editor.zoom_mm_per_quarter
        angle = ev.angleDelta().y()
        if angle == 0:
            ev.accept()
            return
        mods = ev.modifiers()
        try:
            ctrl_down = bool(mods & QtCore.Qt.KeyboardModifier.ControlModifier)
        except Exception:
            ctrl_down = False

        if ctrl_down and self._editor is not None:
            sc = self._editor.current_score()
            if sc is not None:
                ed = getattr(sc, 'editor', None)
                if ed is not None:
                    # Zoom multiplicative steps: ~10% per wheel notch
                    steps = int(round(angle / 120.0))
                    current = float(getattr(ed, 'zoom_mm_per_quarter', 5.0) or 5.0)
                    factor = (1.10 ** steps)
                    new_zoom = max(0.5, min(50.0, current * factor))
                    try:
                        ed.zoom_mm_per_quarter = float(new_zoom)
                    except Exception:
                        pass
                    # Repaint; metrics will be recomputed and emitted in paintEvent
                    self.update()
            ev.accept()
            return

        # Default: bounded wheel scrolling using external scrollbar semantics
        scale = max(1.0, float(self._last_dpr))
        step_logical_px = int(max(1, round(40.0 * (float(self._last_px_per_mm) / scale))))
        steps = int(round(angle / 120.0))
        delta = -steps * step_logical_px  # negative angle scrolls down visually
        new_val = max(0, int(self._scroll_logical_px + delta))
        vp_h_px = int(max(1, self.size().height() * scale))
        max_scroll = max(0, int(round((int(self._content_h_px) - vp_h_px) / scale)))
        if new_val > max_scroll:
            new_val = max_scroll
        if new_val != self._scroll_logical_px:
            self._scroll_logical_px = new_val
            self.scrollLogicalPxChanged.emit(new_val)
            self.update()
        ev.accept()

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
