from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, Sequence, Tuple
import cairo

MM_PER_INCH = 25.4
PT_PER_INCH = 72.0
PT_PER_MM = PT_PER_INCH / MM_PER_INCH

Color = Tuple[float, float, float, float]


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
    # Picking metadata
    id: int = 0
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
    # Picking metadata
    id: int = 0
    tags: List[str] = field(default_factory=list)
    hit_rect_mm: Optional[Tuple[float, float, float, float]] = None


@dataclass
class Oval:
    x_mm: float
    y_mm: float
    w_mm: float
    h_mm: float
    stroke: Optional[Stroke] = field(default_factory=Stroke)
    fill: Optional[Fill] = field(default_factory=Fill)
    # Picking metadata
    id: int = 0
    tags: List[str] = field(default_factory=list)
    hit_rect_mm: Optional[Tuple[float, float, float, float]] = None


@dataclass
class Polyline:
    points_mm: List[Tuple[float, float]]
    closed: bool = False
    stroke: Optional[Stroke] = field(default_factory=Stroke)
    fill: Optional[Fill] = field(default_factory=Fill)
    # Picking metadata
    id: int = 0
    tags: List[str] = field(default_factory=list)
    hit_rect_mm: Optional[Tuple[float, float, float, float]] = None


@dataclass
class Page:
    width_mm: float
    height_mm: float
    items: List[object] = field(default_factory=list)


# ---- Text item ----

@dataclass
class Text:
    x_mm: float
    y_mm: float  # baseline Y position in mm
    text: str
    family: str = "Sans"
    size_pt: float = 10.0
    italic: bool = False
    bold: bool = False
    color: Color = (0, 0, 0, 1)
    # Identity and picking
    id: int = 0  # non-zero => clickable; 0 => skip detection
    tags: List[str] = field(default_factory=list)
    hit_rect_mm: Optional[Tuple[float, float, float, float]] = None  # (x,y,w,h)


