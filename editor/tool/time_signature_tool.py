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
        # Preserve editor widget focus policy while a modal dialog is active
        self._prev_editor_focus_policy: Optional[int] = None

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
        # Determine a suitable parent: prefer the active window (MainWindow)
        parent_w = None
        try:
            from PySide6 import QtWidgets as _QtWidgets
            parent_w = _QtWidgets.QApplication.activeWindow()
        except Exception:
            parent_w = None
        try:
            from ui.widgets.time_signature_dialog import TimeSignatureDialog
        except Exception:
            TimeSignatureDialog = None  # type: ignore
        if TimeSignatureDialog is None:
            return
        # Prefill dialog with active time signature at nearest barline
        initial_numer = 4
        initial_denom = 4
        # For Klavarskribo grouping semantics, defer defaults to dialog
        initial_grid_positions = None
        initial_indicator_enabled: bool = True
        try:
            score: SCORE = self._editor.current_score()
            base_grid = list(getattr(score, 'base_grid', []) or [])
            if base_grid:
                bar_idx = int(self._pending_bar_idx or 0)
                # Map bar_idx to segment index
                cum = 0
                seg_i = 0
                for i, bg in enumerate(base_grid):
                    m = int(getattr(bg, 'measure_amount', 1) or 1)
                    if bar_idx < cum + m:
                        seg_i = i
                        break
                    cum += m
                cur_bg = base_grid[seg_i]
                initial_numer = int(getattr(cur_bg, 'numerator', initial_numer))
                initial_denom = int(getattr(cur_bg, 'denominator', initial_denom))
                gp_attr = getattr(cur_bg, 'beat_grouping', None)
                gp = list(gp_attr if gp_attr is not None else (getattr(cur_bg, 'grid_positions', []) or []))
                if gp:
                    # sanitize to valid positions
                    sanitized = sorted([int(p) for p in gp if isinstance(p, int) and 1 <= int(p) <= int(initial_numer)])
                    initial_grid_positions = sanitized if sanitized else None
                else:
                    # Let dialog choose sensible defaults (e.g., [1] for Klavarskribo)
                    initial_grid_positions = None
                initial_indicator_enabled = bool(getattr(cur_bg, 'indicator_enabled', True))
        except Exception:
            pass
        # Provide indicator_type from Layout to inform dialog defaults
        indicator_type = 'classical'
        try:
            indicator_type = str(getattr(score.layout, 'indicator_type', 'classical'))
        except Exception:
            indicator_type = 'classical'
        dlg = TimeSignatureDialog(parent=parent_w, initial_numer=initial_numer, initial_denom=initial_denom, initial_grid_positions=initial_grid_positions, initial_indicator_enabled=initial_indicator_enabled, indicator_type=indicator_type)
        # Make modeless/non-modal like FX synth dialog
        try:
            dlg.setModal(False)
            dlg.setWindowModality(QtCore.Qt.NonModal)
        except Exception:
            pass
        # Wire OK/Cancel to accept/reject and apply via signals
        try:
            dlg.btns.accepted.connect(dlg.accept)
            dlg.btns.rejected.connect(dlg.reject)
        except Exception:
            pass
        try:
            dlg.accepted.connect(lambda: self._on_time_signature_accepted(dlg))
            dlg.rejected.connect(lambda: self._on_time_signature_rejected(dlg))
        except Exception:
            pass
        # Keep a reference while modeless and show
        self._pending_dialog = dlg
        try:
            dlg.raise_()
            dlg.activateWindow()
        except Exception:
            pass
        dlg.show()
        return

    def _on_time_signature_accepted(self, dlg: QtWidgets.QDialog) -> None:
        if self._editor is None:
            self._pending_dialog = None
            self._pending_bar_idx = None
            return
        try:
            numer, denom, grid_positions, indicator_enabled = dlg.get_values()  # type: ignore[attr-defined]
        except Exception:
            numer, denom, grid_positions, indicator_enabled = 4, 4, [1, 2, 3, 4], True
        try:
            score: SCORE = self._editor.current_score()
            bar_idx = int(self._pending_bar_idx or 0)
            self._apply_time_signature_at_barline(score, bar_idx, int(numer), int(denom), list(grid_positions), bool(indicator_enabled))
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

    def _apply_time_signature_at_barline(self, score: SCORE, bar_idx: int, numer: int, denom: int, grid_positions: list[int], indicator_enabled: bool) -> None:
        base_grid = list(getattr(score, 'base_grid', []) or [])
        if not base_grid:
            # Initialize with a single segment
            score.base_grid = [BaseGrid(numerator=numer, denominator=denom, beat_grouping=list(grid_positions or range(1, numer+1)), measure_amount=1, indicator_enabled=bool(indicator_enabled))]
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
                cur_bg.beat_grouping = list(grid_positions or list(range(1, int(numer) + 1)))
            except Exception:
                pass
            try:
                cur_bg.indicator_enabled = bool(indicator_enabled)
            except Exception:
                pass
            # Keep measure_amount unchanged; no zero-measure segments created.
            self._merge_adjacent_base_grids(score)
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
            new_bg = BaseGrid(numerator=int(numer), denominator=int(denom), beat_grouping=list(grid_positions or list(range(1, int(numer)+1))), measure_amount=max(1, int(tail_count)), indicator_enabled=bool(indicator_enabled))
        except Exception:
            new_bg = BaseGrid()
            new_bg.numerator = int(numer)
            new_bg.denominator = int(denom)
            new_bg.beat_grouping = list(grid_positions or list(range(1, int(numer)+1)))
            new_bg.measure_amount = max(1, int(tail_count))
            try:
                new_bg.indicator_enabled = bool(indicator_enabled)
            except Exception:
                pass
        # Insert new segment after the adjusted current segment
        try:
            score.base_grid.insert(seg_i + 1, new_bg)
        except Exception:
            pass
        # After insertion, merge adjacent identical segments except measure_amount
        self._merge_adjacent_base_grids(score)

    def _merge_adjacent_base_grids(self, score: SCORE) -> None:
        try:
            bgs = list(getattr(score, 'base_grid', []) or [])
            if not bgs:
                return
            merged: list[BaseGrid] = []
            for bg in bgs:
                if merged:
                    prev = merged[-1]
                    # Compare all fields except measure_amount
                    same = (
                        int(getattr(prev, 'numerator', 0)) == int(getattr(bg, 'numerator', 0)) and
                        int(getattr(prev, 'denominator', 0)) == int(getattr(bg, 'denominator', 0)) and
                        list((getattr(prev, 'beat_grouping', None) if getattr(prev, 'beat_grouping', None) is not None else (getattr(prev, 'grid_positions', []) or []))) ==
                        list((getattr(bg, 'beat_grouping', None) if getattr(bg, 'beat_grouping', None) is not None else (getattr(bg, 'grid_positions', []) or []))) and
                        bool(getattr(prev, 'indicator_enabled', True)) == bool(getattr(bg, 'indicator_enabled', True))
                    )
                    if same:
                        try:
                            prev.measure_amount = int(getattr(prev, 'measure_amount', 1) or 1) + int(getattr(bg, 'measure_amount', 1) or 1)
                        except Exception:
                            pass
                        continue
                merged.append(bg)
            score.base_grid = merged
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

    def on_right_click(self, x: float, y: float) -> None:
        """Delete the closest time signature change (segment start) except the first.

        Maps the click Y to time, finds the nearest barline, then selects the nearest
        BaseGrid segment boundary (start) other than the first and removes it by merging
        its measure_amount into the previous segment.
        """
        super().on_right_click(x, y)
        if self._editor is None:
            return
        score: SCORE = self._editor.current_score()
        base_grid = list(getattr(score, 'base_grid', []) or [])
        if not base_grid:
            return
        # Build barline times per measure across segments
        click_t = float(self._editor.y_to_time(y))
        bars: list[float] = []
        seg_start_bar_indices: list[int] = []
        cur_t = 0.0
        for i, bg in enumerate(base_grid):
            seg_start_bar_indices.append(len(bars))  # segment start at current bar count
            measure_len = float(bg.numerator) * (4.0 / float(bg.denominator)) * float(QUARTER_NOTE_UNIT)
            for _ in range(int(getattr(bg, 'measure_amount', 1) or 1)):
                bars.append(cur_t)
                cur_t += measure_len
        if not bars:
            return
        # Find nearest barline index to click
        nearest_bar_idx = 0
        min_abs = abs(click_t - float(bars[0]))
        for i, t in enumerate(bars):
            d = abs(click_t - float(t))
            if d < min_abs:
                min_abs = d
                nearest_bar_idx = i
        # Find nearest segment start index (bar index) excluding the first
        if len(seg_start_bar_indices) <= 1:
            return  # nothing to delete
        # Compute nearest segment start
        nearest_seg_start = seg_start_bar_indices[1]  # init to first deletable
        min_d = abs(nearest_bar_idx - nearest_seg_start)
        for bidx in seg_start_bar_indices[1:]:  # exclude index 0
            d = abs(nearest_bar_idx - bidx)
            if d < min_d:
                min_d = d
                nearest_seg_start = bidx
        # Map this segment-start bar index to the segment index in base_grid
        # Using cumulative measure counts
        cum = 0
        seg_i = None
        for i, bg in enumerate(base_grid):
            m = int(getattr(bg, 'measure_amount', 1) or 1)
            if nearest_seg_start == cum:
                seg_i = i
                break
            cum += m
        if seg_i is None or seg_i <= 0:
            return  # cannot delete first segment or not found
        # Merge current segment into previous and remove it
        try:
            prev = base_grid[seg_i - 1]
            cur = base_grid[seg_i]
            prev.measure_amount = int(getattr(prev, 'measure_amount', 1) or 1) + int(getattr(cur, 'measure_amount', 1) or 1)
            # Remove cur
            del base_grid[seg_i]
            score.base_grid = base_grid
        except Exception:
            return
        # Optional: coalesce adjacent identical segments after removal
        self._merge_adjacent_base_grids(score)
        # Update score length, snapshot, redraw
        try:
            self._editor.update_score_length()
        except Exception:
            pass
        self._editor._snapshot_if_changed(coalesce=True, label='time_signature_delete')
        self._editor.draw_frame()
