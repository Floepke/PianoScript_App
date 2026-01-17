from __future__ import annotations
from typing import Any
from ui.widgets.draw_util import DrawUtil
from editor.editor import Editor
from .base import DrawerBase
from utils.CONSTANT import PIANO_KEY_AMOUNT, BLACK


class StaveDrawer(DrawerBase):
    def draw(self, du: DrawUtil, score: Any, editor: Editor) -> None:
        self.setup_context(du, score, editor)
        # Piano-roll vertical stave: draw vertical lines per semitone across full height
        # Copying the pattern from pianoTab's stave_drawer with adaptation to Cairo/DrawUtil
        try:
            w_mm, h_mm = du.current_page_size_mm()
        except Exception:
            w_mm, h_mm = (210.0, 297.0)
        # Editor-derived layout (no page margins): use Editor metrics
        margin = float(getattr(editor, 'editor_margin_mm', w_mm / 10.0))
        stave_width = float(getattr(editor, 'stave_width_mm', max(1.0, w_mm - 2.0 * margin)))
        semitone_dx = float(getattr(editor, 'semitone_width_mm', stave_width / float(max(1, PIANO_KEY_AMOUNT - 1))))
        stave_left = margin
        stave_right = stave_left + stave_width
        y1 = 0.0
        y2 = h_mm

        def pitch_to_x(key_number: int) -> float:
            return stave_left + (key_number - 1) * semitone_dx

        # Visual style
        dark = (0.15, 0.15, 0.15, 1.0)
        clef_dash = [0.0, 2.0]
        two_dash = [2.0, 1.0]

        for key in BLACK:
            x_pos = pitch_to_x(key)
            is_clef_line = key in (41, 43)  # C# and D# around middle C
            # Draw only black keys; clef positions dashed
            if is_clef_line:
                # Clef lines — thicker and dashed
                width_mm = max(0.05, semitone_dx / 6.0)
                dash = clef_dash
                tag = "stave_clef_line"
            else:
                # Regular black key line — solid
                width_mm = max(0.05, semitone_dx / 16.0)
                dash = None
                tag = "stave_black_key"
            # Avoid drawing outside bounds
            if x_pos < stave_left - 0.1 or x_pos > stave_right + 0.1:
                continue
            du.add_line(x_pos, y1, x_pos, y2, color=dark, width_mm=width_mm,
                        dash_pattern=dash, id=0, tags=[tag])
