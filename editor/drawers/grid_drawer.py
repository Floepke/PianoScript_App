'''
Grid and barline drawing mixin for the Editor class.

Handles drawing barlines, measure numbers, and gridlines.
'''

from __future__ import annotations
from typing import TYPE_CHECKING, cast
from file_model.SCORE import SCORE
from ui.widgets.draw_util import DrawUtil

if TYPE_CHECKING:
    from editor.editor import Editor


class GridDrawerMixin:
    
    def draw_grid(self, du: DrawUtil) -> None:
        self = cast("Editor", self)
        score: SCORE = self.current_score()

        # Page metrics (mm)
        width_mm, height_mm = du.current_page_size_mm()
        margin = float(self.margin)
        stave_left_position = margin + self.semitone_width
        stave_right_position = max(0.0, width_mm - margin) - self.semitone_width * 2

        # Editor zoom controls vertical mm per quarter note
        zoom_mm_per_quarter = score.editor.zoom_mm_per_quarter

        # drawing the grid lines, barlines and measure numbers
        base_grid = score.base_grid
        measure_numbering_cursor = 1
        time_cursor = margin
        for bg in base_grid:
            numerator = int(getattr(bg, 'numerator', 4) or 4)
            denominator = int(getattr(bg, 'denominator', 4) or 4)
            measure_amount = int(getattr(bg, 'measure_amount', 1) or 1)

            # General formula: quarters per measure = numerator * (4/denominator)
            quarters_per_measure = float(numerator) * (4.0 / max(1.0, float(denominator)))
            measure_len_mm = quarters_per_measure * zoom_mm_per_quarter

            # Draw horizontal barlines across the stave width for each measure boundary
            color = self.notation_color
            bar_width_mm = 0.5

            for i in range(measure_amount):
                # measure numbers:
                measure_number_str = str(measure_numbering_cursor)
                du.add_text(1.0, time_cursor, measure_number_str, size_pt=16.0, color=color, id=0, tags=["measure_number"], anchor='w')

                # Beat length inside this measure
                beat_length = measure_len_mm / max(1, numerator)

                for grid in bg.grid_positions:
                    # grid == 1 marks the barline (measure start)
                    is_barline = (grid == 1)

                    # Correct position: 1 → start of measure
                    line_y = time_cursor + (grid - 1) * beat_length

                    # Prepare style once, then call add_line
                    style = {
                        "color": color,
                        "width_mm": bar_width_mm if is_barline else 0.2,
                        "id": 0,
                        "tags": ["barline"] if is_barline else ["grid_line"],
                        "dash_pattern": None if is_barline else [2.0, 2.0],
                    }

                    # draw the line
                    du.add_line(
                        stave_left_position,
                        line_y,
                        stave_right_position,
                        line_y,
                        **style
                    )

                measure_numbering_cursor += 1
                time_cursor += measure_len_mm

        # draw the end barline with same style policy
        du.add_line(
            stave_left_position,
            time_cursor,
            stave_right_position,
            time_cursor,
            color=color,
            width_mm=bar_width_mm * 3,
            id=0,
            tags=["barline"],
            dash_pattern=None
        )