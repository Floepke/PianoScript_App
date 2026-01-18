from __future__ import annotations
from file_model.SCORE import SCORE
from ui.widgets.draw_util import DrawUtil
from utils.CONSTANT import PIANO_KEY_AMOUNT, BLACK, QUARTER_NOTE_UNIT
from typing import TYPE_CHECKING, cast

if TYPE_CHECKING:
    from editor.editor import Editor


class StaveDrawerMixin:
    def draw_stave(self, du: DrawUtil) -> None:
        self = cast("Editor", self)
        score: SCORE = self.current_score()

        # Piano-roll vertical stave: draw vertical lines per semitone across full height
        w_mm, h_mm = du.current_page_size_mm()
        margin = float(self.margin)
        stave_width = float(self.stave_width)
        semitone_dx = float(self.semitone_width)
        stave_left = margin
        stave_right = w_mm - margin
        total_score_time = self.get_score_time()
        stave_length_mm = (total_score_time / QUARTER_NOTE_UNIT) * score.editor.zoom_mm_per_quarter
        y1 = margin
        y2 = margin + stave_length_mm

        def pitch_to_x(key_number: int) -> float:
            return stave_left + (key_number - 1) * semitone_dx
        
        def key_class_filter(key_class: str) -> list[int]:
            ''' 
                Return list of key numbers matching the given class 
                example 'abcdefg' to get all white key numbers (1-88)
                example 'CDFGA' to get all black key numbers (1-88)
            '''
            wanted = set(key_class)
            out: list[int] = []
            for key_num in range(1, PIANO_KEY_AMOUNT + 1):
                pc = (key_num - 1) % 12  # A0-based pitch class
                if pc in (0, 2, 3, 5, 7, 8, 10):  # naturals
                    pc_char = {0: 'a', 2: 'b', 3: 'c', 5: 'd', 7: 'e', 8: 'f', 10: 'g'}[pc]
                else:  # sharps
                    pc_char = {1: 'A', 4: 'C', 6: 'D', 9: 'F', 11: 'G'}[pc]
                if pc_char in wanted:
                    out.append(key_num)
            return out

        for key in key_class_filter('CDFGA'):  # black keys
            x_pos = pitch_to_x(key)
            is_clef_line = key in (41, 43)  # C# and D# around middle C
            is_three_line = key in key_class_filter('FGA')
            if is_clef_line:
                width_mm = max(0.05, semitone_dx / 6.0)
                dash = [2,2]
                tag = "stave_clef_line"
            elif is_three_line:
                width_mm = max(0.05, semitone_dx / 3.0)
                dash = None
                tag = "stave_three_line"
            else:
                # two line
                width_mm = max(0.05, semitone_dx / 10.0)
                dash = None
                tag = "stave_two_line"
            du.add_line(x_pos, y1, x_pos, y2, color=self.notation_color, width_mm=width_mm,
                        dash_pattern=dash, id=0, tags=[tag])
