from PySide6 import QtCore
from pathlib import Path
import bisect
import traceback
from ui.widgets.draw_util import DrawUtil
from utils.CONSTANT import BE_KEYS, QUARTER_NOTE_UNIT, PIANO_KEY_AMOUNT, SHORTEST_DURATION, hex_to_rgba, BLACK_KEYS
from utils.tiny_tool import key_class_filter
from utils.operator import Operator
from file_model.SCORE import SCORE

def do_engrave(score: SCORE, du: DrawUtil, pageno: int = 0) -> None:
    """Compute the full page drawing from the score dict into DrawUtil.

    This function runs off-thread. It should rebuild pages deterministically
    from the input score. Keep Cairo usage confined to DrawUtil rendering.
    """
    score: SCORE = score or {}
    layout = (score.get('layout', {}) or {})
    editor = (score.get('editor', {}) or {})
    events = (score.get('events', {}) or {})
    base_grid = list(score.get('base_grid', []) or [])
    line_breaks = list(events.get('line_break', []) or [])
    notes = list(events.get('note', []) or [])

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
    zpq = float(editor.get('zoom_mm_per_quarter', 25.0) or 25.0)
    stave_two_w = float(layout.get('stave_two_line_thickness_mm', 0.5) or 0.5) * scale
    stave_three_w = float(layout.get('stave_three_line_thickness_mm', 0.5) or 0.5) * scale
    clef_dash = list(layout.get('stave_clef_line_dash_pattern_mm', []) or [])
    if clef_dash:
        clef_dash = [float(v) * scale for v in clef_dash]
    op_time = Operator(SHORTEST_DURATION)

    def _log(msg: str) -> None:
        try:
            log_path = Path.home() / '.keyTAB' / 'engraver.log'
            log_path.parent.mkdir(parents=True, exist_ok=True)
            with log_path.open('a', encoding='utf-8') as f:
                f.write(msg + '\n')
        except Exception:
            traceback.print_exc()

    def _normalize_hex_color(value: str | None) -> str | None:
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
        rgba = hex_to_rgba(hex_color, alpha)
        r, g, b, a = rgba
        return (float(r) / 255.0, float(g) / 255.0, float(b) / 255.0, float(a))

    def _has_followed_rest(item: dict) -> bool:
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
        return {
            'time': 0.0,
            'margin_mm': [10.0, 10.0],
            'stave_range': 'auto',
            'page_break': False,
        }

    def _sanitize_range(rng) -> list[int]:
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
        pc = (int(key) - 1) % 12
        if pc in (0, 2, 3, 5, 7, 8, 10):
            return {0: 'a', 2: 'b', 3: 'c', 5: 'd', 7: 'e', 8: 'f', 10: 'g'}[pc]
        return {1: 'A', 4: 'C', 6: 'D', 9: 'F', 11: 'G'}[pc]

    line_keys = sorted(key_class_filter('ACDFG'))

    def _build_line_groups() -> list[dict]:
        groups: list[dict] = []
        used: set[int] = set()

        def _next_index(start: int, pc_target: str) -> int | None:
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
        if not line_groups:
            return 0
        for i, grp in enumerate(line_groups):
            if grp['range_low'] <= key <= grp['range_high']:
                return i
        return 0 if key <= line_groups[0]['range_low'] else len(line_groups) - 1

    def _note_range_for_window(t0: float, t1: float) -> tuple[int | None, int | None]:
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

    _log("-- do_engrave start --")
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
        line['range'] = [int(bound_left), int(bound_right)]
        min_pos = key_positions.get(bound_left, 0.0)
        max_pos = key_positions.get(bound_right, min_pos)
        stave_width = max(0.0, max_pos - min_pos)
        line['stave_width'] = float(stave_width)
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
        # Debug: outline the page bounds to ensure nothing covers the drawing
        try:
            du.add_rectangle(
                0.5,
                0.5,
                max(0.5, page_w - 0.5),
                max(0.5, page_h - 0.5),
                stroke_color=(0.6, 0.6, 0.6, 1),
                stroke_width_mm=0.5,
                fill_color=None,
                dash_pattern=[0.0, 1.0],
                id=0,
                tags=['engrave_test'],
            )
        except Exception:
            traceback.print_exc()
        # Debug: show printable area (page margins)
        try:
            du.add_rectangle(
                page_left,
                page_top,
                max(page_left + 0.5, page_w - page_right),
                max(page_top + 0.5, page_h - page_bottom),
                stroke_color=(0, .9, 0, 1),
                stroke_width_mm=0.35,
                fill_color=None,
                id=0,
                tags=['engrave_test'],
            )
        except Exception:
            traceback.print_exc()
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
                header_offset = float(layout.get('title_composer_area_height_mm', 0.0) or 0.0)
            y1 = page_top + header_offset
            y2 = float(page_h - page_bottom)
            if y2 <= y1:
                y2 = y1 + 1.0
            line['y_top'] = y1
            line['y_bottom'] = y2

            bound_left = int(line.get('bound_left', line['range'][0]))
            bound_right = int(line.get('bound_right', line['range'][1]))
            origin = float(key_positions.get(bound_left, 0.0))

            def _key_to_x(key: int) -> float:
                return line_x_start + (float(key_positions.get(key, 0.0)) - origin)

            def _time_to_y(ticks: float) -> float:
                total = max(1e-6, float(line['time_end'] - line['time_start']))
                rel = (float(ticks) - float(line['time_start'])) / total
                rel = max(0.0, min(1.0, rel))
                return y1 + (y2 - y1) * rel

            # Grid drawing based on base_grid (barlines and beat lines)
            grid_left = line_x_start
            grid_right = line_x_start + float(line['stave_width'])
            grid_color = (0, 0, 0, 1)
            bar_width_mm = 0.25 * scale
            dash_pattern = list(layout.get('stave_clef_line_dash_pattern_mm', []) or [])
            if dash_pattern:
                dash_pattern = [float(v) * scale for v in dash_pattern]
            time_cursor = 0.0
            for bg in base_grid:
                try:
                    numerator = int(bg.get('numerator', 4) or 4)
                    denominator = int(bg.get('denominator', 4) or 4)
                    measure_amount = int(bg.get('measure_amount', 1) or 1)
                    beat_grouping = list(bg.get('beat_grouping', []) or [])
                except Exception:
                    traceback.print_exc()
                    continue
                if measure_amount <= 0:
                    continue
                measure_len = float(numerator) * (4.0 / float(max(1, denominator))) * float(QUARTER_NOTE_UNIT)
                beat_len = measure_len / max(1, int(numerator))
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
                                    width_mm=max(0.1, bar_width_mm / 2.0),
                                    id=0,
                                    tags=['grid_line'],
                                    dash_pattern=dash_pattern or [2.0 * scale, 2.0 * scale],
                                )
                    time_cursor += measure_len
                if op_time.gt(time_cursor, float(line['time_end'])):
                    break

            visible_keys = list(line.get('visible_keys', []))
            if not visible_keys:
                visible_keys = [k for k in range(int(line['range'][0]), int(line['range'][1]) + 1) if k in line_keys]
            for key in visible_keys:
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

                # Draw notehead
                if bool(layout.get('note_head_visible', True)):
                    note_y = y_start
                    if p in BLACK_KEYS and str(layout.get('black_note_rule', 'below_stem')) == 'above_stem':
                        note_y = y_start - (w * 2.0)
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
                            stroke_width_mm=0.3,
                            fill_color=(1, 1, 1, 1),
                            id=int(item.get('id', 0) or 0),
                            tags=['notehead_white'],
                        )

                # Draw stem
                if bool(layout.get('note_stem_visible', True)):
                    stem_len = float(layout.get('note_stem_length_mm', 7.5) or 7.5)
                    stem_w = float(layout.get('note_stem_width_mm', 0.5) or 0.5)
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
                    note_y = y_start
                    if p in BLACK_KEYS and str(layout.get('black_note_rule', 'below_stem')) == 'above_stem':
                        note_y = y_start - (w * 2.0)
                    w2 = w * 2.0
                    dot_d = w2 * 0.35
                    cy = note_y + (w2 / 2.0)
                    du.add_oval(
                        x - (dot_d / 3.0),
                        cy - (dot_d / 3.0),
                        x + (dot_d / 3.0),
                        cy + (dot_d / 3.0),
                        stroke_color=None,
                        fill_color=(0, 0, 0, 1),
                        id=0,
                        tags=['left_dot'],
                    )

                # Draw note continuation dots
                dot_times: list[float] = []
                for m in line_notes:
                    if int(m.get('id', 0) or 0) == int(item.get('id', 0) or 0):
                        continue
                    if str(m.get('hand', '<') or '<') != hand_key:
                        continue
                    s = float(m.get('time', 0.0) or 0.0)
                    e = float(m.get('end', 0.0) or 0.0)
                    if op_time.gt(s, n_t) and op_time.lt(s, n_end):
                        dot_times.append(s)
                    if op_time.gt(e, n_t) and op_time.lt(e, n_end):
                        dot_times.append(e)
                if dot_times:
                    dot_d = w * 0.8
                    for t in sorted(set(dot_times)):
                        y = _time_to_y(float(t))
                        du.add_oval(
                            x - dot_d / 2.0,
                            y - dot_d / 2.0 + w,
                            x + dot_d / 2.0,
                            y + dot_d / 2.0 + w,
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
                            width_mm=float(layout.get('note_stem_width_mm', 0.5) or 0.5),
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
                        stroke_width_mm=0.4,
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


class _EngraveTask(QtCore.QRunnable):
    def __init__(self, score: dict, du: DrawUtil, finished_cb):
        super().__init__()
        self.setAutoDelete(True)
        self._score = score
        self._du = du
        self._finished_cb = finished_cb

    def run(self) -> None:
        try:
            do_engrave(self._score, self._du)
        finally:
            # Notify completion back to Engraver (GUI thread via signal)
            try:
                self._finished_cb()
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
        self._pool = QtCore.QThreadPool.globalInstance()
        self._running: bool = False
        self._pending_score: dict | None = None

    def engrave(self, score: dict) -> None:
        # If currently running, just replace the pending request
        if self._running:
            self._pending_score = dict(score or {})
            return
        # Start immediately
        self._start_task(dict(score or {}))

    def _start_task(self, score: dict) -> None:
        self._running = True
        task = _EngraveTask(score, self._du, self._on_finished)
        self._pool.start(task)

    @QtCore.Slot()
    def _on_finished(self) -> None:
        # Called on worker completion; schedule next or emit signal
        self._running = False
        if self._pending_score is not None:
            # Grab and clear the latest pending, then run it
            next_score = self._pending_score
            self._pending_score = None
            self._start_task(next_score)
            return
        # No pending: notify listeners (e.g., to request render)
        try:
            self.engraved.emit()
        except Exception:
            traceback.print_exc()