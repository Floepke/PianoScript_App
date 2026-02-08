from __future__ import annotations
from typing import TYPE_CHECKING, cast
from ui.widgets.draw_util import DrawUtil
from utils.operator import Operator
from utils.CONSTANT import QUARTER_NOTE_UNIT
import bisect

if TYPE_CHECKING:
    from editor.editor import Editor


class BeamDrawerMixin:
    def draw_beam(self, du: DrawUtil) -> None:
        self = cast("Editor", self)
        # Build per-hand beam grouping lists following base_grid or beam markers,
        # then draw test beams on the stave sides to visualize group boundaries.
        cache = getattr(self, '_draw_cache', None)
        if not cache:
            return

        notes_by_hand = cache.get('notes_by_hand') or {}
        grid_times = cache.get('grid_den_times') or []
        beam_markers = cache.get('beam_by_hand') or {}
        op: Operator = cache.get('op') or Operator(7)
        score = self.current_score()
        layout = score.layout if score else None

        # Initialize storage for groups
        if not hasattr(self, '_beam_groups_by_hand'):
            self._beam_groups_by_hand = {}
        groups_all: dict[str, list[list]] = {}
        windows_all: dict[str, list[tuple[float, float]]] = {}

        # Helper: group notes by grid intervals [t_i, t_{i+1})
        def assign_groups(notes_sorted: list, starts: list[float], windows: list[tuple[float, float]]) -> list[list]:
            """Assign notes to windows by overlap, not just start-in-window.

            A note belongs to a window (t0, t1) if it overlaps the interval:
            (note_start < t1) and (note_end > t0).
            """
            if not notes_sorted or not windows:
                return []
            # Precompute ends aligned with notes_sorted
            ends = [float(n.time + n.duration) for n in notes_sorted]
            result: list[list] = []
            j = 0
            for (t0, t1) in windows:
                # advance j near t0 to reduce scanning; use starts
                j = bisect.bisect_left(starts, float(t0) - float(op.threshold), j)
                group: list = []
                k = j
                # scan forward while starts < t1 + thr
                while k < len(starts):
                    s = starts[k]
                    if op.ge(s, float(t1) + float(op.threshold)):
                        break
                    e = ends[k]
                    # overlap test
                    if op.gt(e, float(t0)) and op.lt(s, float(t1)):
                        group.append(notes_sorted[k])
                    k += 1
                # also include any notes that start before t0 but extend into window
                # robust backscan from j-1 down to 0 to catch long notes
                b = j - 1
                while b >= 0:
                    s = starts[b]
                    e = ends[b]
                    if op.gt(e, float(t0)) and op.lt(s, float(t1)):
                        group.append(notes_sorted[b])
                    # Optional early break: if e <= t0 and s well before t0, further earlier
                    # notes are unlikely to overlap unless extremely long; keep simple for correctness.
                    b -= 1
                # de-duplicate while preserving order by start time
                if group:
                    group = sorted({m._id: m for m in group}.values(), key=lambda n: float(n.time))
                result.append(group)
            return result

        def build_grid_windows(_times: list[float], a: float, b: float) -> list[tuple[float, float]]:
            """Build windows using base_grid beat_grouping.

            - If beat_grouping is a single full group (1..numer), windows are whole measures.
            - Otherwise, windows are per-group segments using beats where value == 1 as starts.
            """
            if score is None:
                return []
            windows: list[tuple[float, float]] = []
            cur = 0.0
            for bg in getattr(score, 'base_grid', []) or []:
                numer = int(getattr(bg, 'numerator', 4) or 4)
                denom = int(getattr(bg, 'denominator', 4) or 4)
                # Use ticks: QUARTER_NOTE_UNIT per quarter note
                measure_len_ticks = float(numer) * (4.0 / float(denom)) * float(QUARTER_NOTE_UNIT)
                beat_len_ticks = measure_len_ticks / max(1, int(numer))
                seq = list(getattr(bg, 'beat_grouping', []) or [])
                full_group = len(seq) == numer and [int(v) for v in seq] == list(range(1, numer + 1))
                for _ in range(int(getattr(bg, 'measure_amount', 1) or 1)):
                    m_start = float(cur)
                    m_end = float(cur + measure_len_ticks)
                    if op.lt(m_end, float(a)):
                        cur = m_end
                        continue
                    if op.gt(m_start, float(b)):
                        cur = m_end
                        continue
                    if len(seq) != numer:
                        seq = [1]
                    if full_group:
                        # Single full group: split into per-beat windows
                        group_starts = list(range(1, numer + 1))
                    else:
                        # Multiple groups: split by reset-to-1 positions
                        group_starts = [i for i, v in enumerate(seq, start=1) if int(v) == 1]
                        if not group_starts or group_starts[0] != 1:
                            group_starts = [1] + group_starts
                    for gi, s in enumerate(group_starts):
                        e = (group_starts[gi + 1] - 1) if (gi + 1) < len(group_starts) else numer
                        w0 = m_start + (s - 1) * beat_len_ticks
                        w1 = m_start + float(e) * beat_len_ticks
                        w0 = max(float(a), w0)
                        w1 = min(float(b), w1)
                        if op.lt(w0, w1):
                            windows.append((w0, w1))
                    cur = m_end
            return windows

        def build_duration_windows(start: float, end: float, dur: float) -> list[tuple[float, float]]:
            if dur <= 0:
                return [(start, end)]
            windows: list[tuple[float, float]] = []
            t = float(start)
            while op.lt(t, float(end)):
                t1 = min(float(end), t + float(dur))
                windows.append((t, t1))
                t = t1
            return windows

        def group_by_beam_markers(notes: list, times: list[float], markers: list) -> tuple[list[list], list[tuple[float, float]]]:
            # Compute windows independent of whether there are notes; groups may be empty.
            notes_sorted = sorted(notes, key=lambda n: float(n.time)) if notes else []
            starts = [float(n.time) for n in notes_sorted] if notes_sorted else []
            score_start = float(times[0]) if times else (starts[0] if starts else 0.0)
            score_end = float(times[-1]) if times else (starts[-1] if starts else 0.0)
            windows: list[tuple[float, float]] = []
            # markers sorted by time
            markers_sorted = sorted(markers, key=lambda m: float(getattr(m, 'time', 0.0))) if markers else []
            cur = score_start
            for idx, mk in enumerate(markers_sorted):
                mt = float(getattr(mk, 'time', cur))
                dur = float(getattr(mk, 'duration', 0.0) or 0.0)
                next_t = float(getattr(markers_sorted[idx + 1], 'time', score_end)) if (idx + 1) < len(markers_sorted) else score_end
                # grid-following segment before marker
                if op.gt(mt, cur):
                    windows.extend(build_grid_windows(times, cur, mt))
                # segment from marker to next marker/end: duration windows if dur>0, else grid windows
                if dur > 0.0:
                    windows.extend(build_duration_windows(mt, next_t, dur))
                else:
                    windows.extend(build_grid_windows(times, mt, next_t))
                cur = next_t
            # tail segment after last marker: follow grid
            if op.lt(cur, score_end):
                windows.extend(build_grid_windows(times, cur, score_end))
            groups = assign_groups(notes_sorted, starts, windows) if notes_sorted else []
            return groups, windows

        def norm_hand(h: str) -> str:
            return 'l' if h in ('<', 'l') else 'r'

        # Normalize hand keys for notes and markers
        notes_by_norm: dict[str, list] = {'l': [], 'r': []}
        for h, notes in notes_by_hand.items():
            notes_by_norm[norm_hand(str(h))].extend(notes)
        markers_by_norm: dict[str, list] = {'l': [], 'r': []}
        for h, ms in beam_markers.items():
            markers_by_norm[norm_hand(str(h))].extend(ms)

        # Build groups per hand, honoring markers when present
        for hand_norm, notes in notes_by_norm.items():
            markers = markers_by_norm.get(hand_norm) or []
            groups, windows = group_by_beam_markers(notes, grid_times, markers)
            groups_all[hand_norm] = groups
            windows_all[hand_norm] = windows

        # Cache on editor for downstream drawing steps
        self._beam_groups_by_hand = groups_all

        if not bool(layout.beam_visible):
            return

        # ---- Actual beam line drawing (right hand) ----
        # For each right-hand group, draw a slightly diagonal beam line
        # from the first note time (y1) to the last note time (y2).
        # X positions: start at the highest pitch's stem tip (pitch_x + stem_len),
        # and end at x1 + semitone_dist to give a gentle diagonal.
        layout = self.current_score().layout
        stem_len = float(layout.note_stem_length_mm or 5.0) * float(layout.scale or 1.0)
        beam_w = float(layout.beam_thickness_mm or 1.0)
        stem_w = float(layout.note_stem_thickness_mm or 0.5)

        # Iterate windows in lockstep with groups for right hand
        right_groups = groups_all.get('r') or []
        right_windows = windows_all.get('r') or []
        for idx, grp in enumerate(right_groups):
            if not grp or len(grp) < 1:
                continue
            t0, t1 = right_windows[idx] if idx < len(right_windows) else (float(min(grp, key=lambda n: float(n.time)).time), float(max(grp, key=lambda n: float(n.time)).time))
            # First and last starting time within the window
            starts_in = [float(n.time) for n in grp if op.ge(float(n.time), float(t0)) and op.lt(float(n.time), float(t1))]
            if not starts_in:
                # Skip drawing beam if no note starts inside this window
                continue
            # Skip if all starts are effectively equal (single chord only)
            s_min, s_max = min(starts_in), max(starts_in)
            if op.eq(float(s_min), float(s_max)):
                continue
            t_first = min(starts_in)
            t_last = max(starts_in)
            # Highest pitch in the group (including spanning notes)
            highest = max(grp, key=lambda n: int(getattr(n, 'pitch', 0)))
            # x1 at the highest pitch notehead (not stem tip) to avoid covering dots
            x1 = float(self.pitch_to_x(int(getattr(highest, 'pitch', 0)))) + float(stem_len)
            # x2 uses same base as x1 plus semitone_dist to preserve diagonal
            x2 = x1 + float(self.semitone_dist or 0.0)
            y1 = float(self.time_to_mm(t_first))
            y2 = float(self.time_to_mm(t_last))
            du.add_line(
                x1,
                y1,
                x2,
                y2,
                color=self.notation_color,
                width_mm=max(0.2, beam_w),
                id=0,
                tags=["beam_line_right"],
            )
            # Connect each note's stem tip to the beam line at that note's time
            for m in grp:
                mt = float(getattr(m, 'time', t_first))
                # Only connect notes starting inside the window
                if not (op.ge(mt, float(t0)) and op.lt(mt, float(t1))):
                    continue
                y_note = float(self.time_to_mm(mt))
                x_tip = float(self.pitch_to_x(int(getattr(m, 'pitch', 0)))) + float(stem_len)
                if abs(y2 - y1) > 1e-6:
                    t = (y_note - y1) / (y2 - y1)
                    x_on_beam = x1 + t * (x2 - x1)
                else:
                    x_on_beam = x1
                du.add_line(
                    x_tip,
                    y_note,
                    float(x_on_beam),
                    y_note,
                    color=self.notation_color,
                    width_mm=max(0.15, stem_w),
                    id=0,
                    tags=["beam_connect_right"],
                )

        # ---- Actual beam line drawing (left hand) ----
        # For each left-hand group, draw a slightly diagonal beam line
        # using the lowest pitch's stem tip (pitch_x - stem_len) as x1,
        # and x2 = x1 - semitone_dist for a gentle diagonal.
        # Iterate windows in lockstep with groups for left hand
        left_groups = groups_all.get('l') or []
        left_windows = windows_all.get('l') or []
        for idx, grp in enumerate(left_groups):
            if not grp or len(grp) < 1:
                continue
            t0, t1 = left_windows[idx] if idx < len(left_windows) else (float(min(grp, key=lambda n: float(n.time)).time), float(max(grp, key=lambda n: float(n.time)).time))
            starts_in = [float(n.time) for n in grp if op.ge(float(n.time), float(t0)) and op.lt(float(n.time), float(t1))]
            if not starts_in:
                # Skip drawing beam if no note starts inside this window
                continue
            # Skip if all starts are effectively equal (single chord only)
            s_min, s_max = min(starts_in), max(starts_in)
            if op.eq(float(s_min), float(s_max)):
                continue
            t_first = min(starts_in)
            t_last = max(starts_in)
            # Lowest and highest pitch in the group
            lowest = min(grp, key=lambda n: int(getattr(n, 'pitch', 0)))
            x1 = float(self.pitch_to_x(int(getattr(lowest, 'pitch', 0)))) - float(stem_len)
            # x2 uses same base as x1 minus semitone_dist to preserve diagonal
            x2 = x1 - float(self.semitone_dist or 0.0)
            y1 = float(self.time_to_mm(t_first))
            y2 = float(self.time_to_mm(t_last))
            du.add_line(
                x1,
                y1,
                x2,
                y2,
                color=self.notation_color,
                width_mm=max(0.2, beam_w),
                id=0,
                tags=["beam_line_left"],
            )
            # Connect each note's stem tip to the beam line at that note's time
            for m in grp:
                mt = float(getattr(m, 'time', t_first))
                if not (op.ge(mt, float(t0)) and op.lt(mt, float(t1))):
                    continue
                y_note = float(self.time_to_mm(mt))
                x_tip = float(self.pitch_to_x(int(getattr(m, 'pitch', 0)))) - float(stem_len)
                if abs(y2 - y1) > 1e-6:
                    t = (y_note - y1) / (y2 - y1)
                    x_on_beam = x1 + t * (x2 - x1)
                else:
                    x_on_beam = x1
                du.add_line(
                    x_tip,
                    y_note,
                    float(x_on_beam),
                    y_note,
                    color=self.notation_color,
                    width_mm=max(0.15, stem_w),
                    id=0,
                    tags=["beam_connect_left"],
                )
