from __future__ import annotations
from typing import TYPE_CHECKING, cast
from file_model.SCORE import SCORE
from utils.CONSTANT import BLACK_KEYS, QUARTER_NOTE_UNIT
from ui.widgets.draw_util import DrawUtil

if TYPE_CHECKING:
    from editor.editor import Editor


class NoteDrawerMixin:
    def draw_note(self, du: DrawUtil) -> None:
        self = cast("Editor", self)
        score: SCORE = self.current_score()

        # Layout metrics
        margin = float(self.margin)
        zpq = float(score.editor.zoom_mm_per_quarter)

        # Simple performance-oriented rendering: draw vertical bars per note
        # Map time (ticks) → mm and pitch → x center using provided formula.
        def time_to_mm(ticks: float) -> float:
            return margin + (float(ticks) / float(QUARTER_NOTE_UNIT)) * zpq

        for n in score.events.note:
            # optimalization: skip notes outside visible area
            y1 = time_to_mm(n.time)
            y2 = time_to_mm(n.time + n.duration)
            _, page_h_mm = du.current_page_size_mm()
            if y1 > page_h_mm + margin or y2 < margin:
                continue

            x = self.pitch_to_x(n.pitch)

            # midinote color
            if n.pitch in BLACK_KEYS:
                midinote_color = (0.6, 0.6, 0.6, 1)
            else:
                midinote_color = (0.8, 0.8, 0.8, 1)
            
            # Draw note rectangle tagged for layering beneath notation
            du.add_rectangle(
                x - self.semitone_dist / 2,
                y1,
                x + self.semitone_dist / 2,
                y2,
                stroke_color=None,
                fill_color=midinote_color,
                id=0,
                tags=["midi_note"],
            )

            # Draw note head
            if n.pitch in BLACK_KEYS:
                du.add_oval(
                    x - self.semitone_dist,
                    y1,
                    x + self.semitone_dist,
                    y1 + self.semitone_dist * 2,
                    stroke_color=None,
                    fill_color=(0,0,0,1),
                    id=0,
                    tags=["notehead_black"],
                )
            else:
                du.add_oval(
                    x - self.semitone_dist,
                    y1,
                    x + self.semitone_dist,
                    y1 + self.semitone_dist * 2,
                    stroke_width_mm=.25,
                    fill_color=(1,1,1,1),
                    id=0,
                    tags=["notehead_white"],
                )
