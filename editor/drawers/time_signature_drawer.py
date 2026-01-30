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

        # Helper: draw Klavarskribo-style three-column indicator at segment boundary
        def draw_klavarskribo(numerator: int, denominator: int, enabled: bool, y_mm: float, grid_positions: list[int]) -> None:
            color = self.notation_color if enabled else (0.6, 0.6, 0.6, 1.0)
            zpq = float(score.editor.zoom_mm_per_quarter)
            quarters_per_measure = float(numerator) * (4.0 / max(1.0, float(denominator)))
            measure_len_mm = quarters_per_measure * zpq
            beat_len_mm = measure_len_mm / max(1, int(numerator))

            # Column positions: left, middle, right (closest to stave)
            base_x = stave_left_position - ((margin / 4.0) * 2.0)
            col_gap = 6.0
            x_right = base_x + col_gap  # right column (guides)
            x_mid = base_x - col_gap * 0.0  # middle column (beat numbers)
            x_left = base_x - col_gap       # left column (group numbers)

            # Normalize grid positions (1-based indices within measure)
            gp = sorted({int(p) for p in (grid_positions or []) if 1 <= int(p) <= int(numerator)})
            if 1 not in gp:
                gp.insert(0, 1)

            # Right column: draw short thick horizontal guide lines at each beat, plus next measure barline
            guide_half_len = 3.0
            guide_width_mm = 1.5
            for k in range(1, int(numerator) + 1):
                y = y_mm + (k - 1) * beat_len_mm
                du.add_line(x_right - guide_half_len, y, x_right + guide_half_len, y,
                            color=color, width_mm=guide_width_mm, id=0, tags=["ts_klavars_guide"], dash_pattern=None)
            # Final identical guide at start of next measure
            du.add_line(x_right - guide_half_len, y_mm + measure_len_mm, x_right + guide_half_len, y_mm + measure_len_mm,
                        color=color, width_mm=guide_width_mm, id=0, tags=["ts_klavars_guide"], dash_pattern=None)

            # Middle column: label beats 1..numer; reset to 1 at enabled beats (group starts)
            all_beats_enabled = (gp == list(range(1, int(numerator) + 1)))
            if all_beats_enabled:
                # Normal numbering from 1..numer, plus final 1 at next measure barline
                for k in range(1, int(numerator) + 1):
                    y = y_mm + (k - 1) * beat_len_mm
                    du.add_text(x_mid, y, str(k), size_pt=18.0, color=color, id=0, tags=["ts_klavars_mid"], anchor='w', family="Courier New")
                du.add_text(x_mid, y_mm + measure_len_mm, "1", size_pt=18.0, color=color, id=0, tags=["ts_klavars_mid"], anchor='w', family="Courier New")
                # Left column disabled in this case
            else:
                # Build groups between consecutive enabled beats; last group ends at numerator
                group_starts = gp
                groups = []  # list of (start_k, end_k)
                for i, s in enumerate(group_starts):
                    e = (group_starts[i + 1] - 1) if (i + 1) < len(group_starts) else int(numerator)
                    groups.append((int(s), int(e)))
                # Middle column beat numbering with resets per group
                for (s, e) in groups:
                    for idx, k in enumerate(range(s, e + 1), start=1):
                        y = y_mm + (k - 1) * beat_len_mm
                        du.add_text(x_mid, y, str(idx), size_pt=18.0, color=color, id=0, tags=["ts_klavars_mid"], anchor='w', family="Courier New")
                # Final 1 at next measure barline
                du.add_text(x_mid, y_mm + measure_len_mm, "1", size_pt=18.0, color=color, id=0, tags=["ts_klavars_mid"], anchor='w', family="Courier New")
                # Left column: number the amount of beat groups at their start positions
                for gi, (s, _e) in enumerate(groups, start=1):
                    y = y_mm + (s - 1) * beat_len_mm
                    du.add_text(x_left, y, str(gi), size_pt=18.0, color=color, id=0, tags=["ts_klavars_left"], anchor='w', family="Courier New")

        # Iterate BaseGrid segments and draw based on indicator_type
        for bg in list(getattr(score, 'base_grid', []) or []):
            numerator = int(getattr(bg, 'numerator', 4) or 4)
            denominator = int(getattr(bg, 'denominator', 4) or 4)
            measure_amount = int(getattr(bg, 'measure_amount', 1) or 1)
            enabled = bool(getattr(bg, 'indicator_enabled', True))
            grid_positions = list(getattr(bg, 'grid_positions', []) or [])

            if indicator_type == 'classical':
                draw_classical(numerator, denominator, enabled, time_cursor)
            elif indicator_type == 'klavarskribo':
                draw_klavarskribo(numerator, denominator, enabled, time_cursor, grid_positions)
            elif indicator_type == 'both':
                # Draw classical now; Klavarskribo to be added later below or beside.
                draw_classical(numerator, denominator, enabled, time_cursor)
                draw_klavarskribo(numerator, denominator, enabled, time_cursor, grid_positions)

            # Advance time cursor by the segment length (mm) to next segment start
            quarters_per_measure = float(numerator) * (4.0 / max(1.0, float(denominator)))
            measure_len_mm = quarters_per_measure * float(score.editor.zoom_mm_per_quarter)
            time_cursor += measure_len_mm * float(measure_amount)
