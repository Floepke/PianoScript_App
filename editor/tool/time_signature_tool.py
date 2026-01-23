from __future__ import annotations
from typing import Optional
from editor.tool.base_tool import BaseTool
from file_model.SCORE import SCORE, BaseGrid
from utils.CONSTANT import QUARTER_NOTE_UNIT
from PySide6 import QtCore, QtWidgets

class TimeSignatureTool(BaseTool):
    TOOL_NAME = 'time_signature'

    def __init__(self):
        super().__init__()
        self._pending_bar_idx: Optional[int] = None
        self._pending_dialog: Optional[QtWidgets.QDialog] = None

    def toolbar_spec(self) -> list[dict]:
        return [
            {'name': 'time_signature', 'icon': 'time_signature', 'tooltip': 'Set Time Signature'},
        ]

    def on_left_click(self, x: float, y: float) -> None:
        super().on_left_click(x, y)
        if self._editor is None:
            return
        score: SCORE = self._editor.current_score()
        # Compute click time in ticks
        click_t = float(self._editor.y_to_time(y))
        # Find nearest barline index
        try:
            bars = []
            helper = getattr(self._editor, '_get_barline_positions', None)
            if callable(helper):
                bars = list(helper())
            else:
                cur_t = 0.0
                for bg in getattr(score, 'base_grid', []) or []:
                    measure_len = float(bg.numerator) * (4.0 / float(bg.denominator)) * float(QUARTER_NOTE_UNIT)
                    for _ in range(int(bg.measure_amount)):
                        bars.append(cur_t)
                        cur_t += measure_len
            if not bars:
                bars = [0.0]
            nearest_idx = 0
            min_abs = abs(click_t - float(bars[0]))
            for i, t in enumerate(bars):
                d = abs(click_t - float(t))
                if d < min_abs:
                    min_abs = d
                    nearest_idx = i
        except Exception:
            nearest_idx = 0

        # Defer dialog opening until after mouse release to avoid input grabs
        self._pending_bar_idx = int(nearest_idx)
        try:
            QtCore.QTimer.singleShot(0, self._open_time_signature_dialog)
        except Exception:
            # Fallback: open synchronously
            self._open_time_signature_dialog()

    def _open_time_signature_dialog(self) -> None:
        if self._editor is None:
            return
        # Determine a suitable parent (prefer MainWindow)
        parent_w = None
        try:
            splitter = getattr(getattr(self._editor, '_tm', None), '_splitter', None)
            if splitter is not None and hasattr(splitter, 'parent'):
                pw = splitter.parent()
                if pw is not None:
                    parent_w = pw
            if parent_w is None:
                parent_w = getattr(self._editor, 'widget', None)
        except Exception:
            parent_w = getattr(self._editor, 'widget', None)
        try:
            from ui.widgets.time_signature_dialog import TimeSignatureDialog
        except Exception:
            TimeSignatureDialog = None  # type: ignore
        if TimeSignatureDialog is None:
            return
        dlg = TimeSignatureDialog(parent=parent_w, initial_numer=4, initial_denom=4)
        try:
            dlg.setWindowModality(QtCore.Qt.WindowModal)
        except Exception:
            pass
        # Release mouse + clear focus so dialog receives clicks
        try:
            ed_w = getattr(self._editor, 'widget', None)
            if ed_w is not None:
                if hasattr(ed_w, 'releaseMouse'):
                    ed_w.releaseMouse()
                if hasattr(ed_w, 'clearFocus'):
                    ed_w.clearFocus()
        except Exception:
            pass
        # Show and use non-blocking open() with signal handlers
        try:
            dlg.show()
            dlg.raise_()
            dlg.activateWindow()
        except Exception:
            pass
        try:
            dlg.open()
        except Exception:
            # Fallback to exec if open() unavailable
            res = dlg.exec()
            if int(res) == int(QtWidgets.QDialog.Accepted):
                # Simulate accept path
                self._on_time_signature_accepted(dlg)
            else:
                self._on_time_signature_rejected(dlg)
            return
        # Keep reference while modeless-modal
        self._pending_dialog = dlg
        try:
            dlg.accepted.connect(lambda: self._on_time_signature_accepted(dlg))
            dlg.rejected.connect(lambda: self._on_time_signature_rejected(dlg))
        except Exception:
            pass

    def _on_time_signature_accepted(self, dlg: QtWidgets.QDialog) -> None:
        if self._editor is None:
            self._pending_dialog = None
            self._pending_bar_idx = None
            return
        try:
            numer, denom = dlg.get_values()  # type: ignore[attr-defined]
        except Exception:
            numer, denom = 4, 4
        try:
            score: SCORE = self._editor.current_score()
            bar_idx = int(self._pending_bar_idx or 0)
            self._apply_time_signature_at_barline(score, bar_idx, int(numer), int(denom))
            try:
                self._editor.update_score_length()
            except Exception:
                pass
            # Snapshot and redraw
            self._editor._snapshot_if_changed(coalesce=True, label='time_signature_change')
            self._editor.draw_frame()
        except Exception:
            pass
        finally:
            self._pending_dialog = None
            self._pending_bar_idx = None

    def _on_time_signature_rejected(self, dlg: QtWidgets.QDialog) -> None:
        # Simply clear pending state
        self._pending_dialog = None
        self._pending_bar_idx = None

    def _apply_time_signature_at_barline(self, score: SCORE, bar_idx: int, numer: int, denom: int) -> None:
        base_grid = list(getattr(score, 'base_grid', []) or [])
        if not base_grid:
            # Initialize with a single segment
            score.base_grid = [BaseGrid(numerator=numer, denominator=denom, grid_positions=list(range(1, numer+1)), measure_amount=1)]
            return
        # Map bar_idx to segment index and offset
        cum = 0
        seg_i = 0
        offset = 0
        for i, bg in enumerate(base_grid):
            m = int(getattr(bg, 'measure_amount', 1) or 1)
            if bar_idx < cum + m:
                seg_i = i
                offset = bar_idx - cum
                break
            cum += m
        # Existing segment
        cur_bg = base_grid[seg_i]
        m_total = int(getattr(cur_bg, 'measure_amount', 1) or 1)
        # If clicking exactly at the start of an existing time-signature segment (offset==0),
        # replace that segment's signature instead of creating a zero-measure segment.
        if int(offset) <= 0:
            try:
                cur_bg.numerator = int(numer)
            except Exception:
                pass
            try:
                cur_bg.denominator = int(denom)
            except Exception:
                pass
            try:
                cur_bg.grid_positions = list(range(1, int(numer) + 1))
            except Exception:
                pass
            # Keep measure_amount unchanged; no zero-measure segments created.
            return

        # Otherwise, split the current segment at the chosen bar and replace its tail with the new signature
        tail_count = max(0, m_total - int(offset))
        # Adjust current segment to end before the change (non-zero by construction)
        try:
            cur_bg.measure_amount = int(offset)
        except Exception:
            pass
        # Build new segment for the tail
        try:
            new_bg = BaseGrid(numerator=int(numer), denominator=int(denom), grid_positions=list(range(1, int(numer)+1)), measure_amount=max(1, int(tail_count)))
        except Exception:
            new_bg = BaseGrid()
            new_bg.numerator = int(numer)
            new_bg.denominator = int(denom)
            new_bg.grid_positions = list(range(1, int(numer)+1))
            new_bg.measure_amount = max(1, int(tail_count))
        # Insert new segment after the adjusted current segment
        try:
            score.base_grid.insert(seg_i + 1, new_bg)
        except Exception:
            pass

    # Block other mouse handlers for this tool; we use click only
    def on_left_press(self, x: float, y: float) -> None:
        super().on_left_press(x, y)

    def on_left_unpress(self, x: float, y: float) -> None:
        super().on_left_unpress(x, y)

    def on_left_double_click(self, x: float, y: float) -> None:
        super().on_left_double_click(x, y)

    def on_left_drag_start(self, x: float, y: float) -> None:
        super().on_left_drag_start(x, y)

    def on_left_drag(self, x: float, y: float, dx: float, dy: float) -> None:
        super().on_left_drag(x, y, dx, dy)

    def on_left_drag_end(self, x: float, y: float) -> None:
        super().on_left_drag_end(x, y)

    def on_mouse_move(self, x: float, y: float) -> None:
        super().on_mouse_move(x, y)

    def on_toolbar_button(self, name: str) -> None:
        # no-op
        return
