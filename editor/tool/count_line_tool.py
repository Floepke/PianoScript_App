from editor.tool.base_tool import BaseTool
from file_model.SCORE import SCORE



class CountLineTool(BaseTool):
    TOOL_NAME = 'count_line'

    def __init__(self):
        super().__init__()
        self._active_line = None
        self._active_handle: str | None = None  # 'start', 'end', or 'line'

    def toolbar_spec(self) -> list[dict]:
        return []

    def on_left_press(self, x: float, y: float) -> None:
        super().on_left_press(x, y)
        if self._editor is None:
            return
        score: SCORE = self._editor.current_score()
        if score is None:
            return

        # Convert mouse to mm for hit testing
        w_px_per_mm = float(getattr(self._editor, '_widget_px_per_mm', 1.0) or 1.0)
        x_mm = float(x) / max(1e-6, w_px_per_mm)
        y_mm = float(y) / max(1e-6, w_px_per_mm) + float(getattr(self._editor, '_view_y_mm_offset', 0.0) or 0.0)

        # Hit test handles
        handle_w = max(1.5, float(getattr(self._editor, 'semitone_dist', 2.5) or 2.5) * 0.6)
        handle_h = handle_w
        hit = None
        hit_handle = None
        for ev in list(getattr(score.events, 'count_line', []) or []):
            try:
                t0 = float(getattr(ev, 'time', 0.0) or 0.0)
                p1 = int(getattr(ev, 'pitch1', 40) or 40)
                p2 = int(getattr(ev, 'pitch2', 44) or 44)
            except Exception:
                continue
            y_ev = float(self._editor.time_to_mm(t0))
            x1 = float(self._editor.pitch_to_x(p1))
            x2 = float(self._editor.pitch_to_x(p2))
            # Start handle rect
            if (x1 - handle_w * 0.5) <= x_mm <= (x1 + handle_w * 0.5) and (y_ev - handle_h * 0.5) <= y_mm <= (y_ev + handle_h * 0.5):
                hit = ev
                hit_handle = 'start'
                break
            # End handle rect
            if (x2 - handle_w * 0.5) <= x_mm <= (x2 + handle_w * 0.5) and (y_ev - handle_h * 0.5) <= y_mm <= (y_ev + handle_h * 0.5):
                hit = ev
                hit_handle = 'end'
                break

        if hit is not None:
            self._active_line = hit
            self._active_handle = hit_handle
            return

        # Create a new count line at the snapped time
        t_press_raw = float(self._editor.y_to_time(y))
        t_press_snap = float(self._editor.snap_time(t_press_raw))
        pitch_press = int(self._editor.x_to_pitch(x))
        p2 = max(1, min(88, pitch_press + 4))
        self._active_line = score.new_count_line(time=t_press_snap, pitch1=pitch_press, pitch2=p2)
        self._active_handle = 'end'
        if hasattr(self._editor, 'force_redraw_from_model'):
            self._editor.force_redraw_from_model()
        else:
            self._editor.draw_frame()
    def on_left_unpress(self, x: float, y: float) -> None:
        super().on_left_unpress(x, y)
        self._active_line = None
        self._active_handle = None
    def on_left_click(self, x: float, y: float) -> None:
        super().on_left_click(x, y)
        return
    def on_left_double_click(self, x: float, y: float) -> None:
        super().on_left_double_click(x, y)
        print('CountLineTool: on_left_double_click()')
    def on_left_drag_start(self, x: float, y: float) -> None:
        super().on_left_drag_start(x, y)
        return
    def on_left_drag(self, x: float, y: float, dx: float, dy: float) -> None:
        super().on_left_drag(x, y, dx, dy)
        if self._editor is None or self._active_line is None:
            return
        # Update time from y
        t_raw = float(self._editor.y_to_time(y))
        t_snap = float(self._editor.snap_time(t_raw))
        try:
            self._active_line.time = float(t_snap)
        except Exception:
            pass

        # Update pitch for active handle
        pitch = int(self._editor.x_to_pitch(x))
        pitch = max(1, min(88, pitch))
        if self._active_handle == 'start':
            try:
                self._active_line.pitch1 = int(pitch)
            except Exception:
                pass
        elif self._active_handle == 'end':
            try:
                self._active_line.pitch2 = int(pitch)
            except Exception:
                pass
        if hasattr(self._editor, 'force_redraw_from_model'):
            self._editor.force_redraw_from_model()
        else:
            self._editor.draw_frame()
    def on_left_drag_end(self, x: float, y: float) -> None:
        super().on_left_drag_end(x, y)
        self._active_line = None
        self._active_handle = None
    def on_right_press(self, x: float, y: float) -> None:
        super().on_right_press(x, y)
        print('CountLineTool: on_right_press()')
    def on_right_unpress(self, x: float, y: float) -> None:
        super().on_right_unpress(x, y)
        print('CountLineTool: on_right_unpress()')
    def on_right_click(self, x: float, y: float) -> None:
        super().on_right_click(x, y)
        if self._editor is None:
            return
        score: SCORE = self._editor.current_score()
        if score is None:
            return

        # Delete nearest handle if clicked on it
        w_px_per_mm = float(getattr(self._editor, '_widget_px_per_mm', 1.0) or 1.0)
        x_mm = float(x) / max(1e-6, w_px_per_mm)
        y_mm = float(y) / max(1e-6, w_px_per_mm) + float(getattr(self._editor, '_view_y_mm_offset', 0.0) or 0.0)
        handle_w = max(1.5, float(getattr(self._editor, 'semitone_dist', 2.5) or 2.5) * 0.6)
        handle_h = handle_w

        lst = list(getattr(score.events, 'count_line', []) or [])
        for ev in lst:
            try:
                t0 = float(getattr(ev, 'time', 0.0) or 0.0)
                p1 = int(getattr(ev, 'pitch1', 40) or 40)
                p2 = int(getattr(ev, 'pitch2', 44) or 44)
            except Exception:
                continue
            y_ev = float(self._editor.time_to_mm(t0))
            x1 = float(self._editor.pitch_to_x(p1))
            x2 = float(self._editor.pitch_to_x(p2))
            if (x1 - handle_w * 0.5) <= x_mm <= (x1 + handle_w * 0.5) and (y_ev - handle_h * 0.5) <= y_mm <= (y_ev + handle_h * 0.5):
                lst.remove(ev)
                score.events.count_line = lst
                if hasattr(self._editor, 'force_redraw_from_model'):
                    self._editor.force_redraw_from_model()
                else:
                    self._editor.draw_frame()
                return
            if (x2 - handle_w * 0.5) <= x_mm <= (x2 + handle_w * 0.5) and (y_ev - handle_h * 0.5) <= y_mm <= (y_ev + handle_h * 0.5):
                lst.remove(ev)
                score.events.count_line = lst
                if hasattr(self._editor, 'force_redraw_from_model'):
                    self._editor.force_redraw_from_model()
                else:
                    self._editor.draw_frame()
                return
    def on_right_double_click(self, x: float, y: float) -> None:
        super().on_right_double_click(x, y)
        print('CountLineTool: on_right_double_click()')
    def on_right_drag_start(self, x: float, y: float) -> None:
        super().on_right_drag_start(x, y)
        print('CountLineTool: on_right_drag_start()')
    def on_right_drag(self, x: float, y: float, dx: float, dy: float) -> None:
        super().on_right_drag(x, y, dx, dy)
        print('CountLineTool: on_right_drag()')
    def on_right_drag_end(self, x: float, y: float) -> None:
        super().on_right_drag_end(x, y)
        print('CountLineTool: on_right_drag_end()')
    def on_mouse_move(self, x: float, y: float) -> None:
        super().on_mouse_move(x, y)
        # print('CountLineTool: on_mouse_move()')

    def on_toolbar_button(self, name: str) -> None:
        print(f"CountLineTool: on_toolbar_button(name='{name}')")
