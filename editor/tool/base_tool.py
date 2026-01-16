from __future__ import annotations
from typing import Optional


class BaseTool:
    """
    Base class for editor tools with convenient event hooks.
    Tools override methods they need; default implementations do nothing.
    """

    TOOL_NAME: str = "base"

    def __init__(self):
        # Optional: shared state across events
        self._active: bool = False

    # Lifecycle hooks
    def on_activate(self) -> None:
        """Called when this tool becomes the active tool."""
        self._active = True

    def on_deactivate(self) -> None:
        """Called when this tool is no longer the active tool."""
        self._active = False

    # Toolbar integration
    def toolbar_spec(self) -> list[dict]:
        """Return a list of button definitions: {'name','icon','tooltip'}"""
        return []

    def on_toolbar_button(self, name: str) -> None:
        pass

    # Mouse events
    def on_left_press(self, x: float, y: float) -> None: pass
    def on_left_unpress(self, x: float, y: float) -> None: pass
    def on_left_click(self, x: float, y: float) -> None: pass
    def on_left_double_click(self, x: float, y: float) -> None: pass

    def on_left_drag_start(self, x: float, y: float) -> None: pass
    def on_left_drag(self, x: float, y: float, dx: float, dy: float) -> None: pass
    def on_left_drag_end(self, x: float, y: float) -> None: pass

    def on_right_press(self, x: float, y: float) -> None: pass
    def on_right_unpress(self, x: float, y: float) -> None: pass
    def on_right_click(self, x: float, y: float) -> None: pass
    def on_right_double_click(self, x: float, y: float) -> None: pass

    def on_right_drag_start(self, x: float, y: float) -> None: pass
    def on_right_drag(self, x: float, y: float, dx: float, dy: float) -> None: pass
    def on_right_drag_end(self, x: float, y: float) -> None: pass

    def on_mouse_move(self, x: float, y: float) -> None: pass
