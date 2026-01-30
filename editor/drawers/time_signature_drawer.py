from __future__ import annotations
from typing import TYPE_CHECKING, cast
from ui.widgets.draw_util import DrawUtil

if TYPE_CHECKING:
    from editor.editor import Editor


class TimeSignatureDrawerMixin:
    def draw_time_signature(self, du: DrawUtil) -> None:
        self = cast("Editor", self)
        score = self.current_score()
        if score is None:
            return
        # Read global indicator type from Layout
        indicator_type = getattr(score.layout, 'indicator_type', 'classical')

        # Shared layout metrics
        margin = float(self.margin or 0.0)
        stave_left_position = margin + float(self.semitone_dist or 0.0)
        # Render at segment starts along time axis
        time_cursor = margin

        # Helper: draw classical numerator/denominator at segment boundary
        def draw_classical(numerator: int, denominator: int, enabled: bool, y_mm: float) -> None:
            color = self.notation_color if enabled else (0.6, 0.6, 0.6, 1.0)
            x = stave_left_position - ((margin / 4.0) * 2.0)
            # Numerator
            du.add_text(
                x,
                y_mm - 3.0,
                f"{int(numerator)}",
                size_pt=32.0,
                color=color,
                id=0,
                tags=["time_signature"],
                anchor='s',
                family="Courier New",
            )
            # Divider line
            du.add_line(
                x - 5.0,
                y_mm,
                x + 5.0,
                y_mm,
                color=color,
                width_mm=1.5,
                id=0,
                tags=["time_signature_line"],
                dash_pattern=None,
            )
            # Denominator
            du.add_text(
                x,
                y_mm + 3.0,
                f"{int(denominator)}",
                size_pt=32.0,
                color=color,
                id=0,
                tags=["time_signature"],
                anchor='n',
                family="Courier New",
            )

        # Iterate BaseGrid segments and draw based on indicator_type
        for bg in list(getattr(score, 'base_grid', []) or []):
            numerator = int(getattr(bg, 'numerator', 4) or 4)
            denominator = int(getattr(bg, 'denominator', 4) or 4)
            measure_amount = int(getattr(bg, 'measure_amount', 1) or 1)
            enabled = bool(getattr(bg, 'indicator_enabled', True))

            if indicator_type == 'classical':
                draw_classical(numerator, denominator, enabled, time_cursor)
            elif indicator_type == 'klavarskribo':
                # TODO: Implement Klavarskribo style indicator drawing.
                pass
            elif indicator_type == 'both':
                # Draw classical now; Klavarskribo to be added later below or beside.
                draw_classical(numerator, denominator, enabled, time_cursor)
                # Placeholder for Klavarskribo alongside classical
                pass

            # Advance time cursor by the segment length (mm) to next segment start
            quarters_per_measure = float(numerator) * (4.0 / max(1.0, float(denominator)))
            measure_len_mm = quarters_per_measure * float(score.editor.zoom_mm_per_quarter)
            time_cursor += measure_len_mm * float(measure_amount)
