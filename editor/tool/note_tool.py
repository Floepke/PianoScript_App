from editor.tool.base_tool import BaseTool


class NoteTool(BaseTool):
    TOOL_NAME = 'note'

    def toolbar_spec(self) -> list[dict]:
        return [
            {'name': 'note', 'icon': 'note', 'tooltip': 'Note tool'},
        ]

    def on_left_press(self, x: float, y: float) -> None:
        super().on_left_press(x, y)

    def on_left_unpress(self, x: float, y: float) -> None:
        super().on_left_unpress(x, y)
        print('NoteTool: on_left_unpress()')

    def on_left_click(self, x: float, y: float) -> None:
        super().on_left_click(x, y)

    def on_left_double_click(self, x: float, y: float) -> None:
        super().on_left_double_click(x, y)

    def on_left_drag_start(self, x: float, y: float) -> None:
        super().on_left_drag_start(x, y)

    def on_left_drag(self, x: float, y: float, dx: float, dy: float) -> None:
        super().on_left_drag(x, y, dx, dy)

    def on_left_drag_end(self, x: float, y: float) -> None:
        super().on_left_drag_end(x, y)

    def on_right_press(self, x: float, y: float) -> None:
        super().on_right_press(x, y)

    def on_right_unpress(self, x: float, y: float) -> None:
        super().on_right_unpress(x, y)

    def on_right_click(self, x: float, y: float) -> None:
        super().on_right_click(x, y)

    def on_right_double_click(self, x: float, y: float) -> None:
        super().on_right_double_click(x, y)

    def on_right_drag_start(self, x: float, y: float) -> None:
        super().on_right_drag_start(x, y)

    def on_right_drag(self, x: float, y: float, dx: float, dy: float) -> None:
        super().on_right_drag(x, y, dx, dy)

    def on_right_drag_end(self, x: float, y: float) -> None:
        super().on_right_drag_end(x, y)

    def on_mouse_move(self, x: float, y: float) -> None:
        super().on_mouse_move(x, y)

    def on_toolbar_button(self, name: str) -> None:
        print(f"NoteTool: on_toolbar_button(name='{name}')")
