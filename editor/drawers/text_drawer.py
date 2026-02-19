from __future__ import annotations
import math
from typing import TYPE_CHECKING, cast, Tuple
from ui.widgets.draw_util import DrawUtil

if TYPE_CHECKING:
    from editor.editor import Editor


class TextDrawerMixin:
    def _text_bbox(self, du: DrawUtil, text: str, family: str, size_pt: float, italic: bool, bold: bool, angle_deg: float) -> Tuple[float, float, float, list[tuple[float, float]]]:
        """Return (width_mm, height_mm, offset_down_mm, rotated_corners).

        - width/height are axis-aligned (unrotated) text extents.
        - offset_down_mm is how far to shift the center downward so the rotated
          polygon never crosses the time line (y=0 in local coords).
        - rotated_corners are relative to the text center after rotation.
        """
        # Text extents in mm (unrotated)
        xb, yb, w_mm, h_mm = du._get_text_extents_mm(text, family, size_pt, italic, bold)
        padding_mm = 0.5
        w_mm += padding_mm * 2.0
        h_mm += padding_mm * 2.0
        # Corner offsets before rotation (center anchor)
        hw = w_mm * 0.5
        hh = h_mm * 0.5
        corners = [
            (-hw, -hh),
            (hw, -hh),
            (hw, hh),
            (-hw, hh),
        ]
        ang = math.radians(angle_deg)
        sin_a = math.sin(ang)
        cos_a = math.cos(ang)
        rot_corners = []
        min_y = float("inf")
        for (dx, dy) in corners:
            rx = dx * cos_a - dy * sin_a
            ry = dx * sin_a + dy * cos_a
            rot_corners.append((rx, ry))
            if ry < min_y:
                min_y = ry
        # If any part goes above y=0, push down by that amount
        offset_down = max(0.0, -min_y)
        return w_mm, h_mm, offset_down, rot_corners

    def draw_text(self, du: DrawUtil) -> None:
        self = cast("Editor", self)
        score = getattr(self, 'current_score', lambda: None)()
        if score is None:
            return

        events = list(getattr(score.events, 'text', []) or [])
        if not events:
            return

        # Viewport culling
        top_mm = float(getattr(self, '_view_y_mm_offset', 0.0) or 0.0)
        vp_h_mm = float(getattr(self, '_viewport_h_mm', 0.0) or 0.0)
        bottom_mm = top_mm + vp_h_mm
        bleed_mm = max(2.0, float(getattr(score.editor, 'zoom_mm_per_quarter', 25.0) or 25.0) * 0.25)

        active_tool = str(getattr(getattr(self, '_tool', None), 'TOOL_NAME', ''))
        show_handles = active_tool == 'text'

        for ev in events:
            t = float(getattr(ev, 'time', 0.0) or 0.0)
            rp = int(getattr(ev, 'x_rpitch', 0) or 0)
            angle = float(getattr(ev, 'rotation', 0.0) or 0.0)
            txt = str(getattr(ev, 'text', ''))
            display_txt = txt if txt.strip() else "(no text set)"
            font = getattr(ev, 'font', None)
            use_custom = bool(getattr(ev, 'use_custom_font', False))
            if not use_custom or font is None:
                font = getattr(score.layout, 'font_text', None)
            family = font.resolve_family() if font and hasattr(font, 'resolve_family') else getattr(font, 'family', 'Courier New')
            size_pt = float(getattr(font, 'size_pt', 12.0) or 12.0)
            italic = bool(getattr(font, 'italic', False))
            bold = bool(getattr(font, 'bold', False))

            y_mm = float(self.time_to_mm(t))
            if y_mm < (top_mm - bleed_mm) or y_mm > (bottom_mm + bleed_mm):
                continue

            try:
                x_mm = float(self.relative_c4pitch_to_x(rp))
            except Exception:
                x_mm = 0.0

            try:
                w_mm, h_mm, offset_down, rot_corners = self._text_bbox(du, display_txt, family, size_pt, italic, bold, angle)
            except Exception:
                continue

            cy = y_mm + offset_down
            # Build rotated polygon in absolute coords
            poly = [(x_mm + dx, cy + dy) for (dx, dy) in rot_corners]
            min_x = min(p[0] for p in poly)
            max_x = max(p[0] for p in poly)
            min_y = min(p[1] for p in poly)
            max_y = max(p[1] for p in poly)

            # White background mask to cover stave behind text
            du.add_polygon(
                poly,
                stroke_color=None,
                fill_color=(1.0, 1.0, 1.0, 1.0),
                id=int(getattr(ev, '_id', 0) or 0),
                tags=["text"],
            )

            # Text itself (center anchor, rotated)
            du.add_text(
                x_mm,
                cy,
                display_txt,
                family=family,
                size_pt=size_pt,
                italic=italic,
                bold=bold,
                color=self.notation_color,
                anchor='center',
                angle_deg=angle,
                id=int(getattr(ev, '_id', 0) or 0),
                tags=["text"],
            )

            try:
                self.register_text_hit_rect(int(getattr(ev, '_id', 0) or 0), min_x, min_y, max_x, max_y, kind='body')
            except Exception:
                pass

            if show_handles:
                # Place handle just beyond the rotated right edge
                handle_gap = max(1.5, (self.semitone_dist or 2.5) * 0.3)
                handle_size = max(2.0, (self.semitone_dist or 2.5) * 0.6)
                rad = w_mm * 0.5 + handle_gap
                ang = math.radians(angle)
                hx = x_mm + rad * math.cos(ang)
                hy = cy + rad * math.sin(ang)
                hx1 = hx - handle_size * 0.5
                hx2 = hx + handle_size * 0.5
                hy1 = hy - handle_size * 0.5
                hy2 = hy + handle_size * 0.5
                du.add_rectangle(
                    hx1,
                    hy1,
                    hx2,
                    hy2,
                    stroke_color=self.accent_color,
                    stroke_width_mm=0.4,
                    fill_color=(1.0, 0.6, 0.2, 0.8),
                    id=int(getattr(ev, '_id', 0) or 0),
                    tags=["text", "text_handle"],
                )
                try:
                    self.register_text_hit_rect(int(getattr(ev, '_id', 0) or 0), hx1, hy1, hx2, hy2, kind='handle')
                except Exception:
                    pass
