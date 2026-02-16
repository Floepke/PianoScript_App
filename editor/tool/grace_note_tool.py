from typing import Optional
from editor.tool.base_tool import BaseTool
from file_model.SCORE import SCORE


class GraceNoteTool(BaseTool):
    TOOL_NAME = 'grace_note'

    def toolbar_spec(self) -> list[dict]:
        return []

    def _score(self) -> Optional[SCORE]:
        try:
            return self._editor.current_score()
        except Exception:
            return None

    def _add_grace_note(self, x: float, y: float) -> None:
        score = self._score()
        if score is None:
            return
        t_raw = float(self._editor.y_to_time(y))
        t_snap = float(self._editor.snap_time(t_raw))
        pitch = int(self._editor.x_to_pitch(x))
        score.new_grace_note(pitch=pitch, time=t_snap)
        try:
            self._editor._snapshot_if_changed(coalesce=True, label='grace_note_add')
        except Exception:
            pass
        try:
            self._editor.force_redraw_from_model()
        except Exception:
            self._editor.draw_frame()

    def _delete_grace_note(self, x: float, y: float) -> None:
        score = self._score()
        if score is None:
            return
        target = None
        hit_id = None
        hit_test = getattr(self._editor, 'hit_test_note_id', None)
        if callable(hit_test):
            hit_id = hit_test(x, y)
        if hit_id is not None:
            for g in getattr(score.events, 'grace_note', []) or []:
                if int(getattr(g, '_id', -1) or -1) == int(hit_id):
                    target = g
                    break
        if target is None:
            return
        lst = getattr(score.events, 'grace_note', None)
        if isinstance(lst, list):
            try:
                lst.remove(target)
            except ValueError:
                tid = int(getattr(target, '_id', -2) or -2)
                score.events.grace_note = [m for m in lst if int(getattr(m, '_id', -2) or -2) != tid]
        try:
            self._editor._snapshot_if_changed(coalesce=True, label='grace_note_delete')
        except Exception:
            pass
        try:
            self._editor.force_redraw_from_model()
        except Exception:
            self._editor.draw_frame()

    def on_left_click(self, x: float, y: float) -> None:
        super().on_left_click(x, y)
        self._add_grace_note(x, y)

    def on_right_click(self, x: float, y: float) -> None:
        super().on_right_click(x, y)
        self._delete_grace_note(x, y)
