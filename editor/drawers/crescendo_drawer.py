from __future__ import annotations
from typing import TYPE_CHECKING, cast
from ui.widgets.draw_util import DrawUtil

if TYPE_CHECKING:
    from editor.editor import Editor


class CrescendoDrawerMixin:
    def draw_crescendo(self, du: DrawUtil) -> None:
        self = cast("Editor", self)
        # Placeholder for crescendo drawing
        ...
