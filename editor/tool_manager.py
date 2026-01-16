from __future__ import annotations
from typing import Optional
from PySide6 import QtCore
from icons.icons import get_qicon
from ui.widgets.toolbar_splitter import ToolbarSplitter


class ToolManager(QtCore.QObject):
    """Manage the active tool and its contextual toolbar in the splitter."""

    toolChanged = QtCore.Signal(str)

    def __init__(self, splitter: ToolbarSplitter):
        super().__init__()
        self._splitter = splitter
        self._tool = None
        try:
            self._splitter.contextButtonClicked.connect(self._on_context_button_clicked)
        except Exception:
            pass

    def set_tool(self, tool) -> None:
        self._tool = tool
        # Build contextual toolbar from tool.toolbar_spec()
        defs = []
        try:
            defs = tool.toolbar_spec() or []
        except Exception:
            defs = []
        try:
            self._splitter.set_context_buttons(defs)
        except Exception:
            pass
        name = getattr(tool, 'TOOL_NAME', 'unknown')
        self.toolChanged.emit(str(name))

    def _on_context_button_clicked(self, name: str) -> None:
        try:
            if self._tool is not None:
                self._tool.on_toolbar_button(name)
        except Exception:
            pass
