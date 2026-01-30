from __future__ import annotations
from PySide6 import QtCore, QtWidgets
from typing import Optional
from editor.tool.base_tool import BaseTool
from utils.CONSTANT import QUARTER_NOTE_UNIT
from utils.operator import Operator


class TempoTool(BaseTool):
    TOOL_NAME = 'tempo'

    def __init__(self):
        super().__init__()
        self._active_tempo_id: Optional[int] = None
        self._active_time: Optional[float] = None
        self._min_duration: float = 0.0

    def toolbar_spec(self) -> list[dict]:
        return [
            {'name': 'tempo', 'icon': 'text', 'tooltip': 'Tempo tool'},
        ]

    def _find_active_ts_at_time(self, t: float) -> tuple[int, int]:
        """Return (numer, denom) for base grid segment active at time t."""
        if self._editor is None:
            return (4, 4)
        score = self._editor.current_score()
        cur_t = 0.0
        for bg in getattr(score, 'base_grid', []) or []:
            numer = int(getattr(bg, 'numerator', 4) or 4)
            denom = int(getattr(bg, 'denominator', 4) or 4)
            measure_len = float(numer) * (4.0 / float(denom)) * float(QUARTER_NOTE_UNIT)
            count = int(getattr(bg, 'measure_amount', 1) or 1)
            seg_len = float(count) * measure_len
            if t < cur_t + seg_len:
                return (numer, denom)
            cur_t += seg_len
        return (4, 4)

    def _beat_length_ticks(self, numer: int, denom: int) -> float:
        measure_len = float(numer) * (4.0 / float(denom)) * float(QUARTER_NOTE_UNIT)
        return measure_len / max(1, int(numer))

    def _find_tempo_at_time(self, t: float) -> Optional[object]:
        if self._editor is None:
            return None
        score = self._editor.current_score()
        op = Operator(threshold=1e-6)
        for ev in list(getattr(score.events, 'tempo', []) or []):
            if op.equal(float(getattr(ev, 'time', 0.0) or 0.0), float(t)):
                return ev
        return None

    def on_left_click(self, x: float, y: float) -> None:
        if self._editor is None:
            return
        score = self._editor.current_score()
        t = self._editor.snap_time(self._editor.y_to_time(y))
        # If clicked on existing, edit tempo value
        existing = self._find_tempo_at_time(t)
        if existing is not None:
            cur_tempo = int(getattr(existing, 'tempo', 60) or 60)
            dur = float(getattr(existing, 'duration', 0.0) or 0.0)
            ev_time = float(getattr(existing, 'time', 0.0) or 0.0)
            # Determine whether this is the earliest tempo
            lst = list(getattr(score.events, 'tempo', []) or [])
            earliest_time = min(float(getattr(ev, 'time', 0.0) or 0.0) for ev in lst) if lst else ev_time
            op = Operator(threshold=1e-6)
            is_earliest = op.equal(ev_time, earliest_time)
            # Compute minimum duration based on active time signature beat length
            numer, denom = self._find_active_ts_at_time(ev_time)
            min_du = self._beat_length_ticks(numer, denom)

            # Prepare parent and relax editor focus so the dialog receives mouse
            parent_w = None
            try:
                parent_w = QtWidgets.QApplication.activeWindow()
            except Exception:
                parent_w = None
            editor_widget = None
            prev_focus_policy = None
            try:
                from ui.widgets.cairo_views import CairoEditorWidget as _CEW
                if parent_w is not None:
                    editor_widget = parent_w.findChild(_CEW)
            except Exception:
                editor_widget = None
            try:
                if editor_widget is not None:
                    prev_focus_policy = int(editor_widget.focusPolicy())
                    editor_widget.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)
                    editor_widget.clearFocus()
                    editor_widget.releaseMouse()
            except Exception:
                pass

            # Build a small modal dialog for editing tempo (and duration for earliest)
            dlg = QtWidgets.QDialog(parent_w)
            dlg.setWindowTitle("Edit Tempo")
            try:
                dlg.setWindowModality(QtCore.Qt.ApplicationModal)
            except Exception:
                pass
            lay = QtWidgets.QFormLayout(dlg)
            lay.setContentsMargins(12, 12, 12, 12)
            lay.setSpacing(8)
            tempo_spin = QtWidgets.QSpinBox(dlg)
            tempo_spin.setRange(1, 1000)
            tempo_spin.setValue(cur_tempo)
            lay.addRow("Tempo (units/min):", tempo_spin)
            duration_spin = None
            if is_earliest:
                duration_spin = QtWidgets.QSpinBox(dlg)
                # Represent duration in ticks; enforce minimum beat length
                duration_spin.setRange(int(max(1, round(min_du))), 1000000)
                duration_spin.setValue(int(max(int(round(min_du)), int(round(dur)))))
                lay.addRow("Duration (ticks):", duration_spin)
            btns = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel, parent=dlg)
            lay.addRow(btns)
            try:
                ok_btn = btns.button(QtWidgets.QDialogButtonBox.Ok)
                if ok_btn is not None:
                    ok_btn.setDefault(True)
                    ok_btn.setAutoDefault(True)
                    ok_btn.setFocus()
            except Exception:
                pass

            try:
                dlg.raise_()
                dlg.activateWindow()
            except Exception:
                pass

            res = dlg.exec()
            try:
                if int(res) == int(QtWidgets.QDialog.Accepted):
                    # Update tempo
                    try:
                        existing.tempo = int(tempo_spin.value())
                    except Exception:
                        pass
                    # Update duration only for earliest marker; clamp to minimum
                    if duration_spin is not None:
                        try:
                            new_du = float(duration_spin.value())
                            existing.duration = max(float(min_du), float(new_du))
                        except Exception:
                            pass
                    self._editor._snapshot_if_changed(coalesce=True, label='tempo_edit')
                    self._editor.draw_frame()
            finally:
                # Restore editor focus policy
                try:
                    if editor_widget is not None:
                        fp = prev_focus_policy if prev_focus_policy is not None else int(QtCore.Qt.FocusPolicy.StrongFocus)
                        try:
                            editor_widget.setFocusPolicy(QtCore.Qt.FocusPolicy(fp))
                        except Exception:
                            editor_widget.setFocusPolicy(QtCore.Qt.FocusPolicy.StrongFocus)
                        editor_widget.setFocus()
                except Exception:
                    pass
            return
        # Create new tempo with minimum duration = one beat of active time signature
        numer, denom = self._find_active_ts_at_time(t)
        min_du = self._beat_length_ticks(numer, denom)
        tp = score.new_tempo(time=float(t), duration=float(min_du), tempo=60)
        self._active_tempo_id = int(getattr(tp, 'id', 0) or 0)
        self._active_time = float(t)
        self._min_duration = float(min_du)
        self._editor._snapshot_if_changed(coalesce=True, label='tempo_create')
        self._editor.draw_frame()

    def on_left_drag(self, x: float, y: float, dx: float, dy: float) -> None:
        if self._editor is None or self._active_tempo_id is None or self._active_time is None:
            return
        score = self._editor.current_score()
        t_cur = self._editor.snap_time(self._editor.y_to_time(y))
        new_du = max(self._min_duration, float(t_cur - float(self._active_time)))
        if new_du <= 0.0:
            new_du = self._min_duration
        for ev in list(getattr(score.events, 'tempo', []) or []):
            if int(getattr(ev, 'id', -1) or -1) == int(self._active_tempo_id):
                try:
                    ev.duration = float(new_du)
                except Exception:
                    pass
                break
        self._editor.draw_frame()

    def on_left_drag_end(self, x: float, y: float) -> None:
        if self._editor is None:
            return
        self._editor._snapshot_if_changed(coalesce=True, label='tempo_resize')
        self._active_tempo_id = None
        self._active_time = None

    def on_right_click(self, x: float, y: float) -> None:
        if self._editor is None:
            return
        score = self._editor.current_score()
        t = self._editor.snap_time(self._editor.y_to_time(y))
        op = Operator(threshold=1e-6)
        lst = list(getattr(score.events, 'tempo', []) or [])
        if not lst:
            return
        # Do not delete the first tempo marker (earliest time)
        earliest_time = min(float(getattr(ev, 'time', 0.0) or 0.0) for ev in lst)
        for i, ev in enumerate(lst):
            ev_time = float(getattr(ev, 'time', 0.0) or 0.0)
            if op.equal(ev_time, float(t)):
                # If this event is at the earliest time, skip deletion
                if op.equal(ev_time, earliest_time):
                    return
                try:
                    del lst[i]
                    score.events.tempo = lst
                except Exception:
                    pass
                self._editor._snapshot_if_changed(coalesce=True, label='tempo_delete')
                self._editor.draw_frame()
                return

    def on_mouse_move(self, x: float, y: float) -> None:
        super().on_mouse_move(x, y)
