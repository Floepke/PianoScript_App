from PySide6 import QtCore
from datetime import datetime
import bisect
import multiprocessing as mp
import queue
import traceback
from ui.widgets.draw_util import DrawUtil
from utils.CONSTANT import BE_KEYS, QUARTER_NOTE_UNIT, PIANO_KEY_AMOUNT, SHORTEST_DURATION, hex_to_rgba, BLACK_KEYS
from utils.tiny_tool import key_class_filter
from utils.operator import Operator
from file_model.SCORE import SCORE

try:
    _MP_CONTEXT = mp.get_context("spawn")
except Exception:
    _MP_CONTEXT = mp.get_context()

def do_engrave(score: SCORE, du: DrawUtil, pageno: int = 0, pdf_export: bool = False) -> None:
    """Compute the full page drawing from the score dict into DrawUtil.

    This function runs off-thread. It should rebuild pages deterministically
    from the input score. Keep Cairo usage confined to DrawUtil rendering.
    """
    score: SCORE = score or {}
    layout = (score.get('layout', {}) or {})
    header = (score.get('header', {}) or {})
    editor = (score.get('editor', {}) or {})
    events = (score.get('events', {}) or {})
    base_grid = list(score.get('base_grid', []) or [])
    line_breaks = list(events.get('line_break', []) or [])
    notes = list(events.get('note', []) or [])
    count_lines = list(events.get('count_line', []) or [])
    beam_markers = list(events.get('beam', []) or [])

    beam_by_hand: dict[str, list[dict]] = {'l': [], 'r': []}
    for b in beam_markers:
        if not isinstance(b, dict):
            continue
        try:
            bt = float(b.get('time', 0.0) or 0.0)
            bd = float(b.get('duration', 0.0) or 0.0)
        except Exception:
            traceback.print_exc()
            continue
        hand_raw = str(b.get('hand', '<') or '<')
        hand_key = 'l' if hand_raw in ('<', 'l') else 'r'
        beam_by_hand[hand_key].append({'time': bt, 'duration': bd})
    for hk in beam_by_hand:
        beam_by_hand[hk] = sorted(beam_by_hand[hk], key=lambda m: float(m.get('time', 0.0)))

    norm_notes: list[dict] = []
    notes_by_hand: dict[str, list[dict]] = {'<': [], '>': []}
    starts_by_hand: dict[str, list[float]] = {'<': [], '>': []}
    for idx, n in enumerate(notes):
        if not isinstance(n, dict):
            continue
        try:
            n_t = float(n.get('time', 0.0) or 0.0)
            n_d = float(n.get('duration', 0.0) or 0.0)
            n_end = n_t + n_d
            p = int(n.get('pitch', 0) or 0)
        except Exception:
            traceback.print_exc()
            continue
        hand_raw = str(n.get('hand', '<') or '<')
        hand_key = '<' if hand_raw in ('l', '<') else '>'
        item = {
            'time': n_t,
            'duration': n_d,
            'end': n_end,
            'pitch': p,
            'hand': hand_key,
            'id': int(n.get('_id', 0) or 0),
            'idx': int(idx),
            'raw': n,
        }
        norm_notes.append(item)
        notes_by_hand[hand_key].append(item)

    for hand_key, items in notes_by_hand.items():
        items.sort(key=lambda it: (float(it['time']), int(it['pitch']), int(it['id'])))
        starts_by_hand[hand_key] = [float(it['time']) for it in items]

    page_w = float(layout.get('page_width_mm', 210.0) or 210.0)
    page_h = float(layout.get('page_height_mm', 297.0) or 297.0)
    page_left = float(layout.get('page_left_margin_mm', 5.0) or 5.0)
    page_right = float(layout.get('page_right_margin_mm', 5.0) or 5.0)
    page_top = float(layout.get('page_top_margin_mm', 10.0) or 10.0)
    page_bottom = float(layout.get('page_bottom_margin_mm', 10.0) or 10.0)
    scale = float(layout.get('scale', 1.0) or 1.0)
    stave_two_w = float(layout.get('stave_two_line_thickness_mm', 0.5) or 0.5) * scale
    stave_three_w = float(layout.get('stave_three_line_thickness_mm', 0.5) or 0.5) * scale
    clef_dash = list(layout.get('stave_clef_line_dash_pattern_mm', []) or [])
    if clef_dash:
        clef_dash = [float(v) * scale for v in clef_dash]
    op_time = Operator(SHORTEST_DURATION)
    barline_positions: list[float] = []
    cur_bar = 0.0
    for bg in base_grid:
        numer = int(bg.get('numerator', 4) or 4)
        denom = int(bg.get('denominator', 4) or 4)
        measures = int(bg.get('measure_amount', 1) or 1)
        measure_len = float(numer) * (4.0 / float(max(1, denom))) * float(QUARTER_NOTE_UNIT)
        for _ in range(int(max(0, measures))):
            barline_positions.append(float(cur_bar))
            cur_bar += measure_len

    ts_segments: list[dict[str, float | int | list[int] | bool]] = []
    ts_cursor = 0.0
    for bg in base_grid:
        try:
            numer = int(bg.get('numerator', 4) or 4)
            denom = int(bg.get('denominator', 4) or 4)
            measures = int(bg.get('measure_amount', 1) or 1)
            beat_grouping = list(bg.get('beat_grouping', []) or [])
            indicator_enabled = bool(bg.get('indicator_enabled', True))
        except Exception:
            traceback.print_exc()
            continue
        if measures <= 0:
            continue
        measure_len = float(numer) * (4.0 / float(max(1, denom))) * float(QUARTER_NOTE_UNIT)
        ts_segments.append(
            {
                'start': float(ts_cursor),
                'measure_len': float(measure_len),
                'numerator': int(numer),
                'denominator': int(denom),
                'measure_amount': int(measures),
                'beat_grouping': beat_grouping,
                'indicator_enabled': bool(indicator_enabled),
            }
        )
        ts_cursor += measure_len * float(measures)

    # Precompute measure windows for numbering (start/end in ticks)
    measure_windows: list[dict[str, float | int]] = []
    m_idx = 1
    cur_m = 0.0
    for bg in base_grid:
        numer = int(bg.get('numerator', 4) or 4)
        denom = int(bg.get('denominator', 4) or 4)
        measures = int(bg.get('measure_amount', 1) or 1)
        measure_len = float(numer) * (4.0 / float(max(1, denom))) * float(QUARTER_NOTE_UNIT)
        for _ in range(int(max(0, measures))):
            measure_windows.append({'start': float(cur_m), 'end': float(cur_m + measure_len), 'number': int(m_idx)})
            m_idx += 1
            cur_m += measure_len

    def _log(msg: str) -> None:
        """No-op logger placeholder to keep call sites stable."""
        return

    def _normalize_hex_color(value: str | None) -> str | None:
        """Normalize hex color strings and allow special hand markers."""
        if value is None:
            return None
        txt = str(value).strip()
        if not txt:
            return None
        if txt in ('<', '>'):
            return txt
        if not txt.startswith('#'):
            txt = f"#{txt}"
        hex_part = txt[1:]
        if len(hex_part) not in (3, 6, 8):
            return None
        if not all(c in '0123456789abcdefABCDEF' for c in hex_part):
            return None
        if len(hex_part) == 3:
            hex_part = ''.join(c * 2 for c in hex_part)
        if len(hex_part) == 8:
            hex_part = hex_part[:6]
        return f"#{hex_part}"

    def _hex_to_rgba01(hex_color: str, alpha: float = 1.0) -> tuple[float, float, float, float]:
        """Convert a hex color into RGBA floats in the 0..1 range."""
        rgba = hex_to_rgba(hex_color, alpha)
        r, g, b, a = rgba
        return (float(r) / 255.0, float(g) / 255.0, float(b) / 255.0, float(a))

    def _header_entry(key: str) -> dict:
        """Return a normalized header entry dict for title/composer/footer data."""
        value = header.get(key, {}) if isinstance(header, dict) else {}
        if isinstance(value, dict):
            return value
        if isinstance(value, str):
            return {'text': value}
        return {}

    def _allow_font_registry() -> bool:
        """Return True when it is safe to access QFontDatabase (GUI process only)."""
        try:
            return mp.current_process().name == "MainProcess"
        except Exception:
            return False

    def _resolve_font_family(family: str) -> str:
        """Resolve a font family name with the font registry if available."""
        if not _allow_font_registry():
            return family
        try:
            from fonts import resolve_font_family
            return str(resolve_font_family(family))
        except Exception:
            return family

    def _layout_font(key: str, fallback_family: str, fallback_size: float) -> tuple[str, float, bool, bool]:
        """Fetch a layout font entry from the layout dict with fallback values."""
        raw = layout.get(key, {}) if isinstance(layout, dict) else {}
        if not isinstance(raw, dict):
            raw = {}
        family = str(raw.get('family', fallback_family) or fallback_family)
        if family == 'C059' and _allow_font_registry():
            try:
                from fonts import register_font_from_bytes
            except Exception:
                register_font_from_bytes = None  # type: ignore
            try:
                reg = register_font_from_bytes('C059') if register_font_from_bytes else 'C059'
                if reg:
                    family = str(reg)
            except Exception:
                pass
        family = _resolve_font_family(family)
        size_pt = float(raw.get('size_pt', fallback_size) or fallback_size)
        bold = bool(raw.get('bold', False))
        italic = bool(raw.get('italic', False))
        return family, size_pt, bold, italic

    def _header_text(key: str, fallback: str) -> str:
        """Fetch header text with a fallback, always returning a string."""
        entry = _header_entry(key)
        txt = entry.get('text', fallback)
        return str(txt) if txt is not None else str(fallback)

    def _header_font(key: str, fallback_family: str, fallback_size: float) -> tuple[str, float, bool, bool, float, float]:
        """Fetch header font settings (family, size, style, offsets)."""
        entry = _header_entry(key)
        family = _resolve_font_family(str(entry.get('family', fallback_family) or fallback_family))
        size_pt = float(entry.get('size_pt', fallback_size) or fallback_size)
        bold = bool(entry.get('bold', False))
        italic = bool(entry.get('italic', False))
        x_off = float(entry.get('x_offset_mm', 0.0) or 0.0)
        y_off = float(entry.get('y_offset_mm', 0.0) or 0.0)
        return family, size_pt, bold, italic, x_off, y_off

    def _assign_groups(notes_sorted: list[dict], windows: list[tuple[float, float]]) -> list[list[dict]]:
        """Assign notes to time windows by overlap and preserve start-time order."""
        if not notes_sorted or not windows:
            return []
        starts = [float(n.get('time', 0.0) or 0.0) for n in notes_sorted]
        ends = [float(n.get('end', 0.0) or 0.0) for n in notes_sorted]
        result: list[list[dict]] = []
        j = 0
        for (t0, t1) in windows:
            j = bisect.bisect_left(starts, float(t0) - float(op_time.threshold), j)
            group: list[dict] = []
            k = j
            while k < len(starts):
                s = starts[k]
                if op_time.ge(s, float(t1) + float(op_time.threshold)):
                    break
                e = ends[k]
                if op_time.gt(e, float(t0)) and op_time.lt(s, float(t1)):
                    group.append(notes_sorted[k])
                k += 1
            b = j - 1
            while b >= 0:
                s = starts[b]
                e = ends[b]
                if op_time.gt(e, float(t0)) and op_time.lt(s, float(t1)):
                    group.append(notes_sorted[b])
                b -= 1
            if group:
                keyed: dict[int, dict] = {}
                for m in group:
                    key_id = int(m.get('idx', m.get('id', 0)) or 0)
                    keyed[key_id] = m
                group = sorted(keyed.values(), key=lambda n: float(n.get('time', 0.0) or 0.0))
            result.append(group)
        return result

    def _build_grid_windows(a: float, b: float) -> list[tuple[float, float]]:
        """Build time windows using base grid beat grouping between a and b."""
        windows: list[tuple[float, float]] = []
        cur = 0.0
        for bg in base_grid:
            try:
                numer = int(bg.get('numerator', 4) or 4)
                denom = int(bg.get('denominator', 4) or 4)
                measures = int(bg.get('measure_amount', 1) or 1)
                seq = list(bg.get('beat_grouping', []) or [])
            except Exception:
                traceback.print_exc()
                continue
            measure_len = float(numer) * (4.0 / float(max(1, denom))) * float(QUARTER_NOTE_UNIT)
            beat_len = measure_len / max(1, int(numer))
            full_group = len(seq) == numer and [int(v) for v in seq] == list(range(1, numer + 1))
            for _ in range(int(measures)):
                m_start = float(cur)
                m_end = float(cur + measure_len)
                if op_time.lt(m_end, float(a)):
                    cur = m_end
                    continue
                if op_time.gt(m_start, float(b)):
                    cur = m_end
                    continue
                if len(seq) != numer:
                    seq = [1]
                if full_group:
                    group_starts = list(range(1, numer + 1))
                else:
                    group_starts = [i for i, v in enumerate(seq, start=1) if int(v) == 1]
                    if not group_starts or group_starts[0] != 1:
                        group_starts = [1] + group_starts
                for gi, s in enumerate(group_starts):
                    e = (group_starts[gi + 1] - 1) if (gi + 1) < len(group_starts) else numer
                    w0 = m_start + (s - 1) * beat_len
                    w1 = m_start + float(e) * beat_len
                    w0 = max(float(a), w0)
                    w1 = min(float(b), w1)
                    if op_time.lt(w0, w1):
                        windows.append((w0, w1))
                cur = m_end
        return windows

    def _build_duration_windows(start: float, end: float, dur: float) -> list[tuple[float, float]]:
        """Build consecutive windows of fixed duration between start and end."""
        if dur <= 0:
            return [(start, end)]
        windows: list[tuple[float, float]] = []
        t = float(start)
        while op_time.lt(t, float(end)):
            t1 = min(float(end), t + float(dur))
            windows.append((t, t1))
            t = t1
        return windows

    def _group_by_beam_markers(notes: list[dict], markers: list[dict], start: float, end: float) -> tuple[list[list[dict]], list[tuple[float, float]]]:
        """Split notes into beam groups using marker- and grid-based windows."""
        notes_sorted = sorted(notes, key=lambda n: float(n.get('time', 0.0) or 0.0)) if notes else []
        windows: list[tuple[float, float]] = []
        markers_sorted = sorted(markers, key=lambda m: float(m.get('time', 0.0))) if markers else []
        cur = float(start)
        for idx, mk in enumerate(markers_sorted):
            mt = float(mk.get('time', cur) or cur)
            if op_time.lt(mt, float(start)):
                continue
            if op_time.ge(mt, float(end)):
                break
            dur = float(mk.get('duration', 0.0) or 0.0)
            next_t = float(markers_sorted[idx + 1].get('time', end)) if (idx + 1) < len(markers_sorted) else float(end)
            next_t = min(float(end), next_t)
            if op_time.gt(mt, cur):
                windows.extend(_build_grid_windows(cur, mt))
            if dur > 0.0:
                windows.extend(_build_duration_windows(mt, next_t, dur))
            else:
                windows.extend(_build_grid_windows(mt, next_t))
            cur = next_t
        if op_time.lt(cur, float(end)):
            windows.extend(_build_grid_windows(cur, float(end)))
        groups = _assign_groups(notes_sorted, windows) if notes_sorted else []
        return groups, windows

    def _has_followed_rest(item: dict) -> bool:
        """Return True when a note has no immediate following note in its hand."""
        hand_key = str(item.get('hand', '<') or '<')
        hand_list = notes_by_hand.get(hand_key, [])
        starts = starts_by_hand.get(hand_key, [])
        if not hand_list or not starts:
            return True
        end = float(item.get('end', 0.0) or 0.0)
        thr = float(op_time.threshold)
        idx = bisect.bisect_left(starts, float(end - thr))
        min_delta = None
        for j in range(idx, len(hand_list)):
            m = hand_list[j]
            if int(m.get('idx', -1) or -1) == int(item.get('idx', -2) or -2):
                continue
            delta = float(m.get('time', 0.0) or 0.0) - end
            if delta >= -thr:
                min_delta = delta
                break
        if min_delta is None:
            return True
        return op_time.gt(float(min_delta), 0.0)

    # Reset pages
    try:
        du._pages = []
        du._current_index = -1
    except Exception:
        traceback.print_exc()

    def _total_score_ticks() -> float:
        """Compute total score duration in ticks from base grid segments."""
        total = 0.0
        for bg in base_grid:
            try:
                numer = int(bg.get('numerator', 4) or 4)
                denom = int(bg.get('denominator', 4) or 4)
                measures = int(bg.get('measure_amount', 1) or 1)
            except Exception:
                traceback.print_exc()
                continue
            measure_len = float(numer) * (4.0 / float(max(1, denom))) * float(QUARTER_NOTE_UNIT)
            total += measure_len * float(max(0, measures))
        return float(total)

    def _line_break_defaults() -> dict:
        """Return default line break settings used when none exist."""
        return {
            'time': 0.0,
            'margin_mm': [10.0, 10.0],
            'stave_range': 'auto',
            'page_break': False,
        }

    def _sanitize_range(rng) -> list[int]:
        """Clamp and normalize a stave range to valid piano keys."""
        if not isinstance(rng, list) or len(rng) < 2:
            return [1, PIANO_KEY_AMOUNT]
        try:
            lo = int(rng[0])
            hi = int(rng[1])
        except Exception:
            traceback.print_exc()
            return [1, PIANO_KEY_AMOUNT]
        lo = max(1, min(PIANO_KEY_AMOUNT, lo))
        hi = max(1, min(PIANO_KEY_AMOUNT, hi))
        if hi < lo:
            lo, hi = hi, lo
        return [lo, hi]

    def _pc_char(key: int) -> str:
        """Map a piano key number to a pitch-class character for grouping."""
        pc = (int(key) - 1) % 12
        if pc in (0, 2, 3, 5, 7, 8, 10):
            return {0: 'a', 2: 'b', 3: 'c', 5: 'd', 7: 'e', 8: 'f', 10: 'g'}[pc]
        return {1: 'A', 4: 'C', 6: 'D', 9: 'F', 11: 'G'}[pc]

    line_keys = sorted(key_class_filter('ACDFG'))

    def _build_line_groups() -> list[dict]:
        """Build clef-related line groups and their key ranges."""
        groups: list[dict] = []
        used: set[int] = set()

        def _next_index(start: int, pc_target: str) -> int | None:
            """Find the next unused key index matching a pitch-class target."""
            for j in range(start + 1, len(line_keys)):
                if j in used:
                    continue
                if _pc_char(line_keys[j]) == pc_target:
                    return j
            return None

        for i, key in enumerate(line_keys):
            if i in used:
                continue
            pc = _pc_char(key)
            if pc == 'C':
                keys = [key]
                j = _next_index(i, 'D')
                if j is not None:
                    keys.append(line_keys[j])
                    used.add(j)
                used.add(i)
                groups.append({'keys': keys})
            elif pc == 'F':
                keys = [key]
                j = _next_index(i, 'G')
                if j is not None:
                    keys.append(line_keys[j])
                    used.add(j)
                    k = _next_index(j, 'A')
                    if k is not None:
                        keys.append(line_keys[k])
                        used.add(k)
                used.add(i)
                groups.append({'keys': keys})

        # Sort groups by pitch
        groups.sort(key=lambda g: g['keys'][0])

        # Assign membership ranges based on midpoints between groups
        for i, grp in enumerate(groups):
            first = grp['keys'][0]
            last = grp['keys'][-1]
            if i == 0:
                low = 1
            else:
                prev_last = groups[i - 1]['keys'][-1]
                low = int((prev_last + first) // 2) + 1
            if i == len(groups) - 1:
                high = PIANO_KEY_AMOUNT
            else:
                next_first = groups[i + 1]['keys'][0]
                high = int((last + next_first) // 2)
            grp['range_low'] = int(max(1, low))
            grp['range_high'] = int(min(PIANO_KEY_AMOUNT, high))
            if 41 in grp['keys'] and 43 in grp['keys']:
                grp['pattern'] = 'c'
            elif len(grp['keys']) == 2:
                grp['pattern'] = '2'
            else:
                grp['pattern'] = '3'
        return groups

    line_groups = _build_line_groups()
    if not line_groups:
        line_groups = [{'keys': [41, 43], 'range_low': 1, 'range_high': PIANO_KEY_AMOUNT, 'pattern': 'c'}]
    clef_group_index = 0
    for i, grp in enumerate(line_groups):
        if 41 in grp['keys'] and 43 in grp['keys']:
            clef_group_index = i
            break

    def _group_index_for_key(key: int) -> int:
        """Return the line group index for a key using precomputed ranges."""
        if not line_groups:
            return 0
        for i, grp in enumerate(line_groups):
            if grp['range_low'] <= key <= grp['range_high']:
                return i
        return 0 if key <= line_groups[0]['range_low'] else len(line_groups) - 1

    def _note_range_for_window(t0: float, t1: float) -> tuple[int | None, int | None]:
        """Find the lowest and highest pitches overlapping a time window."""
        lo = None
        hi = None
        for n in notes:
            try:
                n_t = float(n.get('time', 0.0) or 0.0)
                n_d = float(n.get('duration', 0.0) or 0.0)
                n_end = n_t + n_d
                p = int(n.get('pitch', 0) or 0)
            except Exception:
                traceback.print_exc()
                continue
            if op_time.lt(n_t, t1) and op_time.gt(n_end, t0):
                if p < 1 or p > PIANO_KEY_AMOUNT:
                    continue
                lo = p if lo is None else min(lo, p)
                hi = p if hi is None else max(hi, p)
        return lo, hi

    def _visible_line_groups_for_range(lo: int, hi: int) -> list[dict]:
        """Return line groups that cover a pitch range, including clef group."""
        lo = int(max(1, min(PIANO_KEY_AMOUNT, lo)))
        hi = int(max(1, min(PIANO_KEY_AMOUNT, hi)))
        if hi < lo:
            lo, hi = hi, lo

        min_group = _group_index_for_key(lo)
        max_group = _group_index_for_key(hi)
        if clef_group_index < min_group:
            min_group = clef_group_index
        if clef_group_index > max_group:
            max_group = clef_group_index

        return [line_groups[gi] for gi in range(min_group, max_group + 1)]

    def _auto_line_keys_and_bounds(t0: float, t1: float) -> tuple[list[dict], list[int], int, int, bool, str]:
        """Choose stave keys and bounds automatically for a time window."""
        lo, hi = _note_range_for_window(t0, t1)
        if lo is None or hi is None:
            grp = line_groups[clef_group_index]
            keys = list(grp['keys'])
            return [grp], keys, int(keys[0]), int(keys[-1]), True, grp.get('pattern', 'c')
        groups = _visible_line_groups_for_range(lo, hi)
        if not groups:
            grp = line_groups[clef_group_index]
            keys = list(grp['keys'])
            return [grp], keys, int(keys[0]), int(keys[-1]), True, grp.get('pattern', 'c')
        keys: list[int] = []
        patterns: list[str] = []
        for grp in groups:
            keys.extend(grp['keys'])
            patterns.append(str(grp.get('pattern', '')))
        return groups, keys, int(keys[0]), int(keys[-1]), False, ' '.join(patterns)

    def _notes_in_window_stats(t0: float, t1: float) -> tuple[int, int | None, int | None]:
        """Return note count and pitch bounds overlapping a time window."""
        count = 0
        lo = None
        hi = None
        for n in notes:
            try:
                n_t = float(n.get('time', 0.0) or 0.0)
                n_d = float(n.get('duration', 0.0) or 0.0)
                n_end = n_t + n_d
                p = int(n.get('pitch', 0) or 0)
            except Exception:
                traceback.print_exc()
                continue
            if op_time.lt(n_t, t1) and op_time.gt(n_end, t0) and 1 <= p <= PIANO_KEY_AMOUNT:
                count += 1
                lo = p if lo is None else min(lo, p)
                hi = p if hi is None else max(hi, p)
        return count, lo, hi

    def _build_key_positions(start_key: int, end_key: int, semitone_mm: float) -> dict[int, float]:
        """Build x positions for keys, adding extra spacing after B/E."""
        positions: dict[int, float] = {}
        x = 0.0
        prev = None
        for key in range(start_key, end_key + 1):
            if prev is not None and prev in BE_KEYS:
                x += semitone_mm
            x += semitone_mm
            positions[key] = x
            prev = key
        return positions

    _log(f"-- do_engrave start pdf_export={bool(pdf_export)} --")
    try:
        pitches = [int(n.get('pitch', 0) or 0) for n in notes if isinstance(n, dict)]
        if pitches:
            _log(f"note_pitch_min={min(pitches)} max={max(pitches)}")
        else:
            _log("note_pitch_min=NA max=NA")
    except Exception:
        traceback.print_exc()
    _log(f"PIANO_KEY_AMOUNT={PIANO_KEY_AMOUNT}")
    total_ticks = _total_score_ticks()
    if total_ticks <= 0.0:
        total_ticks = float(QUARTER_NOTE_UNIT) * 4.0
    if not line_breaks:
        line_breaks = [_line_break_defaults()]

    try:
        line_breaks = sorted(line_breaks, key=lambda lb: float(lb.get('time', 0.0) or 0.0))
    except Exception:
        traceback.print_exc()

    # Build lines from line breaks
    lines = []
    for i, lb in enumerate(line_breaks):
        lb_time = float(lb.get('time', 0.0) or 0.0)
        next_time = float(line_breaks[i + 1].get('time', total_ticks) or total_ticks) if i + 1 < len(line_breaks) else total_ticks
        if next_time < lb_time:
            next_time = lb_time
        margin_mm = list(lb.get('margin_mm', [10.0, 10.0]) or [10.0, 10.0])
        if len(margin_mm) < 2:
            margin_mm = [margin_mm[0] if margin_mm else 10.0, 10.0]
        stave_range = lb.get('stave_range', 'auto')
        if stave_range is True:
            stave_range = 'auto'
        if isinstance(stave_range, list) and len(stave_range) >= 2:
            try:
                r0 = int(stave_range[0])
                r1 = int(stave_range[1])
                if (r0 == 0 and r1 == 0) or (r0 == 1 and r1 == 1):
                    stave_range = 'auto'
            except Exception:
                traceback.print_exc()
        line = {
            'time_start': lb_time,
            'time_end': next_time,
            'margin_left': float(margin_mm[0]),
            'margin_right': float(margin_mm[1]),
            'stave_range': stave_range,
            'page_break': bool(lb.get('page_break', False)),
        }
        lines.append(line)

    _log(f"lines={len(lines)} total_ticks={total_ticks:.2f} notes={len(notes)} base_grid={len(base_grid)}")

    # Calculate ranges and widths
    semitone_mm = 2.5 * scale
    key_positions = _build_key_positions(1, PIANO_KEY_AMOUNT, semitone_mm)
    for line in lines:
        if line['stave_range'] == 'auto':
            groups, keys, bound_left, bound_right, empty, pattern = _auto_line_keys_and_bounds(line['time_start'], line['time_end'])
            line['visible_keys'] = keys
            line['pattern'] = pattern
            if empty:
                count, lo, hi = _notes_in_window_stats(line['time_start'], line['time_end'])
                _log(f"auto_range_empty window={line['time_start']:.2f}..{line['time_end']:.2f} count={count} lo={lo} hi={hi}")
        else:
            manual = _sanitize_range(line['stave_range'])
            groups = _visible_line_groups_for_range(manual[0], manual[1])
            if not groups:
                grp = line_groups[clef_group_index]
                groups = [grp]
            keys: list[int] = []
            patterns: list[str] = []
            for grp in groups:
                keys.extend(grp['keys'])
                patterns.append(str(grp.get('pattern', '')))
            bound_left = int(keys[0])
            bound_right = int(keys[-1])
            line['visible_keys'] = keys
            line['pattern'] = ' '.join(patterns)
        # Special-case low register: use key 2 as the stave's left edge when keys 1-3 appear.
        low_key_present = False
        for item in norm_notes:
            n_t = float(item.get('time', 0.0) or 0.0)
            n_end = float(item.get('end', 0.0) or 0.0)
            p = int(item.get('pitch', 0) or 0)
            if op_time.ge(n_t, float(line['time_end'])) or op_time.le(n_end, float(line['time_start'])):
                continue
            if p in (1, 2, 3):
                low_key_present = True
                break
        if low_key_present:
            bound_left = 2
        line['low_key_left'] = bool(low_key_present)
        line['range'] = [int(bound_left), int(bound_right)]
        min_pos = key_positions.get(bound_left, 0.0)
        max_pos = key_positions.get(bound_right, min_pos)
        stave_width = max(0.0, max_pos - min_pos)
        line['stave_width'] = float(stave_width)
        base_margin_left = float(line.get('margin_left', 0.0) or 0.0)
        ts_lane_width = 0.0
        ts_lane_right_offset = 0.0
        ts_segments_in_line = [
            seg
            for seg in ts_segments
            if op_time.ge(float(seg.get('start', 0.0) or 0.0), float(line['time_start']))
            and op_time.lt(float(seg.get('start', 0.0) or 0.0), float(line['time_end']))
        ]
        if ts_segments_in_line:
            ts_lane_width = float(layout.get('time_signature_indicator_lane_width_mm', 22.0) or 22.0)
            min_pitch = None
            for seg in ts_segments_in_line:
                win_start = float(seg.get('start', 0.0) or 0.0)
                win_end = win_start + float(seg.get('measure_len', 0.0) or 0.0)
                for item in norm_notes:
                    n_t = float(item.get('time', 0.0) or 0.0)
                    n_end = float(item.get('end', 0.0) or 0.0)
                    if op_time.ge(n_t, float(line['time_end'])) or op_time.le(n_end, float(line['time_start'])):
                        continue
                    if op_time.lt(n_t, win_end) and op_time.gt(n_end, win_start):
                        p = int(item.get('pitch', 0) or 0)
                        if 1 <= p <= PIANO_KEY_AMOUNT:
                            min_pitch = p if min_pitch is None else min(min_pitch, p)
            if min_pitch is not None:
                stem_len_units = float(layout.get('note_stem_length_semitone', 3) or 3)
                stem_len_mm = stem_len_units * semitone_mm
                origin = float(key_positions.get(bound_left, 0.0))
                note_offset = float(key_positions.get(min_pitch, origin)) - origin
                offset_left = note_offset - stem_len_mm
                ts_lane_right_offset = min(0.0, float(offset_left))
            extra_left = max(0.0, -ts_lane_right_offset)
            line['margin_left'] = base_margin_left + ts_lane_width + extra_left
        line['base_margin_left'] = base_margin_left
        line['ts_lane_width'] = ts_lane_width
        line['ts_lane_right_offset'] = ts_lane_right_offset
        line['total_width'] = float(line['margin_left'] + stave_width + line['margin_right'])
        line['bound_left'] = int(bound_left)
        line['bound_right'] = int(bound_right)

    # Assign lines to pages
    available_width = max(1e-6, page_w - page_left - page_right)
    pages: list[list[dict]] = []
    cur_page: list[dict] = []
    cur_width = 0.0
    for line in lines:
        if line.get('page_break', False) and cur_page:
            pages.append(cur_page)
            cur_page = []
            cur_width = 0.0
        if cur_page and (cur_width + float(line['total_width'])) > available_width:
            pages.append(cur_page)
            cur_page = []
            cur_width = 0.0
        cur_page.append(line)
        cur_width += float(line['total_width'])
    if cur_page:
        pages.append(cur_page)

    _log(f"pages={len(pages)} available_width={available_width:.2f}")

    # Draw staves per page
    if not pages:
        pages = [[]]
    for page_index, page in enumerate(pages):
        du.new_page(page_w, page_h)
        _log(f"page_lines={len(page)}")
        footer_height = float(layout.get('footer_height_mm', 0.0) or 0.0)
        footer_height = max(0.0, footer_height)
        if page_index == 0:
            title_text = _header_text('title', 'title')
            composer_text = _header_text('composer', 'composer')
            title_family, title_size, title_bold, title_italic, title_x_off, title_y_off = _header_font(
                'title',
                'Times New Roman',
                12.0,
            )
            composer_family, composer_size, composer_bold, composer_italic, composer_x_off, composer_y_off = _header_font(
                'composer',
                'Times New Roman',
                10.0,
            )
            du.add_text(
                page_left + title_x_off,
                page_top + title_y_off,
                title_text,
                family=title_family,
                size_pt=title_size,
                bold=title_bold,
                italic=title_italic,
                color=(0, 0, 0, 1),
                id=0,
                tags=['title'],
                anchor='nw',
            )
            du.add_text(
                (page_w - page_right) + composer_x_off,
                page_top + composer_y_off,
                composer_text,
                family=composer_family,
                size_pt=composer_size,
                bold=composer_bold,
                italic=composer_italic,
                color=(0, 0, 0, 1),
                id=0,
                tags=['composer'],
                anchor='ne',
            )
        if footer_height > 0.0:
            footer_text = _header_text('copyright', f"keyTAB all copyrights reserved {datetime.now().year}")
            footer_family, footer_size, footer_bold, footer_italic, footer_x_off, footer_y_off = _header_font(
                'copyright',
                'Times New Roman',
                8.0,
            )
            du.add_text(
                page_left + footer_x_off,
                (page_h - page_bottom) + footer_y_off,
                f"Page {page_index + 1} of {len(pages)} | {footer_text}",
                family=footer_family,
                size_pt=footer_size,
                bold=footer_bold,
                italic=footer_italic,
                color=(0, 0, 0, 1),
                id=0,
                tags=['copyright'],
                anchor='sw',
            )
        if not page:
            continue
        used_width = sum(float(l['total_width']) for l in page)
        leftover = max(0.0, available_width - used_width)
        gap = leftover / float(len(page) + 1)
        x_cursor = page_left + gap
        for line in page:
            _log(
                "line time=%.2f..%.2f range=%s total_w=%.2f pattern=%s"
                % (
                    float(line.get('time_start', 0.0)),
                    float(line.get('time_end', 0.0)),
                    str(line.get('range', None)),
                    float(line.get('total_width', 0.0)),
                    str(line.get('pattern', '')),
                )
            )
            line_x_start = x_cursor + float(line['margin_left'])
            line_x_end = line_x_start + float(line['stave_width'])
            header_offset = 0.0
            if page_index == 0:
                header_offset = float(layout.get('header_height_mm', 0.0) or 0.0)
            y1 = page_top + header_offset
            y2 = float(page_h - page_bottom - footer_height)
            if y2 <= y1:
                y2 = y1 + 1.0
            line['y_top'] = y1
            line['y_bottom'] = y2

            bound_left = int(line.get('bound_left', line['range'][0]))
            bound_right = int(line.get('bound_right', line['range'][1]))
            origin = float(key_positions.get(bound_left, 0.0))
            manual_range = isinstance(line.get('stave_range'), list) and len(line.get('stave_range')) >= 2
            bound_group_low = _group_index_for_key(bound_left) if manual_range else None
            bound_group_high = _group_index_for_key(bound_right) if manual_range else None
            ledger_drawn: set[tuple[int, int]] = set()

            def _key_to_x(key: int) -> float:
                return line_x_start + (float(key_positions.get(key, 0.0)) - origin)

            def _time_to_y(ticks: float) -> float:
                total = max(1e-6, float(line['time_end'] - line['time_start']))
                rel = (float(ticks) - float(line['time_start'])) / total
                rel = max(0.0, min(1.0, rel))
                return y1 + (y2 - y1) * rel

            tick_per_mm = (float(line['time_end'] - line['time_start'])) / max(1e-6, (y2 - y1))
            mm_per_quarter = float(QUARTER_NOTE_UNIT) / max(1e-6, tick_per_mm)

            indicator_type = str(layout.get('time_signature_indicator_type', 'classical') or 'classical')
            classic_family, classic_size, classic_bold, classic_italic = _layout_font(
                'time_signature_indicator_classic_font',
                'C059',
                35.0,
            )
            klav_family, klav_size, klav_bold, klav_italic = _layout_font(
                'time_signature_indicator_klavarskribo_font',
                'C059',
                25.0,
            )
            guide_thickness = float(layout.get('time_signature_indicator_guide_thickness_mm', 0.5) or 0.5) * scale
            divider_thickness = float(layout.get('time_signature_indicator_divide_guide_thickness_mm', 1.0) or 1.0) * scale
            classic_size_pt = classic_size * scale
            klav_size_pt = klav_size * scale

            def _ts_color(enabled: bool) -> tuple[float, float, float, float]:
                return (0.0, 0.0, 0.0, 1.0) if enabled else (0.6, 0.6, 0.6, 1.0)

            def _draw_classical_ts(numerator: int, denominator: int, enabled: bool, y_mm: float) -> None:
                color = _ts_color(enabled)
                x = ts_x_right
                size_pt = classic_size_pt
                du.add_text(
                    x,
                    y_mm - (3.0 * scale),
                    f"{int(numerator)}",
                    size_pt=size_pt,
                    color=color,
                    id=0,
                    tags=["time_signature"],
                    anchor='s',
                    family=classic_family,
                    bold=classic_bold,
                    italic=classic_italic,
                )
                du.add_line(
                    x - (3.0 * scale),
                    y_mm,
                    x + (3.0 * scale),
                    y_mm,
                    color=color,
                    width_mm=divider_thickness,
                    id=0,
                    tags=["time_signature_line"],
                    dash_pattern=None,
                )
                du.add_text(
                    x,
                    y_mm + (3.0 * scale),
                    f"{int(denominator)}",
                    size_pt=size_pt,
                    color=color,
                    id=0,
                    tags=["time_signature"],
                    anchor='n',
                    family=classic_family,
                    bold=classic_bold,
                    italic=classic_italic,
                )

            def _draw_klavars_ts(numerator: int, denominator: int, enabled: bool, y_mm: float, grid_positions: list[int]) -> None:
                color = _ts_color(enabled)
                quarters_per_measure = float(numerator) * (4.0 / max(1.0, float(denominator)))
                measure_len_mm = quarters_per_measure * mm_per_quarter
                beat_len_mm = measure_len_mm / max(1, int(numerator))

                seq = [int(p) for p in (grid_positions or []) if 1 <= int(p) <= 9]
                if len(seq) != int(numerator):
                    seq = list(range(1, int(numerator) + 1))

                guide_half_len = min(ts_col_w * 0.45, 3.0 * scale) if ts_col_w > 0.0 else (3.0 * scale)
                guide_width_mm = guide_thickness
                for k, val in enumerate(seq, start=1):
                    y = y_mm + (k - 1) * beat_len_mm
                    du.add_line(
                        ts_x_right - guide_half_len,
                        y,
                        ts_x_right + guide_half_len,
                        y,
                        color=color,
                        width_mm=guide_width_mm,
                        id=0,
                        tags=["ts_klavars_guide"],
                        dash_pattern=None,
                    )
                du.add_line(
                    ts_x_right - guide_half_len,
                    y_mm + measure_len_mm,
                    ts_x_right + guide_half_len,
                    y_mm + measure_len_mm,
                    color=color,
                    width_mm=guide_width_mm,
                    id=0,
                    tags=["ts_klavars_guide"],
                    dash_pattern=None,
                )

                for k, val in enumerate(seq, start=1):
                    y = y_mm + (k - 1) * beat_len_mm
                    du.add_text(
                        ts_x_mid,
                        y,
                        str(val),
                        size_pt=klav_size_pt,
                        color=color,
                        id=0,
                        tags=["ts_klavars_mid"],
                        anchor='center',
                        family=klav_family,
                        bold=klav_bold,
                        italic=klav_italic,
                    )
                du.add_text(
                    ts_x_mid,
                    y_mm + measure_len_mm,
                    "1",
                        size_pt=klav_size_pt,
                    color=color,
                    id=0,
                    tags=["ts_klavars_mid"],
                    anchor='center',
                        family=klav_family,
                        bold=klav_bold,
                        italic=klav_italic,
                )
                group_starts = [i for i, v in enumerate(seq, start=1) if v == 1]
                if not group_starts or group_starts[0] != 1:
                    group_starts = [1] + group_starts
                for gi, s in enumerate(group_starts, start=1):
                    y = y_mm + (s - 1) * beat_len_mm
                    du.add_text(
                        ts_x_left,
                        y,
                        str(gi),
                        size_pt=klav_size_pt,
                        color=color,
                        id=0,
                        tags=["ts_klavars_left"],
                        anchor='center',
                        family=klav_family,
                        bold=klav_bold,
                        italic=klav_italic,
                    )

            # Grid drawing based on base_grid (barlines and beat lines)
            grid_left = line_x_start
            grid_right = line_x_start + float(line['stave_width'])
            ts_right_margin = max(0.0, 1.5 * scale)
            ts_lane_width = float(line.get('ts_lane_width', 0.0) or 0.0)
            if ts_lane_width > 0.0:
                ts_lane_right = line_x_start + float(line.get('ts_lane_right_offset', 0.0) or 0.0)
                ts_lane_left = ts_lane_right - ts_lane_width
                ts_left_edge = ts_lane_left
                ts_right_bound = ts_lane_right
            else:
                ts_indicator_width = max(0.0, float(line.get('margin_left', 0.0) or 0.0) - ts_right_margin)
                ts_left_edge = grid_left - ts_right_margin - ts_indicator_width
                ts_right_bound = (grid_left - ts_right_margin) - 5.0
            ts_usable = max(0.0, ts_right_bound - ts_left_edge)
            ts_col_w = ts_usable / 3.0 if ts_usable > 0.0 else 0.0
            ts_x_left = ts_left_edge + (ts_col_w * 0.5)
            ts_x_mid = ts_left_edge + (ts_col_w * 1.5)
            ts_x_right = ts_left_edge + (ts_col_w * 2.5)
            grid_color = (0, 0, 0, 1)
            bar_width_mm = float(layout.get('grid_barline_thickness_mm', 0.25) or 0.25) * scale
            grid_width_mm = float(layout.get('grid_gridline_thickness_mm', 0.15) or 0.15) * scale
            dash_pattern = list(layout.get('grid_gridline_dash_pattern_mm', []) or [])
            if dash_pattern:
                dash_pattern = [float(v) * scale for v in dash_pattern]
            time_cursor = 0.0
            for bg in base_grid:
                try:
                    numerator = int(bg.get('numerator', 4) or 4)
                    denominator = int(bg.get('denominator', 4) or 4)
                    measure_amount = int(bg.get('measure_amount', 1) or 1)
                    beat_grouping = list(bg.get('beat_grouping', []) or [])
                    indicator_enabled = bool(bg.get('indicator_enabled', True))
                except Exception:
                    traceback.print_exc()
                    continue
                if measure_amount <= 0:
                    continue
                measure_len = float(numerator) * (4.0 / float(max(1, denominator))) * float(QUARTER_NOTE_UNIT)
                beat_len = measure_len / max(1, int(numerator))
                if op_time.ge(float(time_cursor), float(line['time_start'])) and op_time.lt(float(time_cursor), float(line['time_end'])):
                    y_ts = _time_to_y(float(time_cursor))
                    if indicator_type == 'classical':
                        _draw_classical_ts(numerator, denominator, indicator_enabled, y_ts)
                    elif indicator_type == 'klavarskribo':
                        _draw_klavars_ts(numerator, denominator, indicator_enabled, y_ts, beat_grouping)
                    elif indicator_type == 'both':
                        _draw_classical_ts(numerator, denominator, indicator_enabled, y_ts)
                        _draw_klavars_ts(numerator, denominator, indicator_enabled, y_ts, beat_grouping)
                for _ in range(measure_amount):
                    if op_time.gt(time_cursor, float(line['time_end'])):
                        break
                    full_group = len(beat_grouping) == int(numerator) and [int(v) for v in beat_grouping] == list(range(1, int(numerator) + 1))
                    for idx in range(int(numerator)):
                        t = float(time_cursor + (beat_len * idx))
                        if op_time.lt(t, float(line['time_start'])) or op_time.gt(t, float(line['time_end'])):
                            continue
                        y = _time_to_y(t)
                        if idx == 0:
                            du.add_line(
                                grid_left,
                                y,
                                grid_right,
                                y,
                                color=grid_color,
                                width_mm=bar_width_mm,
                                id=0,
                                tags=['grid_line'],
                                dash_pattern=None,
                            )
                            if full_group:
                                continue
                        else:
                            group_val = beat_grouping[idx] if idx < len(beat_grouping) else (idx + 1)
                            if full_group or int(group_val) == 1:
                                du.add_line(
                                    grid_left,
                                    y,
                                    grid_right,
                                    y,
                                    color=grid_color,
                                    width_mm=max(0.1, grid_width_mm),
                                    id=0,
                                    tags=['grid_line'],
                                    dash_pattern=dash_pattern or [2.0 * scale, 2.0 * scale],
                                )
                    time_cursor += measure_len
                if op_time.gt(time_cursor, float(line['time_end'])):
                    break

            if op_time.ge(total_ticks, float(line['time_start'])) and op_time.le(total_ticks, float(line['time_end'])):
                y_end_bar = _time_to_y(float(total_ticks))
                du.add_line(
                    grid_left,
                    y_end_bar,
                    grid_right,
                    y_end_bar,
                    color=grid_color,
                    width_mm=bar_width_mm * 2.0,
                    id=0,
                    tags=['grid_line'],
                    dash_pattern=None,
                )

            # Count line drawing (no handles)
            if bool(layout.get('countline_visible', True)) and count_lines:
                dash_pattern = list(layout.get('countline_dash_pattern', []) or [])
                if dash_pattern:
                    dash_pattern = [float(v) * scale for v in dash_pattern]
                countline_w = float(layout.get('countline_thickness_mm', 0.5) or 0.5) * scale
                for ev in count_lines:
                    try:
                        t0 = float(ev.get('time', 0.0) or 0.0)
                        p1 = int(ev.get('pitch1', 40) or 40)
                        p2 = int(ev.get('pitch2', 44) or 44)
                    except Exception:
                        traceback.print_exc()
                        continue
                    if op_time.lt(t0, float(line['time_start'])) or op_time.gt(t0, float(line['time_end'])):
                        continue
                    x1 = _key_to_x(p1)
                    x2 = _key_to_x(p2)
                    if x2 < x1:
                        x1, x2 = x2, x1
                    y_mm = _time_to_y(t0)
                    du.add_line(
                        x1,
                        y_mm,
                        x2,
                        y_mm,
                        color=(0, 0, 0, 1),
                        width_mm=countline_w,
                        dash_pattern=dash_pattern or [0.0, 1.5 * scale],
                        id=int(ev.get('_id', 0) or 0),
                        tags=['count_line'],
                    )

            line_notes: list[dict] = []
            for item in norm_notes:
                n_t = float(item.get('time', 0.0) or 0.0)
                n_end = float(item.get('end', 0.0) or 0.0)
                p = int(item.get('pitch', 0) or 0)
                if op_time.ge(n_t, float(line['time_end'])) or op_time.le(n_end, float(line['time_start'])):
                    continue
                if p < 1 or p > PIANO_KEY_AMOUNT:
                    continue
                line_notes.append(item)

            notes_by_hand_line: dict[str, list[dict]] = {'l': [], 'r': []}
            for item in line_notes:
                hk = str(item.get('hand', '<') or '<')
                hand_norm = 'l' if hk in ('<', 'l') else 'r'
                notes_by_hand_line[hand_norm].append(item)

            beam_groups_by_hand: dict[str, tuple[list[list[dict]], list[tuple[float, float]]]] = {}
            line_start = float(line.get('time_start', 0.0) or 0.0)
            line_end = float(line.get('time_end', 0.0) or 0.0)
            for hand_norm in ('r', 'l'):
                notes_for_hand = notes_by_hand_line.get(hand_norm, [])
                markers_for_hand = beam_by_hand.get(hand_norm, [])
                groups, windows = _group_by_beam_markers(notes_for_hand, markers_for_hand, line_start, line_end)
                beam_groups_by_hand[hand_norm] = (groups, windows)

            # Measure numbering with collision avoidance
            mn_family, mn_size, mn_bold, mn_italic = _layout_font('measure_numbering_font', 'C059', 10.0)
            size_pt = mn_size
            mm_per_pt = 25.4 / 72.0
            text_h_mm = size_pt * mm_per_pt
            measure_pad = 1.5
            stem_len_units = float(layout.get('note_stem_length_semitone', 3) or 3)
            stem_len_mm = stem_len_units * semitone_mm

            def _note_x_range(it: dict) -> tuple[float, float]:
                p = int(it.get('pitch', 0) or 0)
                x = _key_to_x(p)
                w = semitone_mm
                hand_key = str(it.get('hand', '<') or '<')
                beam_ext = semitone_mm
                if hand_key in ('l', '<'):
                    x_min = x - max(w, stem_len_mm + beam_ext)
                    x_max = x + w
                else:
                    x_min = x - w
                    x_max = x + max(w, stem_len_mm + beam_ext)
                return (x_min, x_max)

            def _right_extent(t0: float, t1: float) -> float:
                max_x = grid_right
                for it in line_notes:
                    nt = float(it.get('time', 0.0) or 0.0)
                    ne = float(it.get('end', 0.0) or 0.0)
                    if op_time.ge(nt, float(t1)) or op_time.le(ne, float(t0)):
                        continue
                    _x0, x1 = _note_x_range(it)
                    if x1 > max_x:
                        max_x = x1
                return max_x

            def _beam_group_right_extent(t0: float) -> float | None:
                max_x = None
                for hand_norm, payload in beam_groups_by_hand.items():
                    groups, windows = payload
                    for idx, grp in enumerate(groups):
                        if not grp or idx >= len(windows):
                            continue
                        w0, w1 = windows[idx]
                        if op_time.ge(float(t0), float(w1)) or op_time.lt(float(t0), float(w0)):
                            continue
                        highest = max(grp, key=lambda n: int(n.get('pitch', 0) or 0))
                        p = int(highest.get('pitch', 0) or 0)
                        base_x = _key_to_x(p)
                        if hand_norm == 'r':
                            x = base_x + stem_len_mm
                        else:
                            x = base_x + semitone_mm
                        if max_x is None or x > max_x:
                            max_x = x
                return max_x

            def _collides(x0: float, x1: float, t0: float, t1: float) -> bool:
                for it in line_notes:
                    nt = float(it.get('time', 0.0) or 0.0)
                    ne = float(it.get('end', 0.0) or 0.0)
                    if op_time.ge(nt, float(t1)) or op_time.le(ne, float(t0)):
                        continue
                    nx0, nx1 = _note_x_range(it)
                    if (nx1 >= x0) and (nx0 <= x1):
                        return True
                return False

            for mw in measure_windows:
                m_start = float(mw.get('start', 0.0))
                m_end = float(mw.get('end', 0.0))
                if op_time.ge(m_start, float(line['time_end'])) or op_time.le(m_end, float(line['time_start'])):
                    continue
                num_txt = str(int(mw.get('number', 0) or 0))
                if not num_txt:
                    continue
                text_w_mm = max(1.0, text_h_mm * 0.6 * len(num_txt))
                t0 = m_start
                t1 = min(float(line['time_end']), m_start + (text_h_mm * tick_per_mm))
                y_text = _time_to_y(t0) + 1.0

                # Default outside-right; only move further right on collision
                base_right = grid_right + measure_pad
                beam_right = _beam_group_right_extent(t0)
                needed_right = _right_extent(t0, t1) + measure_pad
                if beam_right is not None:
                    needed_right = max(needed_right, float(beam_right) + measure_pad)
                x_pos = max(base_right, needed_right)
                x0 = x_pos
                x1 = x_pos + text_w_mm
                step = text_w_mm + measure_pad
                tries = 0
                while _collides(x0, x1, t0, t1) and tries < 6:
                    x_pos += step
                    x0 = x_pos
                    x1 = x_pos + text_w_mm
                    tries += 1
                guide_y = _time_to_y(t0)
                du.add_line(
                    grid_right,
                    guide_y,
                    x_pos + text_w_mm,
                    guide_y,
                    color=(0, 0, 0, 1),
                    width_mm=max(0.12, 0.15 * scale),
                    id=0,
                    tags=['measure_number_guide'],
                    dash_pattern=[0.8 * scale, 0.8 * scale],
                )
                du.add_text(
                    x_pos,
                    y_text,
                    num_txt,
                    size_pt=size_pt,
                    color=(0, 0, 0, 1),
                    id=0,
                    tags=['measure_number'],
                    anchor='nw',
                    family=mn_family,
                    bold=mn_bold,
                    italic=mn_italic,
                )

            visible_keys = list(line.get('visible_keys', []))
            if not visible_keys:
                visible_keys = [k for k in range(int(line['range'][0]), int(line['range'][1]) + 1) if k in line_keys]
            # Special-case low register: draw A#0 (key 2) line when keys 1-3 appear.
            low_key_present = bool(line.get('low_key_left', False))
            if low_key_present:
                x_pos = _key_to_x(2)
                width_mm = max(stave_three_w, semitone_mm / 3.0)
                du.add_line(
                    x_pos,
                    y1,
                    x_pos,
                    y2,
                    color=(0, 0, 0, 1),
                    width_mm=width_mm,
                    dash_pattern=None,
                    id=0,
                    tags=['stave'],
                )
            for key in visible_keys:
                if low_key_present and int(key) == 2:
                    continue
                x_pos = _key_to_x(key)
                is_clef_line = key in (41, 43)
                is_three_line = key in key_class_filter('FGA')
                if is_clef_line:
                    width_mm = max(stave_two_w, semitone_mm / 6.0)
                    dash = clef_dash if clef_dash else [2.0 * scale, 2.0 * scale]
                elif is_three_line:
                    width_mm = max(stave_three_w, semitone_mm / 3.0)
                    dash = None
                else:
                    width_mm = max(stave_two_w, semitone_mm / 10.0)
                    dash = None
                _log(f"Drawing line key={key} x={x_pos:.2f}mm w={width_mm:.2f}mm")
                du.add_line(x_pos, y1, x_pos, y2, color=(0, 0, 0, 1), width_mm=width_mm, dash_pattern=dash, id=0, tags=['stave'])

            # ---- Beam drawing per line ----
            if bool(layout.get('beam_visible', True)):
                notes_by_hand_line: dict[str, list[dict]] = {'l': [], 'r': []}
                for item in line_notes:
                    hk = str(item.get('hand', '<') or '<')
                    hand_norm = 'l' if hk in ('<', 'l') else 'r'
                    notes_by_hand_line[hand_norm].append(item)

                stem_len_units = float(layout.get('note_stem_length_semitone', 3) or 3)
                layout_stem_len = stem_len_units * semitone_mm
                beam_w = float(layout.get('beam_thickness_mm', 1.0) or 1.0) * scale
                stem_w = float(layout.get('note_stem_thickness_mm', 0.5) or 0.5) * scale
                line_start = float(line.get('time_start', 0.0) or 0.0)
                line_end = float(line.get('time_end', 0.0) or 0.0)

                for hand_norm in ('r', 'l'):
                    notes_for_hand = notes_by_hand_line.get(hand_norm, [])
                    markers_for_hand = beam_by_hand.get(hand_norm, [])
                    groups, windows = _group_by_beam_markers(notes_for_hand, markers_for_hand, line_start, line_end)
                    for idx, grp in enumerate(groups):
                        if not grp:
                            continue
                        t0, t1 = windows[idx] if idx < len(windows) else (line_start, line_end)
                        starts_in = [float(n.get('time', 0.0) or 0.0) for n in grp if op_time.ge(float(n.get('time', 0.0) or 0.0), float(t0)) and op_time.lt(float(n.get('time', 0.0) or 0.0), float(t1))]
                        if not starts_in:
                            continue
                        s_min, s_max = min(starts_in), max(starts_in)
                        if op_time.eq(float(s_min), float(s_max)):
                            continue
                        t_first = min(starts_in)
                        t_last = max(starts_in)
                        if hand_norm == 'r':
                            highest = max(grp, key=lambda n: int(n.get('pitch', 0) or 0))
                            x1 = _key_to_x(int(highest.get('pitch', 0) or 0)) + float(layout_stem_len)
                            x2 = x1 + float(semitone_mm)
                        else:
                            lowest = min(grp, key=lambda n: int(n.get('pitch', 0) or 0))
                            x1 = _key_to_x(int(lowest.get('pitch', 0) or 0)) - float(layout_stem_len)
                            x2 = x1 - float(semitone_mm)
                        yb1 = _time_to_y(float(t_first))
                        yb2 = _time_to_y(float(t_last))
                        du.add_line(
                            x1,
                            yb1,
                            x2,
                            yb2,
                            color=(0, 0, 0, 1),
                            width_mm=max(0.2, beam_w),
                            id=0,
                            tags=['beam'],
                        )
                        for m in grp:
                            mt = float(m.get('time', t_first) or t_first)
                            if not (op_time.ge(mt, float(t0)) and op_time.lt(mt, float(t1))):
                                continue
                            y_note = _time_to_y(float(mt))
                            if hand_norm == 'r':
                                x_tip = _key_to_x(int(m.get('pitch', 0) or 0)) + float(layout_stem_len)
                            else:
                                x_tip = _key_to_x(int(m.get('pitch', 0) or 0)) - float(layout_stem_len)
                            if abs(yb2 - yb1) > 1e-6:
                                t_ratio = (y_note - yb1) / (yb2 - yb1)
                                x_on_beam = x1 + t_ratio * (x2 - x1)
                            else:
                                x_on_beam = x1
                            du.add_line(
                                x_tip,
                                y_note,
                                float(x_on_beam),
                                y_note,
                                color=(0, 0, 0, 1),
                                width_mm=max(0.15, stem_w),
                                id=0,
                                tags=['beam_stem'],
                            )

            for item in line_notes:
                n_t = float(item.get('time', 0.0) or 0.0)
                n_end = float(item.get('end', 0.0) or 0.0)
                p = int(item.get('pitch', 0) or 0)
                hand_key = str(item.get('hand', '<') or '<')
                n = item.get('raw', {}) or {}
                x = _key_to_x(p)
                y_start = _time_to_y(n_t)
                y_end = _time_to_y(n_end)
                if y_end < y_start:
                    y_start, y_end = y_end, y_start
                w = semitone_mm
                note_y = y_start
                if p in BLACK_KEYS and str(layout.get('black_note_rule', 'below_stem')) == 'above_stem':
                    note_y = y_start - (w * 2.0)
                # Draw midi-note body
                raw_color = n.get('midinote_color', None)
                if raw_color in (None, ''):
                    raw_color = n.get('hand', '<')
                midicol = _normalize_hex_color(raw_color)
                if midicol == '<':
                    base = _normalize_hex_color(layout.get('note_midinote_left_color', '#cccccc'))
                elif midicol == '>':
                    base = _normalize_hex_color(layout.get('note_midinote_right_color', '#cccccc'))
                elif midicol:
                    base = midicol
                else:
                    fallback = 'note_midinote_left_color' if hand_key in ('l', '<') else 'note_midinote_right_color'
                    base = _normalize_hex_color(layout.get(fallback, '#cccccc'))
                if not base:
                    base = '#cccccc'
                fill = _hex_to_rgba01(base, 1.0)
                if bool(layout.get('note_midinote_visible', True)):
                    du.add_polygon(
                        [
                            (x, y_start),
                            (x - w, y_start + semitone_mm),
                            (x - w, y_end),
                            (x + w, y_end),
                            (x + w, y_start + semitone_mm),
                        ],
                        stroke_color=None,
                        fill_color=fill,
                        id=int(item.get('id', 0) or 0),
                        tags=['midi_note'],
                    )

                on_barline = False
                for bt in barline_positions:
                    if op_time.eq(float(bt), n_t):
                        on_barline = True
                        break
                if on_barline:
                    stem_len_units = float(layout.get('note_stem_length_semitone', 3) or 3)
                    stem_len = stem_len_units * semitone_mm
                    thickness = float(layout.get('grid_barline_thickness_mm', 0.25) or 0.25) * scale
                    if hand_key in ('l', '<'):
                        x1 = x
                        x2 = x + (w * 2.0)
                        x3 = x - stem_len
                    else:
                        x1 = x
                        x2 = x - (w * 2.0)
                        x3 = x + stem_len
                    du.add_line(
                        x1,
                        y_start,
                        x2,
                        y_start,
                        color=(1, 1, 1, 1),
                        width_mm=thickness,
                        line_cap="butt",
                        id=0,
                        tags=['hand_split'],
                    )
                    du.add_line(
                        x3,
                        y_start,
                        x2,
                        y_start,
                        color=(1, 1, 1, 1),
                        width_mm=thickness,
                        line_cap="butt",
                        id=0,
                        tags=['hand_split'],
                    )

                # Draw notehead
                if bool(layout.get('note_head_visible', True)):
                    outline_w = float(layout.get('note_stem_thickness_mm', 0.5) or 0.5) * scale
                    if p in BLACK_KEYS:
                        du.add_oval(
                            x - (w * 0.8),
                            note_y,
                            x + (w * 0.8),
                            note_y + (w * 2.0),
                            stroke_color=(0, 0, 0, 1),
                            stroke_width_mm=0.3,
                            fill_color=(0, 0, 0, 1),
                            id=int(item.get('id', 0) or 0),
                            tags=['notehead_black'],
                        )
                    else:
                        du.add_oval(
                            x - w,
                            note_y,
                            x + w,
                            note_y + (w * 2.0),
                            stroke_color=(0, 0, 0, 1),
                            stroke_width_mm=outline_w,
                            fill_color=(1, 1, 1, 1),
                            id=int(item.get('id', 0) or 0),
                            tags=['notehead_white'],
                        )

                # Draw stem
                if bool(layout.get('note_stem_visible', True)):
                    stem_len_units = float(layout.get('note_stem_length_semitone', 3) or 3)
                    stem_len = stem_len_units * semitone_mm
                    stem_w = float(layout.get('note_stem_thickness_mm', 0.5) or 0.5) * scale
                    x2 = x - stem_len if hand_key in ('l', '<') else x + stem_len
                    du.add_line(
                        x,
                        y_start,
                        x2,
                        y_start,
                        color=(0, 0, 0, 1),
                        width_mm=stem_w,
                        id=0,
                        tags=['stem'],
                    )

                # Draw left-hand dot
                if bool(layout.get('note_leftdot_visible', True)) and hand_key in ('l', '<'):
                    w2 = w * 2.0
                    dot_d = w2 * 0.35
                    cy = note_y + (w2 / 2.0)
                    fill = (1, 1, 1, 1) if p in BLACK_KEYS else (0, 0, 0, 1)
                    du.add_oval(
                        x - (dot_d / 3.0),
                        cy - (dot_d / 3.0),
                        x + (dot_d / 3.0),
                        cy + (dot_d / 3.0),
                        stroke_color=None,
                        fill_color=fill,
                        id=0,
                        tags=['left_dot'],
                    )

                # Draw ledger lines when manual range trims the stave
                if manual_range:
                    ledger_groups: list[dict] = []
                    if p < bound_left:
                        g_start = _group_index_for_key(p)
                        g_end = int(bound_group_low or 0) - 1
                        if g_start <= g_end:
                            ledger_groups = line_groups[g_start:g_end + 1]
                    elif p > bound_right:
                        g_start = int(bound_group_high or 0) + 1
                        g_end = _group_index_for_key(p)
                        if g_start <= g_end:
                            ledger_groups = line_groups[g_start:g_end + 1]
                    if ledger_groups:
                        y_center = note_y + w
                        seg_half = w
                        y_seg1 = y_center - seg_half
                        y_seg2 = y_center + seg_half + seg_half + (seg_half / 2.0)
                        for grp in ledger_groups:
                            for key in grp.get('keys', []):
                                x_pos = _key_to_x(int(key))
                                is_clef_line = int(key) in (41, 43)
                                is_three_line = int(key) in key_class_filter('FGA')
                                if is_clef_line:
                                    width_mm = max(stave_two_w, semitone_mm / 6.0)
                                    dash = clef_dash if clef_dash else [2.0 * scale, 2.0 * scale]
                                elif is_three_line:
                                    width_mm = max(stave_three_w, semitone_mm / 3.0)
                                    dash = None
                                else:
                                    width_mm = max(stave_two_w, semitone_mm / 10.0)
                                    dash = None
                                key_sig = (int(key), int(round(y_center * 1000)))
                                if key_sig in ledger_drawn:
                                    continue
                                ledger_drawn.add(key_sig)
                                du.add_line(
                                    x_pos,
                                    y_seg1,
                                    x_pos,
                                    y_seg2,
                                    color=(0, 0, 0, 1),
                                    width_mm=width_mm,
                                    dash_pattern=dash,
                                    id=0,
                                    tags=['stave'],
                                )

                # Draw note continuation dots (same rules as editor; uses scaled semitone size).
                dot_times: list[float] = []
                for m in line_notes:
                    if int(m.get('idx', -1) or -1) == int(item.get('idx', -2) or -2):
                        continue
                    if str(m.get('hand', '<') or '<') != hand_key:
                        continue
                    s = float(m.get('time', 0.0) or 0.0)
                    e = float(m.get('end', 0.0) or 0.0)
                    if op_time.gt(s, n_t) and op_time.lt(s, n_end):
                        dot_times.append(s)
                    if op_time.gt(e, n_t) and op_time.lt(e, n_end):
                        dot_times.append(e)
                for bt in barline_positions:
                    bt = float(bt)
                    if op_time.gt(bt, n_t) and op_time.lt(bt, n_end):
                        dot_times.append(bt)
                if dot_times:
                    dot_d = w * 0.8
                    for t in sorted(set(dot_times)):
                        y_center = _time_to_y(float(t)) + w
                        du.add_oval(
                            x - dot_d / 2.0,
                            y_center - dot_d / 2.0,
                            x + dot_d / 2.0,
                            y_center + dot_d / 2.0,
                            fill_color=(0, 0, 0, 1),
                            stroke_color=None,
                            id=0,
                            tags=['left_dot'],
                        )

                # Draw chord connect stem
                same_time = [m for m in line_notes if str(m.get('hand', '<') or '<') == hand_key and op_time.eq(float(m.get('time', 0.0) or 0.0), n_t)]
                if len(same_time) >= 2:
                    lowest = min(same_time, key=lambda m: int(m.get('pitch', 0) or 0))
                    highest = max(same_time, key=lambda m: int(m.get('pitch', 0) or 0))
                    if int(lowest.get('id', 0) or 0) == int(item.get('id', 0) or 0):
                        x1 = _key_to_x(int(lowest.get('pitch', 0) or 0))
                        x2 = _key_to_x(int(highest.get('pitch', 0) or 0))
                        du.add_line(
                            x1,
                            y_start,
                            x2,
                            y_start,
                            color=(0, 0, 0, 1),
                            width_mm=float(layout.get('note_stem_thickness_mm', 0.5) or 0.5) * scale,
                            id=0,
                            tags=['chord_connect'],
                        )

                # Draw stop sign if followed by rest
                if _has_followed_rest(item):
                    w_stop = w * 1.8
                    points = [
                        (x - w_stop / 2.0, y_end - w_stop),
                        (x, y_end),
                        (x + w_stop / 2.0, y_end - w_stop),
                    ]
                    du.add_polyline(
                        points,
                        stroke_color=(0, 0, 0, 1),
                        stroke_width_mm=float(layout.get('note_stopsign_thickness_mm', 0.4) or 0.4) * scale,
                        id=0,
                        tags=['stop_sign'],
                    )

            x_cursor = x_cursor + float(line['total_width']) + gap


    # Ensure a valid current page index
    try:
        if du.page_count() > 0:
            du.set_current_page(0)
    except Exception:
        traceback.print_exc()


def _engrave_worker(score: dict, request_id: int, out_queue) -> None:
    local_du = DrawUtil()
    try:
        do_engrave(score, local_du)
    except Exception:
        traceback.print_exc()
    try:
        out_queue.put((int(request_id), local_du))
    except Exception:
        traceback.print_exc()


class Engraver(QtCore.QObject):
    """Convenient engraver API ensuring single-run with latest-request semantics.

    - Call engrave(score) to request an engraving.
    - If one is running, stores the latest pending request and runs it next.
    - Skips intermediate requests; never runs two tasks at the same time.
    """

    engraved = QtCore.Signal()

    def __init__(self, draw_util: DrawUtil, parent=None):
        super().__init__(parent)
        self._du = draw_util
        self._mp_ctx = _MP_CONTEXT
        self._result_queue = self._mp_ctx.Queue()
        self._proc: mp.Process | None = None
        self._poll_timer = QtCore.QTimer(self)
        self._poll_timer.setInterval(50)
        self._poll_timer.timeout.connect(self._poll_results)
        self._running: bool = False
        self._pending_score: dict | None = None
        self._pending_request_id: int | None = None
        self._latest_request_id: int = 0
        self._min_interval_ms: int = 500
        self._last_start_ms: int = -500
        self._elapsed = QtCore.QElapsedTimer()
        self._elapsed.start()
        self._delay_timer = QtCore.QTimer(self)
        self._delay_timer.setSingleShot(True)
        self._delay_timer.timeout.connect(self._maybe_start_pending)

    def engrave(self, score: dict) -> None:
        self._latest_request_id += 1
        req_id = int(self._latest_request_id)
        # If currently running, just replace the pending request
        if self._running:
            self._pending_score = dict(score or {})
            self._pending_request_id = req_id
            return
        self._pending_score = dict(score or {})
        self._pending_request_id = req_id
        self._maybe_start_pending()

    def _maybe_start_pending(self) -> None:
        if self._running:
            return
        if self._pending_score is None:
            return
        if self._pending_request_id is None:
            return
        elapsed_ms = int(self._elapsed.elapsed())
        since_last = elapsed_ms - int(self._last_start_ms)
        if since_last >= self._min_interval_ms:
            next_score = self._pending_score
            next_req_id = int(self._pending_request_id)
            self._pending_score = None
            self._pending_request_id = None
            self._start_task(next_score, next_req_id)
            return
        delay_ms = max(1, int(self._min_interval_ms - since_last))
        if self._delay_timer.isActive():
            self._delay_timer.stop()
        self._delay_timer.start(delay_ms)

    def _start_task(self, score: dict, request_id: int) -> None:
        self._running = True
        self._last_start_ms = int(self._elapsed.elapsed())
        if self._proc is not None:
            try:
                if self._proc.is_alive():
                    self._proc.terminate()
            except Exception:
                pass
        self._proc = self._mp_ctx.Process(
            target=_engrave_worker,
            args=(score, request_id, self._result_queue),
            daemon=True,
        )
        self._proc.start()
        if not self._poll_timer.isActive():
            self._poll_timer.start()

    def _poll_results(self) -> None:
        got_result = False
        while True:
            try:
                req_id, result_du = self._result_queue.get_nowait()
            except queue.Empty:
                break
            got_result = True
            self._on_finished(req_id, result_du)

        if self._proc is not None and not self._proc.is_alive():
            try:
                self._proc.join(timeout=0)
            except Exception:
                pass
            self._proc = None
            if self._running and not got_result:
                self._running = False
                if self._pending_score is not None:
                    self._maybe_start_pending()
            if not self._running:
                try:
                    self._poll_timer.stop()
                except Exception:
                    pass

    def shutdown(self) -> None:
        try:
            if self._poll_timer.isActive():
                self._poll_timer.stop()
        except Exception:
            pass
        if self._proc is not None:
            try:
                if self._proc.is_alive():
                    self._proc.terminate()
            except Exception:
                pass
            try:
                self._proc.join(timeout=0.1)
            except Exception:
                pass
            self._proc = None

    @QtCore.Slot(int, object)
    def _on_finished(self, request_id: int, result_du: DrawUtil) -> None:
        # Called on worker completion; schedule next or emit signal
        self._running = False
        if self._pending_score is not None:
            # Grab and clear the latest pending, then run it
            self._maybe_start_pending()
            return
        # No pending: notify listeners (e.g., to request render)
        try:
            if int(request_id) == int(self._latest_request_id):
                try:
                    self._du._pages = list(result_du._pages)
                    self._du._current_index = int(result_du._current_index)
                except Exception:
                    pass
                self.engraved.emit()
        except Exception:
            traceback.print_exc()