from __future__ import annotations
from typing import TYPE_CHECKING, cast, Iterable
import bisect
from file_model.SCORE import SCORE
from utils.CONSTANT import BLACK_KEYS, QUARTER_NOTE_UNIT, BE_KEYS
from ui.widgets.draw_util import DrawUtil
from utils.tiny_tool import key_class_filter
from utils.operator import Operator

if TYPE_CHECKING:
    from editor.editor import Editor


class NoteDrawerMixin:
    '''
        Note drawing pipeline adapted from legacy project:
        - Entry `_draw_notes()` computes x/y once and dispatches components
        - `_draw_single_note()` draws all parts (rectangle, head, stem, etc.)
        - Skips centered dashed chord guide for now; beams come later
    '''

    # Local key-class sets (approximate groups used for small positional tweaks)
    _CF_KEYS: set[int] = set(key_class_filter('CF'))
    _ADG_KEYS: set[int] = set(key_class_filter('ADG'))
    # Thresholded time comparator: 7 ticks (smallest app unit is 8)
    _time_op: Operator = Operator(7)
    # Cached sorted notes and indices for current draw pass
    _cached_notes_sorted: list | None = None
    _cached_notes_starts: list[float] | None = None
    _cached_window_lo: int | None = None
    _cached_window_hi: int | None = None
    _cached_notes_view: list | None = None

    def draw_note(self, du: DrawUtil) -> None:
        """Editor drawer entry point as used by draw_all()."""
        self._draw_notes(du, draw_mode='note')

    def _draw_notes(self, du: DrawUtil, draw_mode: str = 'note') -> None:
        self = cast("Editor", self)
        score: SCORE = self.current_score()
        if score is None:
            return

        # Layout metrics
        margin = float(self.margin or 0.0)
        zpq = float(score.editor.zoom_mm_per_quarter)

        def time_to_mm(ticks: float) -> float:
            return margin + (float(ticks) / float(QUARTER_NOTE_UNIT)) * zpq

        # Viewport culling: compute visible time range with small bleed
        top_mm = float(getattr(self, '_view_y_mm_offset', 0.0) or 0.0)
        vp_h_mm = float(getattr(self, '_viewport_h_mm', 0.0) or 0.0)
        bottom_mm = top_mm + vp_h_mm
        bleed_mm = max(2.0, zpq * 0.25)  # ~quarter-note/4 or 2mm minimum
        time_begin = float(self.mm_to_time(top_mm - bleed_mm))
        time_end = float(self.mm_to_time(bottom_mm + bleed_mm))

        # Build a time-indexed view: sort by start time once
        notes_sorted = sorted(score.events.note or [], key=lambda n: (n.time, n.pitch))
        starts = [float(n.time) for n in notes_sorted]
        ends = [float(n.time + n.duration) for n in notes_sorted]
        # Slice candidates whose start or end falls within range; also include spans via backward expansion
        lo_start = bisect.bisect_left(starts, time_begin)
        hi_start = bisect.bisect_right(starts, time_end)
        lo_end = bisect.bisect_left(ends, time_begin)
        hi_end = bisect.bisect_right(ends, time_end)
        viewport_len = float(time_end - time_begin)
        slack = float(self._time_op.threshold)
        back_lo = bisect.bisect_left(starts, float(time_begin - viewport_len - slack))
        # Union of index ranges to ensure ends-only and spanning notes are included
        candidate_idx_set = set(range(back_lo, hi_start)) | set(range(lo_end, hi_end))
        candidate_indices = sorted(candidate_idx_set)

        # Cache the candidate window for helper methods
        self._cached_notes_sorted = notes_sorted
        self._cached_notes_starts = starts
        self._cached_window_lo = candidate_indices[0] if candidate_indices else 0
        self._cached_window_hi = (candidate_indices[-1] + 1) if candidate_indices else 0
        self._cached_notes_view = [notes_sorted[i] for i in candidate_indices]

        # Iterate candidate set only
        for idx in candidate_indices:
            if idx < 0 or idx >= len(notes_sorted):
                continue
            n = notes_sorted[idx]
            # Final interval intersection test in time domain
            n_start = float(n.time)
            n_end = float(n.time + n.duration)
            if self._time_op.lt(n_end, time_begin) or self._time_op.gt(n_start, time_end):
                continue
            # Compute positions once and draw parts
            x = self.pitch_to_x(n.pitch)
            y1 = time_to_mm(n_start)
            y2 = time_to_mm(n_end)
            self._draw_single_note(du, n, x, y1, y2, draw_mode=draw_mode)

        # Clear caches after draw pass
        self._cached_notes_sorted = None
        self._cached_notes_starts = None
        self._cached_window_lo = None
        self._cached_window_hi = None
        self._cached_notes_view = None

    def _draw_single_note(self, du: DrawUtil, n, x: float, y1: float, y2: float, draw_mode: str = 'note') -> None:
        
        # Midinote rectangle
        self._draw_midinote(du, n, x, y1, y2, draw_mode)
        
        # Notehead
        self._draw_notehead(du, n, x, y1, draw_mode)
        
        # Stop sign (triangle) when followed by rest
        self._draw_notestop(du, n, x, y2, draw_mode)
        
        # Stem (horizontal tick at start)
        self._draw_stem(du, n, x, y1, draw_mode)
        
        # Continuation dot(s) for overlaps within the duration
        self._draw_note_continuation_dot(du, n, x, y1, y2, draw_mode)
        
        # Connect stem between extremes in chord at same start time (hand-local)
        self._draw_connect_stem(du, n, x, y1, draw_mode)
        
        # Left-hand indicator dot inside notehead
        self._draw_left_dot(du, n, x, y1, draw_mode)

    def _midinote_color(self, n, draw_mode: str) -> tuple[float, float, float, float]:
        if draw_mode in ('cursor', 'edit', 'selected'):
            return (0.2, 0.6, 1.0, 1.0)  # accent
        return (0.6, 0.7, 0.8, 1.0) if (getattr(n, 'hand', '<') in ('l', '<')) else (0.8, 0.7, 0.6, 1.0)

    def _draw_midinote(self, du: DrawUtil, n, x: float, y1: float, y2: float, draw_mode: str) -> None:
        fill = self._midinote_color(n, draw_mode)
        w = float(self.semitone_dist or 0.5)
        du.add_rectangle(
            x - w,
            y1,
            x + w,
            y2,
            stroke_color=None,
            fill_color=fill,
            id=0,
            tags=["midi_note"],
        )

    def _draw_notehead(self, du: DrawUtil, n, x: float, y1: float, draw_mode: str) -> None:
        w = float(self.semitone_dist or 0.5)
        layout = cast("Editor", self).current_score().layout
        outline_w = .3
        # Adjust vertical for black-note rule 'above_stem'
        if n.pitch in BLACK_KEYS and layout.black_note_rule == 'above_stem':
            y1 = y1 - (w * 2.0)
        if n.pitch in BLACK_KEYS:
            du.add_oval(
                x - w,
                y1,
                x + w,
                y1 + w * 2.0,
                stroke_color=None,
                fill_color=(0, 0, 0, 1),
                id=0,
                tags=["notehead_black"],
            )
        else:
            du.add_oval(
                x - w,
                y1,
                x + w,
                y1 + w * 2.0,
                stroke_width_mm=outline_w,
                fill_color=(1, 1, 1, 1),
                id=0,
                tags=["notehead_white"],
            )

    def _draw_notestop(self, du: DrawUtil, n, x: float, y2: float, draw_mode: str) -> None:
        # Show stop triangle if followed by a rest in same hand
        if not self._is_followed_by_rest(n):
            return
        
        # Draw triangle pointing down at end of note
        w = float(self.semitone_dist or 0.5) * 2.0
        points = [
            (x - w / 2, y2 - w),
            (x, y2),
            (x + w / 2, y2 - w),
        ]
        fill = self.notation_color
        # For cursor/edit/selected, emphasize
        if draw_mode in ('cursor', 'edit', 'selected'):
            fill = self.accent_color
        du.add_polygon(points_mm=points, stroke_color=None, fill_color=fill, id=0, tags=["stop_sign"]) 

    def _draw_stem(self, du: DrawUtil, n, x: float, y1: float, draw_mode: str) -> None:
        layout = cast("Editor", self).current_score().layout
        stem_len = 7.5
        stem_w = .75
        if getattr(n, 'hand', '<') in ('l', '<'):
            x2 = x - stem_len
        else:
            x2 = x + stem_len
        du.add_line(
            x,
            y1,
            x2,
            y1,
            color=(0, 0, 0, 1),
            width_mm=stem_w,
            id=0,
            tags=["stem"],
        )

    def _draw_note_continuation_dot(self, du: DrawUtil, n, x: float, y1: float, y2: float, draw_mode: str) -> None:
        # Draw dots where other notes in same hand start or end within this note duration
        hand = getattr(n, 'hand', '<')
        start = float(n.time)
        end = float(n.time + n.duration)
        w = float(self.semitone_dist or 0.5)

        # Collect dot times
        dot_times: list[float] = []
        notes_view = self._cached_notes_view or []
        for m in notes_view:
            if m.id == n.id or getattr(m, 'hand', '<') != hand:
                continue
            s = float(m.time)
            e = float(m.time + m.duration)
            if self._time_op.gt(s, start) and self._time_op.lt(s, end):
                dot_times.append(s)
            if self._time_op.gt(e, start) and self._time_op.lt(e, end):
                dot_times.append(e)
        if not dot_times:
            return

        # Draw dots
        dot_d = w * 0.8
        for t in sorted(set(dot_times)):
            y = float(self.time_to_mm(t))
            du.add_oval(
                x - dot_d / 2.0,
                y - dot_d / 2.0 + w,
                x + dot_d / 2.0,
                y + dot_d / 2.0 + w,
                fill_color=self.notation_color,
                stroke_color=None,
                id=0,
                tags=["left_dot"],
            )

    def _draw_connect_stem(self, du: DrawUtil, n, x: float, y1: float, draw_mode: str) -> None:
        # Connect extreme notes in a chord (same start time, same hand)
        hand = getattr(n, 'hand', '<')
        t = float(n.time)
        notes_view = self._cached_notes_view or []
        same_time = [m for m in notes_view if getattr(m, 'hand', '<') == hand and self._time_op.eq(float(m.time), t)]
        if len(same_time) < 2:
            return
        lowest = min(same_time, key=lambda m: m.pitch)
        highest = max(same_time, key=lambda m: m.pitch)
        x1 = self.pitch_to_x(lowest.pitch)
        x2 = self.pitch_to_x(highest.pitch)
        du.add_line(
            x1,
            y1,
            x2,
            y1,
            color=(0, 0, 0, 1),
            width_mm=.75,
            id=0,
            tags=["chord_connect"],
        )

    def _draw_left_dot(self, du: DrawUtil, n, x: float, y1: float, draw_mode: str) -> None:
        # Simple left-hand indicator dot in notehead (optional)
        if getattr(n, 'hand', '<') not in ('l', '<'):
            return
        w = float(self.semitone_dist or 0.5) * 2.0
        dot_d = w * 0.35
        cy = y1 + (w / 2.0)
        fill = (1, 1, 1, 1) if (n.pitch in BLACK_KEYS) else (0, 0, 0, 1)
        du.add_oval(
            x - dot_d / 2.0,
            cy - dot_d / 2.0,
            x + dot_d / 2.0,
            cy + dot_d / 2.0,
            stroke_color=None,
            fill_color=fill,
            id=0,
            tags=["left_dot"],
        )

    # ---- Helpers ----
    def _get_barline_positions(self) -> list[float]:
        score: SCORE = cast("Editor", self).current_score()
        pos: list[float] = []
        cur = 0.0
        for bg in score.base_grid:
            measure_len = float(bg.numerator) * (4.0 / float(bg.denominator)) * float(QUARTER_NOTE_UNIT)
            for _ in range(int(bg.measure_amount)):
                pos.append(cur)
                cur += measure_len
        return pos

    def _is_followed_by_rest(self, n) -> bool:
        # True if there is a gap after this note before next note in same hand
        hand = getattr(n, 'hand', '<')
        end = float(n.time + n.duration)
        min_delta = None
        thr = float(self._time_op.threshold)
        starts = self._cached_notes_starts or []
        notes_sorted = self._cached_notes_sorted or []
        idx = bisect.bisect_left(starts, float(end - thr)) if starts else 0
        for j in range(idx, len(notes_sorted)):
            m = notes_sorted[j]
            if m.id == n.id or getattr(m, 'hand', '<') != hand:
                continue
            delta = float(m.time) - end
            if delta >= -thr:
                min_delta = delta
                break
        if min_delta is None:
            return True
        return self._time_op.gt(float(min_delta), 0.0)