class DrawUtil:
    def __init__(self) -> None:
        self._pages: List[Page] = []
        self._current_index: int = -1

    def new_page(self, width_mm: float, height_mm: float) -> None:
        self._pages.append(Page(width_mm, height_mm))
        self._current_index = len(self._pages) - 1

    def set_current_page(self, index: int) -> None:
        if not (0 <= index < len(self._pages)):
            raise IndexError("Page index out of range")
        self._current_index = index

    def current_page_index(self) -> int:
        return self._current_index

    def page_count(self) -> int:
        return len(self._pages)

    def current_page_size_mm(self) -> Tuple[float, float]:
        if self._current_index < 0:
            return (0.0, 0.0)
        p = self._pages[self._current_index]
        return (p.width_mm, p.height_mm)

    def set_current_page_size_mm(self, width_mm: float, height_mm: float) -> None:
        """Update the current page dimensions (mm) without altering items.

        If there is no current page, creates one.
        """
        width_mm = float(max(0.0, width_mm))
        height_mm = float(max(0.0, height_mm))
        if self._current_index < 0:
            self.new_page(width_mm or 210.0, height_mm or 297.0)
            return
        p = self._pages[self._current_index]
        p.width_mm = width_mm or p.width_mm
        p.height_mm = height_mm or p.height_mm

    def add_line(self, x1_mm: float, y1_mm: float, x2_mm: float, y2_mm: float,
                 color: Color = (0, 0, 0, 1), width_mm: float = 0.3,
                 dash_pattern: Optional[Sequence[float]] = None,
                 dash_offset_mm: float = 0.0,
                 id: int = 0, tags: Optional[List[str]] = None,
                 hit_rect_mm: Optional[Tuple[float, float, float, float]] = None) -> None:
        self._ensure_page()
        stroke = Stroke(color=color, width_mm=width_mm,
                        dash_pattern_mm=dash_pattern, dash_offset_mm=dash_offset_mm)
        if tags is None:
            tags = []
        if hit_rect_mm is None and id != 0:
            x = min(x1_mm, x2_mm)
            y = min(y1_mm, y2_mm)
            w = abs(x2_mm - x1_mm)
            h = abs(y2_mm - y1_mm)
            hit_rect_mm = (x, y, w, h)
        self._pages[self._current_index].items.append(Line(x1_mm, y1_mm, x2_mm, y2_mm, stroke, id, tags, hit_rect_mm))

    def add_rectangle(self, x_mm: float, y_mm: float, w_mm: float, h_mm: float,
                      stroke_color: Optional[Color] = (0, 0, 0, 1),
                      stroke_width_mm: float = 0.3,
                      fill_color: Optional[Color] = None,
                      dash_pattern: Optional[Sequence[float]] = None,
                      dash_offset_mm: float = 0.0,
                      id: int = 0, tags: Optional[List[str]] = None,
                      hit_rect_mm: Optional[Tuple[float, float, float, float]] = None) -> None:
        self._ensure_page()
        stroke = None
        fill = None
        if stroke_color is not None:
            stroke = Stroke(stroke_color, stroke_width_mm, dash_pattern, dash_offset_mm)
        if fill_color is not None:
            fill = Fill(fill_color)
        if tags is None:
            tags = []
        if hit_rect_mm is None and id != 0:
            hit_rect_mm = (x_mm, y_mm, w_mm, h_mm)
        self._pages[self._current_index].items.append(Rect(x_mm, y_mm, w_mm, h_mm, stroke, fill, id, tags, hit_rect_mm))

    def add_oval(self, x_mm: float, y_mm: float, w_mm: float, h_mm: float,
                 stroke_color: Optional[Color] = (0, 0, 0, 1),
                 stroke_width_mm: float = 0.3,
                 fill_color: Optional[Color] = None,
                 dash_pattern: Optional[Sequence[float]] = None,
                 dash_offset_mm: float = 0.0,
                 id: int = 0, tags: Optional[List[str]] = None,
                 hit_rect_mm: Optional[Tuple[float, float, float, float]] = None) -> None:
        self._ensure_page()
        stroke = None
        fill = None
        if stroke_color is not None:
            stroke = Stroke(stroke_color, stroke_width_mm, dash_pattern, dash_offset_mm)
        if fill_color is not None:
            fill = Fill(fill_color)
        if tags is None:
            tags = []
        if hit_rect_mm is None and id != 0:
            hit_rect_mm = (x_mm, y_mm, w_mm, h_mm)
        self._pages[self._current_index].items.append(Oval(x_mm, y_mm, w_mm, h_mm, stroke, fill, id, tags, hit_rect_mm))

    def add_polygon(self, points_mm: Sequence[Tuple[float, float]],
                    stroke_color: Optional[Color] = (0, 0, 0, 1),
                    stroke_width_mm: float = 0.3,
                    fill_color: Optional[Color] = None,
                    dash_pattern: Optional[Sequence[float]] = None,
                    dash_offset_mm: float = 0.0,
                    id: int = 0, tags: Optional[List[str]] = None,
                    hit_rect_mm: Optional[Tuple[float, float, float, float]] = None) -> None:
        self._ensure_page()
        stroke = None
        fill = None
        if stroke_color is not None:
            stroke = Stroke(stroke_color, stroke_width_mm, dash_pattern, dash_offset_mm)
        if fill_color is not None:
            fill = Fill(fill_color)
        if tags is None:
            tags = []
        if hit_rect_mm is None and id != 0:
            xs = [p[0] for p in points_mm]
            ys = [p[1] for p in points_mm]
            x = min(xs) if xs else 0.0
            y = min(ys) if ys else 0.0
            w = (max(xs) - x) if xs else 0.0
            h = (max(ys) - y) if ys else 0.0
            hit_rect_mm = (x, y, w, h)
        self._pages[self._current_index].items.append(Polyline(list(points_mm), True, stroke, fill, id, tags, hit_rect_mm))

    def add_polyline(self, points_mm: Sequence[Tuple[float, float]],
                     stroke_color: Optional[Color] = (0, 0, 0, 1),
                     stroke_width_mm: float = 0.3,
                     dash_pattern: Optional[Sequence[float]] = None,
                     dash_offset_mm: float = 0.0,
                     id: int = 0, tags: Optional[List[str]] = None,
                     hit_rect_mm: Optional[Tuple[float, float, float, float]] = None) -> None:
        self._ensure_page()
        stroke = Stroke(stroke_color, stroke_width_mm, dash_pattern, dash_offset_mm)
        if tags is None:
            tags = []
        if hit_rect_mm is None and id != 0:
            xs = [p[0] for p in points_mm]
            ys = [p[1] for p in points_mm]
            x = min(xs) if xs else 0.0
            y = min(ys) if ys else 0.0
            w = (max(xs) - x) if xs else 0.0
            h = (max(ys) - y) if ys else 0.0
            hit_rect_mm = (x, y, w, h)
        self._pages[self._current_index].items.append(Polyline(list(points_mm), False, stroke, None, id, tags, hit_rect_mm))

    def add_text(self, x_mm: float, y_mm: float, text: str,
                 family: str = "Sans", size_pt: float = 10.0,
                 italic: bool = False, bold: bool = False,
                 color: Color = (0, 0, 0, 1),
                 id: int = 0, tags: Optional[List[str]] = None,
                 hit_rect_mm: Optional[Tuple[float, float, float, float]] = None) -> None:
        """Add a text item. y_mm is the baseline.

        If hit_rect_mm is not provided, it will be computed from toy-text extents
        (approximate; upgrade to PangoCairo later for robust metrics).
        """
        self._ensure_page()
        if tags is None:
            tags = []
        if hit_rect_mm is None:
            hit_rect_mm = self._compute_text_hit_rect_mm(x_mm, y_mm, text, family, size_pt, italic, bold)
        self._pages[self._current_index].items.append(
            Text(x_mm, y_mm, text, family, size_pt, italic, bold, color, id, tags, hit_rect_mm)
        )

    def _ensure_page(self) -> None:
        if self._current_index < 0:
            raise RuntimeError("No page: call new_page(width_mm, height_mm) first")

    def render_to_cairo(self, ctx: cairo.Context, page_index: int, px_per_mm: float) -> None:
        page = self._pages[page_index]
        ctx.save()
        ctx.set_antialias(cairo.ANTIALIAS_BEST)
        ctx.scale(px_per_mm, px_per_mm)
        ctx.save()
        ctx.set_source_rgb(1, 1, 1)
        ctx.rectangle(0, 0, page.width_mm, page.height_mm)
        ctx.fill()
        ctx.restore()

        for item in page.items:
            if isinstance(item, Line):
                self._draw_line(ctx, item)
            elif isinstance(item, Rect):
                self._draw_rect(ctx, item)
            elif isinstance(item, Oval):
                self._draw_oval(ctx, item)
            elif isinstance(item, Polyline):
                self._draw_polyline(ctx, item)
            elif isinstance(item, Text):
                self._draw_text(ctx, item)
        ctx.restore()

    # ---- Hit detection ----

    def _rect_contains_point(self, rect_mm: Tuple[float, float, float, float], x_mm: float, y_mm: float) -> bool:
        rx, ry, rw, rh = rect_mm
        return (x_mm >= rx) and (y_mm >= ry) and (x_mm <= rx + rw) and (y_mm <= ry + rh)

    def hit_test_point_mm(self, x_mm: float, y_mm: float, page_index: Optional[int] = None):
        """Return the smallest-area clickable item at (x_mm, y_mm) or None.

        Only items with `id != 0` and a `hit_rect_mm` are considered.
        """
        if page_index is None:
            page_index = self._current_index
        if page_index < 0 or page_index >= len(self._pages):
            return None
        page = self._pages[page_index]
        candidates = []
        for item in page.items:
            rect = getattr(item, "hit_rect_mm", None)
            item_id = getattr(item, "id", 0)
            if item_id == 0 or rect is None:
                continue
            if self._rect_contains_point(rect, x_mm, y_mm):
                rx, ry, rw, rh = rect
                area = max(0.0, rw * rh)
                candidates.append((area, item))
        if not candidates:
            return None
        candidates.sort(key=lambda t: t[0])
        return candidates[0][1]

    def hit_test_all_point_mm(self, x_mm: float, y_mm: float, page_index: Optional[int] = None):
        """Return list of all clickable items at (x_mm, y_mm) sorted by area ascending."""
        if page_index is None:
            page_index = self._current_index
        if page_index < 0 or page_index >= len(self._pages):
            return []
        page = self._pages[page_index]
        out = []
        for item in page.items:
            rect = getattr(item, "hit_rect_mm", None)
            item_id = getattr(item, "id", 0)
            if item_id == 0 or rect is None:
                continue
            if self._rect_contains_point(rect, x_mm, y_mm):
                rx, ry, rw, rh = rect
                area = max(0.0, rw * rh)
                out.append((area, item))
        out.sort(key=lambda t: t[0])
        return [i for (_a, i) in out]

    def save_pdf(self, path: str) -> None:
        if not self._pages:
            return
        for i, page in enumerate(self._pages):
            width_pt = page.width_mm * PT_PER_MM
            height_pt = page.height_mm * PT_PER_MM
            if i == 0:
                surface = cairo.PDFSurface(path, width_pt, height_pt)
                ctx = cairo.Context(surface)
            else:
                surface.set_size(width_pt, height_pt)
                surface.show_page()
                ctx = cairo.Context(surface)
            ctx.save()
            ctx.scale(PT_PER_MM, PT_PER_MM)
            ctx.set_source_rgb(1, 1, 1)
            ctx.rectangle(0, 0, page.width_mm, page.height_mm)
            ctx.fill()
            for item in page.items:
                if isinstance(item, Line):
                    self._draw_line(ctx, item)
                elif isinstance(item, Rect):
                    self._draw_rect(ctx, item)
                elif isinstance(item, Oval):
                    self._draw_oval(ctx, item)
                elif isinstance(item, Polyline):
                    self._draw_polyline(ctx, item)
                elif isinstance(item, Text):
                    self._draw_text(ctx, item)
            ctx.restore()
        surface.show_page()
        surface.finish()

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

    def _draw_line(self, ctx: cairo.Context, line: Line):
        self._apply_stroke(ctx, line.stroke)
        ctx.move_to(line.x1_mm, line.y1_mm)
        ctx.line_to(line.x2_mm, line.y2_mm)
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

    def _draw_oval(self, ctx: cairo.Context, o: Oval):
        cx = o.x_mm + o.w_mm / 2.0
        cy = o.y_mm + o.h_mm / 2.0
        rx = max(0.0, o.w_mm / 2.0)
        ry = max(0.0, o.h_mm / 2.0)
        ctx.save()
        ctx.translate(cx, cy)
        if rx > 0 and ry > 0:
            ctx.scale(rx, ry)
            ctx.new_path()
            ctx.arc(0, 0, 1.0, 0, 2*3.1415926535)
            if o.fill:
                self._apply_fill(ctx, o.fill)
            if o.stroke:
                self._apply_stroke(ctx, o.stroke)
                ctx.stroke()
            else:
                ctx.new_path()
            ctx.restore()
        else:
            ctx.restore()

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
        # Cairo toy text: good for simple Latin text; for complex scripts use PangoCairo later.
        slant = cairo.FONT_SLANT_ITALIC if t.italic else cairo.FONT_SLANT_NORMAL
        weight = cairo.FONT_WEIGHT_BOLD if t.bold else cairo.FONT_WEIGHT_NORMAL
        ctx.select_font_face(t.family, slant, weight)
        # We are in mm user units; convert pt size to mm
        ctx.set_font_size(t.size_pt * PT_PER_MM)
        ctx.set_source_rgba(*t.color)
        # Text position uses baseline at (x_mm, y_mm)
        ctx.move_to(t.x_mm, t.y_mm)
        ctx.show_text(t.text)

    def _compute_text_hit_rect_mm(self, x_mm: float, y_mm: float, text: str,
                                  family: str, size_pt: float,
                                  italic: bool, bold: bool) -> Tuple[float, float, float, float]:
        # Use a scratch surface to get text extents; compute in mm using pt→mm conversion.
        surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, 1, 1)
        ctx = cairo.Context(surf)
        slant = cairo.FONT_SLANT_ITALIC if italic else cairo.FONT_SLANT_NORMAL
        weight = cairo.FONT_WEIGHT_BOLD if bold else cairo.FONT_WEIGHT_NORMAL
        ctx.select_font_face(family, slant, weight)
        ctx.set_font_size(size_pt)  # extents in 'user units'; here treat as points
        te = ctx.text_extents(text)
        # Convert extents from points to mm
        x_bearing_mm = te.x_bearing / PT_PER_MM
        y_bearing_mm = te.y_bearing / PT_PER_MM
        width_mm = te.width / PT_PER_MM
        height_mm = te.height / PT_PER_MM
        # Baseline at (x_mm, y_mm); top-left = (x_mm + x_bearing_mm, y_mm + y_bearing_mm)
        rect_x = x_mm + x_bearing_mm
        rect_y = y_mm + y_bearing_mm
        return (rect_x, rect_y, width_mm, height_mm)
