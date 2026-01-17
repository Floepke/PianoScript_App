from __future__ import annotations
from ui.widgets.draw_util import DrawUtil
from utils.CONSTANT import PIANO_KEY_AMOUNT, BLACK


class StaveDrawerMixin:
    def draw_stave(self, du: DrawUtil) -> None:
        # Piano-roll vertical stave: draw vertical lines per semitone across full height
        w_mm, h_mm = du.current_page_size_mm()
        # Editor-derived layout (no page margins): use Editor metrics
        margin = float(self.margin)
        stave_width = float(self.stave_width)
        semitone_dx = float(self.semitone_width)
        stave_left = margin
        stave_right = stave_left + stave_width
        y1 = 0.0
        y2 = h_mm

        def pitch_to_x(key_number: int) -> float:
            return stave_left + (key_number - 1) * semitone_dx

        # Visual style
        dark = (0, 0, 0.1, 1.0)
        clef_dash = [0.0, 2.0]

        for key in BLACK:
            x_pos = pitch_to_x(key)
            is_clef_line = key in (41, 43)  # C# and D# around middle C
            if is_clef_line:
                width_mm = max(0.05, semitone_dx / 6.0)
                dash = clef_dash
                tag = "stave_clef_line"
            else:
                width_mm = max(0.05, semitone_dx / 16.0)
                dash = None
                tag = "stave_black_key"
            if x_pos < stave_left - 0.1 or x_pos > stave_right + 0.1:
                continue
            du.add_line(x_pos, y1, x_pos, y2, color=dark, width_mm=width_mm,
                        dash_pattern=dash, id=0, tags=[tag])
