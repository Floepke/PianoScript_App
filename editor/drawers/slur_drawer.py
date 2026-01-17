from __future__ import annotations
from typing import Any
from ui.widgets.draw_util import DrawUtil
from editor.editor import Editor
from .base import DrawerBase


class SlurDrawer(DrawerBase):
    def draw(self, du: DrawUtil, score: Any, editor: Editor) -> None:
        self.setup_context(du, score, editor)
        
        ... # Implementation for drawing slur elements would go here
