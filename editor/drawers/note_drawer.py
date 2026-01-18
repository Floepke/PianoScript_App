from __future__ import annotations
from typing import TYPE_CHECKING, cast
from file_model.SCORE import SCORE
from utils.CONSTANT import QUARTER_NOTE_UNIT
from ui.widgets.draw_util import DrawUtil

if TYPE_CHECKING:
    from editor.editor import Editor


class NoteDrawerMixin:
    def draw_note(self, du: DrawUtil) -> None:
        self = cast("Editor", self)
        score: SCORE = self.current_score()
        if score is None:
            return

        # Layout metrics
        margin = float(self.margin)
        semitone_w = float(self.semitone_width)
        zoom_mm_per_quarter = float(score.editor.zoom_mm_per_quarter)

        # Simple performance-oriented rendering: draw vertical bars per note
        # Map time (ticks) → mm and pitch → x center using provided formula.
        def time_to_mm(ticks: float) -> float:
            return margin + (float(ticks) / float(QUARTER_NOTE_UNIT)) * zoom_mm_per_quarter

        # Rectangle width as a fraction of semitone spacing
        rect_w = max(0.2, semitone_w * 0.6)

        # Colors: subtle semi-transparent fill to keep focus on grid/stave
        fill_rgba = (0.10, 0.10, 0.12, 0.35)

        for n in score.events.note:
            try:
                pitch = int(getattr(n, 'pitch', 40) or 40)
                time_ticks = float(getattr(n, 'time', 0.0) or 0.0)
                duration_ticks = float(getattr(n, 'duration', 0.0) or 0.0)
            except Exception:
                continue

            # X center for pitch (A0 = 1)
            x_center = margin - semitone_w + semitone_w * float(pitch)

            # Y position and height
            y_top = time_to_mm(time_ticks)
            h_mm = max(0.5, (duration_ticks / float(QUARTER_NOTE_UNIT)) * zoom_mm_per_quarter)

            # Draw note rectangle tagged for layering beneath notation
            du.add_rectangle(
                x_center - self.semitone_width / 2,
                y_top,
                x_center + self.semitone_width / 2,
                y_top + h_mm,
                stroke_color=None,
                fill_color=fill_rgba,
                id=0,
                tags=["midi_note"],
            )
