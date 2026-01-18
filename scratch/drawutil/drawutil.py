from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, Sequence, Tuple
import os

import cairo

# Units: millimeters (mm) with origin at top-left.
# Rendering: Cairo ImageSurface scaled by px_per_mm.

Color = Tuple[float, float, float, float]

MM_PER_INCH = 25.4
PT_PER_INCH = 72.0
PT_PER_MM = PT_PER_INCH / MM_PER_INCH


@dataclass
class Stroke:
    color: Color = (0, 0, 0, 1)
    width_mm: float = 0.3
    dash_pattern_mm: Optional[Sequence[float]] = None
    dash_offset_mm: float = 0.0


@dataclass
class Fill:
    color: Color = (0, 0, 0, 0)


@dataclass
class Line:
    x1_mm: float
    y1_mm: float
    x2_mm: float
    y2_mm: float
    stroke: Stroke = field(default_factory=Stroke)
    tags: List[str] = field(default_factory=list)
    hit_rect_mm: Optional[Tuple[float, float, float, float]] = None


@dataclass
class Rect:
    x_mm: float
    y_mm: float
    w_mm: float
    h_mm: float
    stroke: Optional[Stroke] = field(default_factory=Stroke)
    fill: Optional[Fill] = field(default_factory=Fill)
    tags: List[str] = field(default_factory=list)
    hit_rect_mm: Optional[Tuple[float, float, float, float]] = None


@dataclass
class Polyline:
    points_mm: List[Tuple[float, float]]
    closed: bool = False
    stroke: Optional[Stroke] = field(default_factory=Stroke)
    fill: Optional[Fill] = field(default_factory=Fill)
    tags: List[str] = field(default_factory=list)
    hit_rect_mm: Optional[Tuple[float, float, float, float]] = None


@dataclass
class Text:
    x_mm: float
    y_mm: float
    text: str
    family: str = "Sans"
    size_pt: float = 10.0
    italic: bool = False
    bold: bool = False
    color: Color = (0, 0, 0, 1)
    tags: List[str] = field(default_factory=list)
    hit_rect_mm: Optional[Tuple[float, float, float, float]] = None


