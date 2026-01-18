from editor.tool.base_tool import BaseTool


class NoteTool(BaseTool):
    TOOL_NAME = 'note'

    def toolbar_spec(self) -> list[dict]:
        return [
            {'name': 'note', 'icon': 'note', 'tooltip': 'Note tool'},
        ]

    # Debug event hooks
    def on_left_press(self, x: float, y: float) -> None: print('NoteTool: on_left_press()')
    def on_left_unpress(self, x: float, y: float) -> None: print('NoteTool: on_left_unpress()')
    def on_left_click(self, x: float, y: float) -> None: print('NoteTool: on_left_click()')
    def on_left_double_click(self, x: float, y: float) -> None: print('NoteTool: on_left_double_click()')
    def on_left_drag_start(self, x: float, y: float) -> None: print('NoteTool: on_left_drag_start()')
    def on_left_drag(self, x: float, y: float, dx: float, dy: float) -> None: print('NoteTool: on_left_drag()')
    def on_left_drag_end(self, x: float, y: float) -> None: print('NoteTool: on_left_drag_end()')
    def on_right_press(self, x: float, y: float) -> None: print('NoteTool: on_right_press()')
    def on_right_unpress(self, x: float, y: float) -> None: print('NoteTool: on_right_unpress()')
    def on_right_click(self, x: float, y: float) -> None: print('NoteTool: on_right_click()')
    def on_right_double_click(self, x: float, y: float) -> None: print('NoteTool: on_right_double_click()')
    def on_right_drag_start(self, x: float, y: float) -> None: print('NoteTool: on_right_drag_start()')
    def on_right_drag(self, x: float, y: float, dx: float, dy: float) -> None: print('NoteTool: on_right_drag()')
    def on_right_drag_end(self, x: float, y: float) -> None: print('NoteTool: on_right_drag_end()')
    def on_mouse_move(self, x: float, y: float) -> None: ...#print('NoteTool: on_mouse_move()')

    def on_toolbar_button(self, name: str) -> None:
        print(f"NoteTool: on_toolbar_button(name='{name}')")
