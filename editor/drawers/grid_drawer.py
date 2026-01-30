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
    '''
        Draws:
            - barlines
            - measure numbers
            - gridlines
            - time signature indicators
            - project title and composer at top-left
    '''
    
    def draw_grid(self, du: DrawUtil) -> None:
        self = cast("Editor", self)
        score: SCORE = self.current_score()

        # draw title and composer at top-left
        du.add_text(
            1,
            1,
            f"'{score.header.title}' by composer: {score.header.composer}",
            size_pt=12.0,
            color=self.notation_color,
            id=0,
            tags=["title"],
            anchor='nw',
            family="Courier New",
        )

        # Page metrics (mm)
        width_mm, height_mm = du.current_page_size_mm()
        margin = float(self.margin)
        stave_left_position = margin + self.semitone_dist
        stave_right_position = max(0.0, width_mm - margin) - self.semitone_dist * 2

        # Editor zoom controls vertical mm per quarter note
        zpq = score.editor.zoom_mm_per_quarter

        # --------------- drawing the grid lines, barlines, measure numbers and time signature indicators ---------------
        base_grid = score.base_grid
        measure_numbering_cursor = 1
        time_cursor = margin
        for bg in base_grid:
            numerator = bg.numerator
            denominator = bg.denominator
            measure_amount = bg.measure_amount

            # numerator/denominator indicator color: grey if disabled
            indicator_color = self.notation_color if getattr(bg, 'indicator_enabled', True) else (0.6, 0.6, 0.6, 1.0)

            # numerator text
            tsig_indicator_x = stave_left_position - ((margin / 4) * 2)
            du.add_text(
                tsig_indicator_x,
                time_cursor - 3,
                f"{numerator}",
                size_pt=32.0,
                color=indicator_color,
                id=0,
                tags=["time_signature"],
                anchor='s',
                family="Courier New",
            )

            # indicator line between numerator and denominator
            du.add_line(
                tsig_indicator_x - 5,
                time_cursor,
                tsig_indicator_x + 5,
                time_cursor,
                color=indicator_color,
                width_mm=1.5,
                id=0,
                tags=["time_signature_line"],
                dash_pattern=None,
            )

            # denominator text
            du.add_text(
                tsig_indicator_x,
                time_cursor + 3,
                f"{denominator}",
                size_pt=32.0,
                color=indicator_color,
                id=0,
                tags=["time_signature"],
                anchor='n',
                family="Courier New",
            )

            # General formula: quarters per measure = numerator * (4/denominator)
            quarters_per_measure = float(numerator) * (4.0 / max(1.0, float(denominator)))
            measure_len_mm = quarters_per_measure * zpq

            # Draw horizontal barlines across the stave width for each measure boundary
            color = self.notation_color
            bar_width_mm = 0.25

            for i in range(measure_amount):
                # measure numbers:
                measure_number_str = str(measure_numbering_cursor)
                du.add_text(
                    1.0,
                    time_cursor + 1.0,
                    measure_number_str,
                    size_pt=16.0,
                    color=color,
                    id=0,
                    tags=["measure_number"],
                    anchor='nw',
                    family="Courier New"
                )

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