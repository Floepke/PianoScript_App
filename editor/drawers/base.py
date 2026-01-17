from __future__ import annotations
from typing import Any
from ui.widgets.draw_util import DrawUtil
from editor.editor import Editor


class EditorAccessMixin:
    """Mixin providing convenient access to shared editor-related helpers.

    Assumes subclasses will set `self._du`, `self._score`, and `self._editor`
    before use (via `setup_context`).
    """
    _du: DrawUtil | None = None
    _score: Any = None
    _editor: Editor | None = None

    def setup_context(self, du: DrawUtil, score: Any, editor: Editor) -> None:
        self._du = du
        self._score = score
        self._editor = editor

    # Shared helpers (expand as needed)
    def add_highlight_rect(self, x_mm: float, y_mm: float, w_mm: float, h_mm: float):
        if self._du is None:
            return
        self._du.add_rectangle(x_mm, y_mm, w_mm, h_mm,
                               stroke_color=(0.0, 0.5, 1.0, 1.0),
                               stroke_width_mm=0.3,
                               fill_color=(0.0, 0.5, 1.0, 0.08),
                               id=0, tags=["highlight"])

    def page_size_mm(self) -> tuple[float, float]:
        if self._du is None:
            return (210.0, 297.0)
        return self._du.current_page_size_mm()

    def draw_background_gray(self) -> None:
        """Draw a full-page background rectangle in print-view grey.

        This ensures the rendered image has the desired background,
        independent of QImage defaults.
        """
        if self._du is None:
            return
        w_mm, h_mm = self.page_size_mm()
        grey = (122/255.0, 122/255.0, 122/255.0, 1.0)  # #7a7a7a
        # Pure fill, no stroke
        self._du.add_rectangle(0.0, 0.0, w_mm, h_mm,
                               stroke_color=None,
                               fill_color=grey,
                               id=0,
                               tags=["background"])


class DrawerBase(EditorAccessMixin):
    """Base class for drawers. Subclass this for shared context and helpers."""
    def draw(self, du: DrawUtil, score: Any, editor: Editor) -> None:
        # Subclasses should override and call `setup_context` first.
        raise NotImplementedError
