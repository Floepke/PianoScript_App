from __future__ import annotations
from typing import TYPE_CHECKING, cast
from ui.widgets.draw_util import DrawUtil
from utils.CONSTANT import QUARTER_NOTE_UNIT

if TYPE_CHECKING:
    from editor.editor import Editor


class TempoDrawerMixin:
    def draw_tempo(self, du: DrawUtil) -> None:
        self = cast("Editor", self)
        score = self.current_score()
        if score is None:
            return

        # Layout anchors
        margin = float(self.margin or 0.0)
        # Draw on the outer right side of the editor page
        page_w_mm, _ = du.current_page_size_mm()

        # Iterate tempo events
        events = list(getattr(score.events, 'tempo', []) or [])
        if not events:
            return

        # Font setup: reuse C059 if available
        try:
            from fonts import register_font_from_bytes
            font_family = register_font_from_bytes('C059') or 'C059'
        except Exception:
            font_family = 'C059'

        for tp in events:
            try:
                t0 = float(getattr(tp, 'time', 0.0) or 0.0)
                du_ticks = float(getattr(tp, 'duration', 0.0) or 0.0)
                tempo_val = int(getattr(tp, 'tempo', 60) or 60)
            except Exception:
                continue
            if du_ticks <= 0.0:
                continue
            # Positions in mm
            y0 = float(self.time_to_mm(t0))
            y1 = float(self.time_to_mm(t0 + du_ticks))
            y3 = float(y0 + 50.0)
            if y1 < y0:
                y0, y1 = y1, y0
            # Text and rectangle sizing
            text = str(tempo_val)
            # Estimate extents in mm for unrotated text (width_mm, height_mm)
            _xb, _yb, w_mm, h_mm = du._get_text_extents_mm(text, font_family, 24.0, False, True)
            # Rotated 90°: horizontal width should accommodate original height
            rect_w = max(h_mm + 6.0, 10.0)
            # Place rectangle near the outer right page edge
            x_left = float(page_w_mm) - rect_w - margin * 0.35
            # Underlay rectangle (grey) with height equal to rotated text height
            du.add_rectangle(x_left, y0, x_left + rect_w, y0 + w_mm + 3.0,
                             stroke_color=None, fill_color=(0.7, 0.7, 0.7, 1), id=0,
                             tags=["tempo_under"], dash_pattern=None)
            # Background rectangle (black)
            du.add_rectangle(x_left, y0, x_left + rect_w, y1,
                             stroke_color=None, fill_color=(0, 0, 0, 1), id=0,
                             tags=["tempo_bg"], dash_pattern=None)
            # add guide start line (black)
            du.add_line(page_w_mm - margin - self.semitone_dist * 2, y0, x_left, y0,
                        color=(0, 0, 0, 1), width_mm=0.25, id=0,
                        tags=["tempo_guide_line"], dash_pattern=[0,1])
            # add guide line end (black)
            du.add_line(page_w_mm - margin - self.semitone_dist * 2, y1, x_left, y1,
                        color=(0, 0, 0, 1), width_mm=0.25, id=0,
                        tags=["tempo_guide_line"], dash_pattern=[0,1])
            # Rotated white text: center horizontally inside rectangle; start at top side
            # After 90° rotation, visual width along x ≈ unrotated height
            x_text = x_left + (rect_w - h_mm) / 2.0 + .41
            y_text = y0 + 2.0
            du.add_text(x_text, y_text, text,
                        family=font_family, size_pt=24.0, italic=False, bold=True,
                        color=(1, 1, 1, 1), anchor=None, id=0, tags=["tempo_text"],
                        hit_rect_mm=None, angle_deg=90.0)
