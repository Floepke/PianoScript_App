from editor.tool.base_tool import BaseTool


class DecrescendoTool(BaseTool):
    TOOL_NAME = 'decrescendo'

    def toolbar_spec(self) -> list[dict]:
        return [
            {'name': 'decrescendo', 'icon': 'decrescendo', 'tooltip': 'Decrescendo tool'},
        ]

    def on_left_press(self, x: float, y: float) -> None:
        super().on_left_press(x, y)
        print('DecrescendoTool: on_left_press()')
    def on_left_unpress(self, x: float, y: float) -> None:
        super().on_left_unpress(x, y)
        print('DecrescendoTool: on_left_unpress()')
    def on_left_click(self, x: float, y: float) -> None:
        super().on_left_click(x, y)
        print('DecrescendoTool: on_left_click()')
    def on_left_double_click(self, x: float, y: float) -> None:
        super().on_left_double_click(x, y)
        print('DecrescendoTool: on_left_double_click()')
    def on_left_drag_start(self, x: float, y: float) -> None:
        super().on_left_drag_start(x, y)
        print('DecrescendoTool: on_left_drag_start()')
    def on_left_drag(self, x: float, y: float, dx: float, dy: float) -> None:
        super().on_left_drag(x, y, dx, dy)
        print('DecrescendoTool: on_left_drag()')
    def on_left_drag_end(self, x: float, y: float) -> None:
        super().on_left_drag_end(x, y)
        print('DecrescendoTool: on_left_drag_end()')
    def on_right_press(self, x: float, y: float) -> None:
        super().on_right_press(x, y)
        print('DecrescendoTool: on_right_press()')
    def on_right_unpress(self, x: float, y: float) -> None:
        super().on_right_unpress(x, y)
        print('DecrescendoTool: on_right_unpress()')
    def on_right_click(self, x: float, y: float) -> None:
        super().on_right_click(x, y)
        print('DecrescendoTool: on_right_click()')
    def on_right_double_click(self, x: float, y: float) -> None:
        super().on_right_double_click(x, y)
        print('DecrescendoTool: on_right_double_click()')
    def on_right_drag_start(self, x: float, y: float) -> None:
        super().on_right_drag_start(x, y)
        print('DecrescendoTool: on_right_drag_start()')
    def on_right_drag(self, x: float, y: float, dx: float, dy: float) -> None:
        super().on_right_drag(x, y, dx, dy)
        print('DecrescendoTool: on_right_drag()')
    def on_right_drag_end(self, x: float, y: float) -> None:
        super().on_right_drag_end(x, y)
        print('DecrescendoTool: on_right_drag_end()')
    def on_mouse_move(self, x: float, y: float) -> None:
        super().on_mouse_move(x, y)
        # print('DecrescendoTool: on_mouse_move()')

    def on_toolbar_button(self, name: str) -> None:
        print(f"DecrescendoTool: on_toolbar_button(name='{name}')")
