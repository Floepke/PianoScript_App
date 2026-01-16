from PySide6 import QtCore
from ui.widgets.draw_util import DrawUtil

def do_engrave(score: dict, du: DrawUtil, pageno: int = 0) -> None:
    """Compute the full page drawing from the score dict into DrawUtil.

    This function runs off-thread. It should rebuild pages deterministically
    from the input score. Keep Cairo usage confined to DrawUtil rendering.
    """
    # Simple demo engraving:
    # - Create a single A4 page
    # - Draw header text
    # - Draw a stave and one note rectangle based on the first event
    try:
        # Reset pages to avoid duplicating content on repeated runs
        # DrawUtil does not have a clear method; rebuild anew.
        # Create a fresh page and replace current content.
        du.new_page(210, 297) if du.page_count() == 0 else None
        # Clear current page items by recreating the page
        w_mm, h_mm = du.current_page_size_mm()
        # Recreate page: naive approach (add a new last page and set it current)
        du.new_page(w_mm or 210, h_mm or 297)
        du.set_current_page(du.page_count() - 1)

        # Header
        header = score.get('header', {})
        title = header.get('title', 'Untitled')
        composer = header.get('composer', '')
        du.add_text(20, 20, title, size_pt=16, bold=True, id=101, tags=['title'])
        if composer:
            du.add_text(20, 27, composer, size_pt=12, italic=True, id=102, tags=['composer'])

        # Stave: 5 lines
        top_y = 60.0
        spacing = 2.0
        for i in range(5):
            y = top_y + i * spacing
            du.add_line(20.0, y, 190.0, y, color=(0, 0, 0, 1), width_mm=0.2, id=0)

        # First note: draw as a rectangle at a y derived from pitch
        events = score.get('events', {})
        note_events = events.get('note', [])
        if note_events:
            n0 = note_events[0]
            pitch = int(n0.get('pitch', 60))
            time = float(n0.get('time', 0.0))
            duration = float(n0.get('duration', 100.0))
            # Map time to x in mm: 100 units -> 20 mm
            x_mm = 20.0 + (time / 100.0) * 20.0
            w_mm = max(2.0, (duration / 100.0) * 10.0)
            # Map pitch to stave position: coarse mapping
            y_mm = top_y + (60 - pitch) * 0.5
            du.add_rectangle(x_mm, y_mm - 1.0, w_mm, 2.0, fill_color=(0.1, 0.7, 0.3, 0.8), stroke_color=(0, 0, 0, 1), stroke_width_mm=0.2, id=201, tags=['note'])
    except Exception as e:
        # Let caller decide how to handle errors; for now we print.
        print(f"do_engrave error: {e}")


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