from __future__ import annotations
from typing import Any
from ui.widgets.draw_util import DrawUtil
from editor.editor import Editor
from .base import DrawerBase


class TextDrawer(DrawerBase):
    def draw(self, du: DrawUtil, score: Any, editor: Editor) -> None:
        self.setup_context(du, score, editor)
        
        ... # Implementation for drawing text elements would go here
