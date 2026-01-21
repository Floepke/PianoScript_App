import math
from typing import Optional
from editor.tool.base_tool import BaseTool
from file_model.SCORE import SCORE
from utils.operator import Operator
from ui.widgets.draw_util import DrawUtil


class NoteTool(BaseTool):
    TOOL_NAME = 'note'
    def __init__(self):
        super().__init__()
        # Currently edited/created note during a press/drag session
        self.edit_note = None
        self._hand: str = '<'

    def toolbar_spec(self) -> list[dict]:
        # Two explicit hand selectors for quick switching
        return [
            {'name': 'hand_left', 'icon': 'note_left', 'tooltip': 'Left hand (<)'},
            {'name': 'hand_right', 'icon': 'note_right', 'tooltip': 'Right hand (>)'},
        ]

    def on_left_press(self, x: float, y: float) -> None:
        super().on_left_press(x, y)
        # Detect existing note under cursor or create a new one, then enter edit mode
        if self._editor is None:
            return
        score: SCORE = self._editor.current_score()
        if score is None:
            return

        # Compute raw (non-snapped) time for detection and snapped for creation
        t_press_raw = float(self._editor.y_to_time(y))
        t_press_snap = float(self._editor.snap_time(t_press_raw))
        pitch_press = int(self._editor.x_to_pitch(x))
        self._hand = str(getattr(self._editor, 'hand_cursor', '<') or '<')

        # Prefer rectangle-based hit detection for precise clickable area
        found = None
        hit_id = None
        hit_test = getattr(self._editor, 'hit_test_note_id', None)
        if callable(hit_test):
            hit_id = hit_test(x, y)
        if hit_id is not None:
            for n in getattr(score.events, 'note', []) or []:
                if int(getattr(n, 'id', -1) or -1) == int(hit_id):
                    found = n
                    break

        if found:
            # Edit existing note
            self.edit_note = found
        else:
            # Create a new note at the snapped press time with minimum duration = snap size
            units = float(max(1e-6, getattr(self._editor, 'snap_size_units', 8.0)))
            self.edit_note = score.new_note(pitch=pitch_press, time=t_press_snap, duration=units, hand=self._hand)

        # Explicitly build a frame for immediate feedback (cache + hit rects)
        self._editor.draw_frame()

    def on_left_unpress(self, x: float, y: float) -> None:
        super().on_left_unpress(x, y)
        # Keep last edit and clear the session handle
        self.edit_note = None

    def on_left_click(self, x: float, y: float) -> None:
        super().on_left_click(x, y)
        # Click handled on press; avoid duplicate creation on release-click path
        return

    def on_left_double_click(self, x: float, y: float) -> None:
        super().on_left_double_click(x, y)

    def on_left_drag_start(self, x: float, y: float) -> None:
        super().on_left_drag_start(x, y)
        # Nothing to do; edit_note is established on press
        return

    def on_left_drag(self, x: float, y: float, dx: float, dy: float) -> None:
        super().on_left_drag(x, y, dx, dy)
        # Update the in-progress note based on current mouse
        if self.edit_note is None or self._editor is None:
            return
        
        # Get note being edited and current raw/snap time and pitch
        note = self.edit_note
        cur_t_raw = float(self._editor.y_to_time(y))
        cur_t_snap = float(self._editor.snap_time(cur_t_raw))
        cur_pitch = int(self._editor.x_to_pitch(x))

        # Update rules:
        # - If cursor is before or at note start + snap size: update only pitch
        # - If cursor is after start: update only duration (min snap size)
        start_t = float(getattr(note, 'time', 0.0) or 0.0)
        units = float(max(1e-6, getattr(self._editor, 'snap_size_units', 8.0)))
        if cur_t_raw <= start_t:
            # Pitch-only edit
            note.pitch = cur_pitch
        else:
            # Duration-only edit; snap using ceiling to next snap band from start
            if cur_t_raw < start_t + units:
                note.duration = units
            else:
                delta = max(0.0, float(cur_t_snap - start_t))
                steps = max(1, int(math.ceil(delta / max(1e-6, units))))
                note.duration = float(steps) * float(units) + units

    def on_left_drag_end(self, x: float, y: float) -> None:
        super().on_left_drag_end(x, y)
        # Finalize edit session
        self.edit_note = None

    def on_right_press(self, x: float, y: float) -> None:
        super().on_right_press(x, y)

    def on_right_unpress(self, x: float, y: float) -> None:
        super().on_right_unpress(x, y)

    def on_right_click(self, x: float, y: float) -> None:
        super().on_right_click(x, y)
        # Detect a note at click position; if found, delete and redraw
        if self._editor is None:
            return
        score: SCORE = self._editor.current_score()
        if score is None:
            return

        # Use rectangle hit detection for delete
        target = None
        hit_id = None
        hit_test = getattr(self._editor, 'hit_test_note_id', None)
        if callable(hit_test):
            hit_id = hit_test(x, y)
        if hit_id is not None:
            for n in getattr(score.events, 'note', []) or []:
                if int(getattr(n, 'id', -1) or -1) == int(hit_id):
                    target = n
                    break

        if target is not None:
            notes_list = getattr(score.events, 'note', None)
            if isinstance(notes_list, list):
                if target in notes_list:
                    notes_list.remove(target)
                else:
                    tid = int(getattr(target, 'id', -1) or -1)
                    new_list = [m for m in notes_list if int(getattr(m, 'id', -2) or -2) != tid]
                    if len(new_list) != len(notes_list):
                        score.events.note = new_list
        # Explicitly build a frame for immediate feedback (cache + hit rects)
        self._editor.draw_frame()

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
        if self._editor is None:
            return
        if name == 'hand_left':
            self._editor.hand_cursor = '<'
        elif name == 'hand_right':
            self._editor.hand_cursor = '>'
        # Refresh overlay guides to reflect the change immediately
        if hasattr(self._editor, 'widget') and getattr(self._editor, 'widget', None) is not None:
            w = getattr(self._editor, 'widget')
            if hasattr(w, 'request_overlay_refresh'):
                w.request_overlay_refresh()