class DrawUtil:
    def __init__(self) -> None:
        self._width_mm: float = 0.0
        self._height_mm: float = 0.0
        self._items: List[object] = []

    def set_drawing_size_mm(self, width_mm: float, height_mm: float) -> None:
        self._width_mm = float(max(0.0, width_mm))
        self._height_mm = float(max(0.0, height_mm))

    def drawing_size_mm(self) -> Tuple[float, float]:
        return (self._width_mm, self._height_mm)

    def clear(self) -> None:
        self._items.clear()

    # ---- Add items ----

    def add_line(self, x1_mm: float, y1_mm: float, x2_mm: float, y2_mm: float,
                 color: Color = (0, 0, 0, 1), width_mm: float = 0.3,
                 dash_pattern: Optional[Sequence[float]] = None,
                 dash_offset_mm: float = 0.0,
                 tags: Optional[List[str]] = None,
                 hit_rect_mm: Optional[Tuple[float, float, float, float]] = None) -> None:
        stroke = Stroke(color=color, width_mm=width_mm,
                        dash_pattern_mm=dash_pattern, dash_offset_mm=dash_offset_mm)
        if tags is None:
            tags = []
        if hit_rect_mm is None:
            x = min(x1_mm, x2_mm)
            y = min(y1_mm, y2_mm)
            w = abs(x2_mm - x1_mm)
            h = abs(y2_mm - y1_mm)
            hit_rect_mm = (x, y, w, h)
        self._items.append(Line(x1_mm, y1_mm, x2_mm, y2_mm, stroke, tags, hit_rect_mm))

    def add_rectangle(self,
                      x_mm: float,
                      y_mm: float,
                      w_mm: float,
                      h_mm: float,
                      stroke_color: Optional[Color] = (0, 0, 0, 1),
                      stroke_width_mm: float = 0.3,
                      fill_color: Optional[Color] = None,
                      dash_pattern: Optional[Sequence[float]] = None,
                      dash_offset_mm: float = 0.0,
                      tags: Optional[List[str]] = None,
                      hit_rect_mm: Optional[Tuple[float, float, float, float]] = None,
                      *,
                      x2_mm: Optional[float] = None,
                      y2_mm: Optional[float] = None,
                      as_points: Optional[bool] = None) -> None:
        stroke = Stroke(stroke_color, stroke_width_mm, dash_pattern, dash_offset_mm) if stroke_color is not None else None
        fill = Fill(fill_color) if fill_color is not None else None
        if tags is None:
            tags = []
        use_points = bool(as_points) or (x2_mm is not None and y2_mm is not None)
        if use_points:
            x_a = float(x_mm)
            y_a = float(y_mm)
            x_b = float(x2_mm if x2_mm is not None else x_mm)
            y_b = float(y2_mm if y2_mm is not None else y_mm)
            rx = min(x_a, x_b)
            ry = min(y_a, y_b)
            rw = abs(x_b - x_a)
            rh = abs(y_b - y_a)
        else:
            rx = float(x_mm)
            ry = float(y_mm)
            rw = float(w_mm)
            rh = float(h_mm)
        if hit_rect_mm is None:
            hit_rect_mm = (rx, ry, rw, rh)
        self._items.append(Rect(rx, ry, rw, rh, stroke, fill, tags, hit_rect_mm))

    def add_polyline(self, points_mm: Sequence[Tuple[float, float]],
                     stroke_color: Optional[Color] = (0, 0, 0, 1),
                     stroke_width_mm: float = 0.3,
                     closed: bool = False,
                     fill_color: Optional[Color] = None,
                     dash_pattern: Optional[Sequence[float]] = None,
                     dash_offset_mm: float = 0.0,
                     tags: Optional[List[str]] = None,
                     hit_rect_mm: Optional[Tuple[float, float, float, float]] = None) -> None:
        stroke = Stroke(stroke_color, stroke_width_mm, dash_pattern, dash_offset_mm) if stroke_color is not None else None
        fill = Fill(fill_color) if fill_color is not None else None
        if tags is None:
            tags = []
        if hit_rect_mm is None:
            xs = [p[0] for p in points_mm]
            ys = [p[1] for p in points_mm]
            x = min(xs) if xs else 0.0
            y = min(ys) if ys else 0.0
            w = (max(xs) - x) if xs else 0.0
            h = (max(ys) - y) if ys else 0.0
            hit_rect_mm = (x, y, w, h)
        self._items.append(Polyline(list(points_mm), closed, stroke, fill, tags, hit_rect_mm))

    def add_text(self, x_mm: float, y_mm: float, text: str,
                 family: str = "Sans", size_pt: float = 10.0,
                 italic: bool = False, bold: bool = False,
                 color: Color = (0, 0, 0, 1),
                 tags: Optional[List[str]] = None,
                 hit_rect_mm: Optional[Tuple[float, float, float, float]] = None) -> None:
        if tags is None:
            tags = []
        if hit_rect_mm is None:
            hit_rect_mm = self._compute_text_hit_rect_mm(x_mm, y_mm, text, family, size_pt, italic, bold)
        self._items.append(Text(x_mm, y_mm, text, family, size_pt, italic, bold, color, tags, hit_rect_mm))

    # ---- Render ----

    def render_viewport(self, ctx: cairo.Context, px_per_mm: float,
                        clip_rect_mm: Tuple[float, float, float, float], overscan_mm: float = 0.5) -> None:
        """Render only the viewport region:
        - Scales user units to mm
        - Clips via Cairo with an overscan margin to avoid antialias cutoff
        - Translates so viewport origin is at (0,0)
        - Explicitly clips line endpoints to viewport borders
        - Culls items using hit_rect intersection
        """
        x, y, w, h = clip_rect_mm
        ctx.save()
        ctx.scale(px_per_mm, px_per_mm)
        # Cairo clip strictly to viewport to anchor borders
        ctx.rectangle(x, y, w, h)
        ctx.clip()
        # Translate by true viewport origin (no overscan)
        ctx.translate(-x, -y)
        vp_w = w
        vp_h = h
        # Iterate items in insertion order; cull by rect
        for it in self._iter_items_culled(clip_rect_mm):
            if isinstance(it, Line):
                self._draw_line_clipped(ctx, it, x, y, vp_w, vp_h)
            elif isinstance(it, Rect):
                self._draw_rect(ctx, it)
            elif isinstance(it, Polyline):
                self._draw_polyline(ctx, it)
            elif isinstance(it, Text):
                self._draw_text(ctx, it)
        ctx.restore()

    # ---- PX-based viewport rendering (no Cairo scale) ----
    def render_viewport_px(self, ctx: cairo.Context, px_per_mm: float,
                           clip_rect_px: Tuple[int, int, int, int]) -> None:
        """Render using px-space for the viewport with programmatic trimming only.

        - No Cairo scaling; convert mm→px per item
        - Translate by -clip origin so (0,0) anchors the viewport
        - Do not use Cairo clip; trim shapes against viewport rectangle in px
        """
        rx, ry, rw, rh = [int(v) for v in clip_rect_px]
        if rw <= 0 or rh <= 0:
            return
        debug = os.getenv('DEBUG_CLIP', '0') in ('1', 'true', 'True')
        if debug:
            print(f"[DrawUtil] clip_rect_px rx={rx} ry={ry} rw={rw} rh={rh} px_per_mm={px_per_mm:.4f}")
        ctx.save()
        # Anchor drawing to viewport origin
        ctx.translate(-rx, -ry)
        vp_w = float(rw)
        vp_h = float(rh)
        # Optional visible borders at top/bottom of viewport
        if os.getenv('DEBUG_BORDERS', '0') in ('1', 'true', 'True'):
            ctx.save()
            # Top border (green)
            ctx.set_source_rgba(0.1, 0.7, 0.1, 0.9)
            ctx.set_line_width(1.0)
            ctx.move_to(0.0, 0.0)
            ctx.line_to(vp_w, 0.0)
            ctx.stroke()
            # Bottom border (red)
            ctx.set_source_rgba(0.8, 0.1, 0.1, 0.9)
            ctx.move_to(0.0, vp_h)
            ctx.line_to(vp_w, vp_h)
            ctx.stroke()
            ctx.restore()
        top_hits = 0
        bottom_hits = 0
        sample_top: List[Tuple[float, float, float, float]] = []
        sample_bottom: List[Tuple[float, float, float, float]] = []
        eps = 0.75  # tolerance in px for border alignment
        # Draw items with explicit trimming
        for it in self._items:
            if isinstance(it, Line):
                # Convert endpoints to viewport px (0..rw, 0..rh)
                x1 = it.x1_mm * px_per_mm - rx
                y1 = it.y1_mm * px_per_mm - ry
                x2 = it.x2_mm * px_per_mm - rx
                y2 = it.y2_mm * px_per_mm - ry
                clipped = self._clip_line_rect_viewport_px(x1, y1, x2, y2, rw, rh)
                if clipped is None:
                    continue
                cx1, cy1, cx2, cy2 = clipped
                # Diagnostics: check border alignments
                if abs(cy1 - 0.0) < eps or abs(cy2 - 0.0) < eps:
                    top_hits += 1
                    if len(sample_top) < 3:
                        sample_top.append((cx1, cy1, cx2, cy2))
                if abs(cy1 - rh) < eps or abs(cy2 - rh) < eps:
                    bottom_hits += 1
                    if len(sample_bottom) < 3:
                        sample_bottom.append((cx1, cy1, cx2, cy2))
                self._apply_stroke_px(ctx, it.stroke, px_per_mm)
                ctx.move_to(cx1, cy1)
                ctx.line_to(cx2, cy2)
                ctx.stroke()
            elif isinstance(it, Rect):
                # Trim rectangle to viewport and draw the intersection
                self._draw_rect_px_trimmed(ctx, it, px_per_mm, rx, ry, vp_w, vp_h)
            elif isinstance(it, Polyline):
                # Draw clipped polyline segments in viewport space
                self._draw_polyline_px_trimmed(ctx, it, px_per_mm, rx, ry, vp_w, vp_h)
            elif isinstance(it, Text):
                # Cull by text bbox in viewport space
                self._draw_text_px_culled(ctx, it, px_per_mm, rx, ry, vp_w, vp_h)
        if debug:
            print(f"[DrawUtil] viewport bounds y=[0..{rh}] top_hits={top_hits} bottom_hits={bottom_hits}")
            for i, (cx1, cy1, cx2, cy2) in enumerate(sample_top):
                print(f"  top#{i}: ({cx1:.1f},{cy1:.1f})->({cx2:.1f},{cy2:.1f})")
            for i, (cx1, cy1, cx2, cy2) in enumerate(sample_bottom):
                print(f"  bottom#{i}: ({cx1:.1f},{cy1:.1f})->({cx2:.1f},{cy2:.1f})")
        ctx.restore()

    def _apply_stroke_px(self, ctx: cairo.Context, stroke: Stroke, px_per_mm: float):
        ctx.set_source_rgba(*stroke.color)
        ctx.set_line_width(max(0.5, stroke.width_mm * px_per_mm))
        ctx.set_line_join(cairo.LINE_JOIN_ROUND)
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        if stroke.dash_pattern_mm:
            # Convert dash lengths to px
            dashes_px = [max(0.5, d * px_per_mm) for d in stroke.dash_pattern_mm]
            ctx.set_dash(dashes_px, stroke.dash_offset_mm * px_per_mm)
        else:
            ctx.set_dash([])

    def _draw_rect_px_trimmed(self, ctx: cairo.Context, r: Rect, px_per_mm: float,
                              rx: int, ry: int, vp_w: float, vp_h: float):
        x = r.x_mm * px_per_mm - rx
        y = r.y_mm * px_per_mm - ry
        w = r.w_mm * px_per_mm
        h = r.h_mm * px_per_mm
        # Intersect with viewport
        ix = max(0.0, x)
        iy = max(0.0, y)
        iw = min(vp_w, x + w) - ix
        ih = min(vp_h, y + h) - iy
        if iw <= 0.0 or ih <= 0.0:
            return
        ctx.new_path()
        ctx.rectangle(ix, iy, iw, ih)
        if r.fill:
            ctx.set_source_rgba(*r.fill.color)
            ctx.fill_preserve()
        if r.stroke:
            self._apply_stroke_px(ctx, r.stroke, px_per_mm)
            ctx.stroke()
        else:
            ctx.new_path()

    def _draw_polyline_px_trimmed(self, ctx: cairo.Context, pl: Polyline, px_per_mm: float,
                                  rx: int, ry: int, vp_w: float, vp_h: float):
        pts = pl.points_mm
        if not pts:
            return
        # Clip each segment and draw
        self._apply_stroke_px(ctx, pl.stroke or Stroke(), px_per_mm)
        for i in range(len(pts) - 1):
            x1 = pts[i][0] * px_per_mm - rx
            y1 = pts[i][1] * px_per_mm - ry
            x2 = pts[i+1][0] * px_per_mm - rx
            y2 = pts[i+1][1] * px_per_mm - ry
            clipped = self._clip_line_rect_viewport_px(x1, y1, x2, y2, int(vp_w), int(vp_h))
            if clipped is None:
                continue
            cx1, cy1, cx2, cy2 = clipped
            ctx.move_to(cx1, cy1)
            ctx.line_to(cx2, cy2)
            ctx.stroke()

    def _draw_text_px_culled(self, ctx: cairo.Context, t: Text, px_per_mm: float,
                              rx: int, ry: int, vp_w: float, vp_h: float):
        # Compute rough bbox in px (viewport coords) and cull
        x_px = t.x_mm * px_per_mm - rx
        y_px = t.y_mm * px_per_mm - ry
        slant = cairo.FONT_SLANT_ITALIC if t.italic else cairo.FONT_SLANT_NORMAL
        weight = cairo.FONT_WEIGHT_BOLD if t.bold else cairo.FONT_WEIGHT_NORMAL
        ctx.select_font_face(t.family, slant, weight)
        # Convert pt size to px: size_pt * (px_per_mm * mm_per_pt) = size_pt * (px_per_mm / PT_PER_MM)
        px_per_pt = px_per_mm / PT_PER_MM
        ctx.set_font_size(max(1.0, t.size_pt * px_per_pt))
        # Get text extents in current font size (px)
        te = ctx.text_extents(t.text)
        bx = x_px + te.x_bearing
        by = y_px + te.y_bearing
        bw = te.width
        bh = te.height
        if (bx + bw) < 0 or bx > vp_w or (by + bh) < 0 or by > vp_h:
            return
        ctx.set_source_rgba(*t.color)
        ctx.move_to(x_px, y_px)
        ctx.show_text(t.text)

    def _clip_line_rect_viewport_px(self, x1: float, y1: float, x2: float, y2: float,
                                    rw: int, rh: int):
        # Rect bounds in viewport px coordinates (0..rw, 0..rh)
        x_min = 0.0
        y_min = 0.0
        x_max = float(rw)
        y_max = float(rh)
        dx = x2 - x1
        dy = y2 - y1
        p = [-dx, dx, -dy, dy]
        q = [x1 - x_min, x_max - x1, y1 - y_min, y_max - y1]
        u1, u2 = 0.0, 1.0
        for pi, qi in zip(p, q):
            if pi == 0.0:
                if qi < 0.0:
                    return None
            else:
                t = qi / pi
                if pi < 0.0:
                    if t > u2:
                        return None
                    if t > u1:
                        u1 = t
                else:
                    if t < u1:
                        return None
                    if t < u2:
                        u2 = t
        cx1 = x1 + u1 * dx
        cy1 = y1 + u1 * dy
        cx2 = x1 + u2 * dx
        cy2 = y1 + u2 * dy
        # Fully outside guards
        if (cx1 < x_min and cx2 < x_min) or (cx1 > x_max and cx2 > x_max) or \
           (cy1 < y_min and cy2 < y_min) or (cy1 > y_max and cy2 > y_max):
            return None
        return (cx1, cy1, cx2, cy2)

    def _iter_items_culled(self, clip_rect_mm: Tuple[float, float, float, float]):
        cx, cy, cw, ch = clip_rect_mm
        for it in self._items:
            rect = getattr(it, "hit_rect_mm", None)
            if rect is None:
                yield it
                continue
            rx, ry, rw, rh = rect
            if not (rx + rw < cx or cx + cw < rx or ry + rh < cy or cy + ch < ry):
                yield it

    def _apply_stroke(self, ctx: cairo.Context, stroke: Stroke):
        ctx.set_source_rgba(*stroke.color)
        ctx.set_line_width(stroke.width_mm)
        ctx.set_line_join(cairo.LINE_JOIN_ROUND)
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        if stroke.dash_pattern_mm:
            ctx.set_dash(list(stroke.dash_pattern_mm), stroke.dash_offset_mm)
        else:
            ctx.set_dash([])

    def _apply_fill(self, ctx: cairo.Context, fill: Optional[Fill]):
        if fill and fill.color[3] > 0:
            ctx.set_source_rgba(*fill.color)
            ctx.fill_preserve()

    # Liang–Barsky clipping for a line segment in viewport space
    def _clip_line_to_viewport(self, x1: float, y1: float, x2: float, y2: float, vp_w: float, vp_h: float):
        dx = x2 - x1
        dy = y2 - y1
        p = [-dx, dx, -dy, dy]
        q = [x1, vp_w - x1, y1, vp_h - y1]
        u1 = 0.0
        u2 = 1.0
        for pi, qi in zip(p, q):
            if pi == 0.0:
                if qi < 0.0:
                    return None
            else:
                t = qi / pi
                if pi < 0.0:
                    if t > u2:
                        return None
                    if t > u1:
                        u1 = t
                else:  # pi > 0
                    if t < u1:
                        return None
                    if t < u2:
                        u2 = t
        cx1 = x1 + u1 * dx
        cy1 = y1 + u1 * dy
        cx2 = x1 + u2 * dx
        cy2 = y1 + u2 * dy
        return (cx1, cy1, cx2, cy2)

    def _draw_line_clipped(self, ctx: cairo.Context, line: Line, x_o: float, y_o: float, vp_w_mm: float, vp_h_mm: float):
        x1 = line.x1_mm - x_o
        y1 = line.y1_mm - y_o
        x2 = line.x2_mm - x_o
        y2 = line.y2_mm - y_o
        clipped = self._clip_line_to_viewport(x1, y1, x2, y2, vp_w_mm, vp_h_mm)
        if clipped is None:
            return
        cx1, cy1, cx2, cy2 = clipped
        self._apply_stroke(ctx, line.stroke)
        ctx.move_to(cx1, cy1)
        ctx.line_to(cx2, cy2)
        ctx.stroke()

    def _draw_rect(self, ctx: cairo.Context, r: Rect):
        ctx.new_path()
        ctx.rectangle(r.x_mm, r.y_mm, r.w_mm, r.h_mm)
        if r.fill:
            self._apply_fill(ctx, r.fill)
        if r.stroke:
            self._apply_stroke(ctx, r.stroke)
            ctx.stroke()
        else:
            ctx.new_path()

    def _draw_polyline(self, ctx: cairo.Context, pl: Polyline):
        pts = pl.points_mm
        if not pts:
            return
        ctx.new_path()
        ctx.move_to(pts[0][0], pts[0][1])
        for (x, y) in pts[1:]:
            ctx.line_to(x, y)
        if pl.closed:
            ctx.close_path()
        if pl.fill and pl.closed:
            self._apply_fill(ctx, pl.fill)
        if pl.stroke:
            self._apply_stroke(ctx, pl.stroke)
            ctx.stroke()
        else:
            ctx.new_path()

    def _draw_text(self, ctx: cairo.Context, t: Text):
        slant = cairo.FONT_SLANT_ITALIC if t.italic else cairo.FONT_SLANT_NORMAL
        weight = cairo.FONT_WEIGHT_BOLD if t.bold else cairo.FONT_WEIGHT_NORMAL
        ctx.select_font_face(t.family, slant, weight)
        ctx.set_font_size(t.size_pt * PT_PER_MM)
        ctx.set_source_rgba(*t.color)
        ctx.move_to(t.x_mm, t.y_mm)
        ctx.show_text(t.text)

    def _compute_text_hit_rect_mm(self, x_mm: float, y_mm: float, text: str,
                                  family: str, size_pt: float,
                                  italic: bool, bold: bool) -> Tuple[float, float, float, float]:
        surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, 1, 1)
        ctx = cairo.Context(surf)
        slant = cairo.FONT_SLANT_ITALIC if italic else cairo.FONT_SLANT_NORMAL
        weight = cairo.FONT_WEIGHT_BOLD if bold else cairo.FONT_WEIGHT_NORMAL
        ctx.select_font_face(family, slant, weight)
        ctx.set_font_size(size_pt)
        te = ctx.text_extents(text)
        x_bearing_mm = te.x_bearing / PT_PER_MM
        y_bearing_mm = te.y_bearing / PT_PER_MM
        width_mm = te.width / PT_PER_MM
        height_mm = te.height / PT_PER_MM
        rect_x = x_mm + x_bearing_mm
        rect_y = y_mm + y_bearing_mm
        return (rect_x, rect_y, width_mm, height_mm)
