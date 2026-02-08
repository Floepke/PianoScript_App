from PySide6 import QtCore
from pathlib import Path
from ui.widgets.draw_util import DrawUtil
from utils.CONSTANT import BE_KEYS, QUARTER_NOTE_UNIT, PIANO_KEY_AMOUNT
from utils.tiny_tool import key_class_filter
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

    def _log(msg: str) -> None:
        try:
            log_path = Path.home() / '.keyTAB' / 'engraver.log'
            log_path.parent.mkdir(parents=True, exist_ok=True)
            with log_path.open('a', encoding='utf-8') as f:
                f.write(msg + '\n')
        except Exception:
            pass

    # Reset pages
    try:
        du._pages = []
        du._current_index = -1
    except Exception:
        pass

    def _total_score_ticks() -> float:
        total = 0.0
        for bg in base_grid:
            try:
                numer = int(bg.get('numerator', 4) or 4)
                denom = int(bg.get('denominator', 4) or 4)
                measures = int(bg.get('measure_amount', 1) or 1)
            except Exception:
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
            return [1, PIANO_KEY_AMOUNT]
        lo = max(1, min(PIANO_KEY_AMOUNT, lo))
        hi = max(1, min(PIANO_KEY_AMOUNT, hi))
        if hi < lo:
            lo, hi = hi, lo
        return [lo, hi]

    def _auto_range_for_window(t0: float, t1: float) -> list[int]:
        lo = None
        hi = None
        for n in notes:
            try:
                n_t = float(n.get('time', 0.0) or 0.0)
                n_d = float(n.get('duration', 0.0) or 0.0)
                n_end = n_t + n_d
                p = int(n.get('pitch', 0) or 0)
            except Exception:
                continue
            if n_t < t1 and n_end > t0:
                if p < 1 or p > PIANO_KEY_AMOUNT:
                    continue
                lo = p if lo is None else min(lo, p)
                hi = p if hi is None else max(hi, p)
        if lo is None or hi is None:
            return [1, PIANO_KEY_AMOUNT]
        return _sanitize_range([lo, hi])

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
                continue
            if n_t < t1 and n_end > t0 and 1 <= p <= PIANO_KEY_AMOUNT:
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

    def _get_stave_width(start_key: int, end_key: int, semitone_mm: float) -> float:
        positions = _build_key_positions(start_key, end_key, semitone_mm)
        min_pos = positions.get(start_key, 0.0)
        max_pos = positions.get(end_key, 0.0)
        return (max_pos - min_pos) + semitone_mm

    _log("-- do_engrave start --")
    try:
        pitches = [int(n.get('pitch', 0) or 0) for n in notes if isinstance(n, dict)]
        if pitches:
            _log(f"note_pitch_min={min(pitches)} max={max(pitches)}")
        else:
            _log("note_pitch_min=NA max=NA")
    except Exception:
        pass
    _log(f"PIANO_KEY_AMOUNT={PIANO_KEY_AMOUNT}")
    total_ticks = _total_score_ticks()
    if total_ticks <= 0.0:
        total_ticks = float(QUARTER_NOTE_UNIT) * 4.0
    if not line_breaks:
        line_breaks = [_line_break_defaults()]

    try:
        line_breaks = sorted(line_breaks, key=lambda lb: float(lb.get('time', 0.0) or 0.0))
    except Exception:
        pass

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
                pass
        line = {
            'time_start': lb_time,
            'time_end': next_time,
            'margin_left': float(margin_mm[0]) * scale,
            'margin_right': float(margin_mm[1]) * scale,
            'stave_range': stave_range,
            'page_break': bool(lb.get('page_break', False)),
        }
        lines.append(line)

    _log(f"lines={len(lines)} total_ticks={total_ticks:.2f} notes={len(notes)} base_grid={len(base_grid)}")

    # Calculate ranges and widths
    semitone_mm = 2.5 * scale
    for line in lines:
        if line['stave_range'] == 'auto':
            line_range = _auto_range_for_window(line['time_start'], line['time_end'])
        else:
            line_range = _sanitize_range(line['stave_range'])
        line['range'] = line_range
        if line['stave_range'] == 'auto' and line_range == [1, 1]:
            count, lo, hi = _notes_in_window_stats(line['time_start'], line['time_end'])
            _log(f"auto_range_empty window={line['time_start']:.2f}..{line['time_end']:.2f} count={count} lo={lo} hi={hi}")
        key_max_pos = _build_key_positions(line_range[0], line_range[1], semitone_mm)
        min_pos = key_max_pos.get(line_range[0], 0.0)
        stave_width = _get_stave_width(line_range[0], line_range[1], semitone_mm)
        line['stave_width'] = float(stave_width)
        line['total_width'] = float(line['margin_left'] + stave_width + line['margin_right'])
        line['key_max_pos'] = key_max_pos
        line['key_min_pos'] = min_pos

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
                stroke_width_mm=0.2,
                fill_color=None,
                id=0,
                tags=['engrave_test'],
            )
        except Exception:
            pass
        # Debug: show printable area (page margins)
        try:
            du.add_rectangle(
                page_left,
                page_top,
                max(page_left + 0.5, page_w - page_right),
                max(page_top + 0.5, page_h - page_bottom),
                stroke_color=(1, 0, 0, 1),
                stroke_width_mm=0.35,
                fill_color=None,
                id=0,
                tags=['engrave_test'],
            )
        except Exception:
            pass
        if not page:
            continue
        used_width = sum(float(l['total_width']) for l in page)
        leftover = max(0.0, available_width - used_width)
        gap = leftover / float(len(page) + 1)
        x_cursor = page_left + gap
        for line in page:
            _log(
                "line time=%.2f..%.2f range=%s total_w=%.2f"
                % (
                    float(line.get('time_start', 0.0)),
                    float(line.get('time_end', 0.0)),
                    str(line.get('range', None)),
                    float(line.get('total_width', 0.0)),
                )
            )
            line_x_start = x_cursor + float(line['margin_left'])
            line_x_end = line_x_start + float(line['stave_width'])
            time_len = float(line['time_end'] - line['time_start'])
            if time_len <= 0.0:
                time_len = float(QUARTER_NOTE_UNIT) * 4.0
            line_height = (time_len / float(QUARTER_NOTE_UNIT)) * zpq * scale
            header_offset = 0.0
            if page_index == 0:
                header_offset = float(layout.get('title_composer_area_height_mm', 0.0) or 0.0) * scale
            y1 = page_top + header_offset
            y2 = min(page_h - page_bottom, y1 + line_height)

            # Debug: per-line bounding box
            try:
                du.add_rectangle(
                    line_x_start,
                    y1,
                    line_x_end,
                    y2,
                    stroke_color=(1, 1, 1, 1),
                    stroke_width_mm=0.25,
                    fill_color=None,
                    id=0,
                    tags=['engrave_test'],
                )
            except Exception:
                pass

            key_max_pos = line['key_max_pos']
            min_pos = float(line['key_min_pos'])
            for key in range(int(line['range'][0]), int(line['range'][1]) + 1):
                if key not in key_class_filter('ACDFG'):
                    continue
                x_pos = line_x_start + (float(key_max_pos.get(key, 0.0)) - min_pos)
                is_clef_line = key in (41, 43)
                is_three_line = key in key_class_filter('FGA')
                if is_clef_line:
                    width_mm = max(stave_two_w, semitone_mm / 6.0)
                    dash = [2, 2]
                elif is_three_line:
                    width_mm = max(stave_three_w, semitone_mm / 3.0)
                    dash = None
                else:
                    width_mm = max(stave_two_w, semitone_mm / 10.0)
                    dash = None
                _log(f"Drawing line key={key} x={x_pos:.2f}mm w={width_mm:.2f}mm")
                du.add_line(x_pos, y1, x_pos, y2, color=(0, 0, 0, 1), width_mm=width_mm, dash_pattern=dash, id=0, tags=['stave'])

            x_cursor = x_cursor + float(line['total_width']) + gap

    # Ensure a valid current page index
    try:
        if du.page_count() > 0:
            du.set_current_page(0)
    except Exception:
        pass


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
                pass


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
            pass