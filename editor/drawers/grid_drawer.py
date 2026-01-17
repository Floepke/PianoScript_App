'''
Grid and barline drawing mixin for the Editor class.

Handles drawing barlines, measure numbers, and gridlines.
'''

from ui.widgets.draw_util import DrawUtil


class GridDrawerMixin:
    
    def draw_grid(self, du: DrawUtil) -> None:
        sc = None
        if hasattr(self, 'current_score'):
            sc = self.current_score()
        if sc is None:
            # Fallback: draw a debug grid so you can see scrolling behavior
            self._draw_debug_grid(du)
            return

        # Page metrics (mm)
        w_mm, h_mm = du.current_page_size_mm()
        margin = float(self.margin)
        x_left = margin
        x_right = max(0.0, w_mm - margin)
        y_top = margin
        y_bottom = max(y_top, margin + h_mm - 2.0 * margin)

        # Editor zoom controls vertical mm per quarter note
        zoom_mm_per_quarter = float(getattr(getattr(sc, 'editor', None), 'zoom_mm_per_quarter', 5.0) or 5.0)

        # Base grid: use the first section for this quick test
        bg_list = getattr(sc, 'base_grid', []) or []
        if not bg_list:
            self._draw_debug_grid(du)
            return
        bg = bg_list[0]
        numerator = int(getattr(bg, 'numerator', 4) or 4)
        denominator = int(getattr(bg, 'denominator', 4) or 4)
        measure_amount = int(getattr(bg, 'measure_amount', 1) or 1)

        # General formula: quarters per measure = numerator * (4/denominator)
        quarters_per_measure = float(numerator) * (4.0 / max(1.0, float(denominator)))
        measure_len_mm = quarters_per_measure * zoom_mm_per_quarter

        # Draw horizontal barlines across the stave width for each measure boundary
        color = getattr(self, 'notation_color', (0.0, 0.0, 0.0, 1.0))
        bar_width_mm = max(0.15, measure_len_mm / 200.0)  # modest thickness, scales gently with zoom

        # Include an initial barline at y_top
        du.add_line(x_left, y_top, x_right, y_top, color=color, width_mm=bar_width_mm, id=0, tags=["barline"])

        # Subsequent barlines spaced by measure_len_mm
        # Stop once past y_bottom to avoid redundant off-screen items
        # Note: page height is already computed from base_grid in the editor view.
        for i in range(1, measure_amount + 1):
            y = y_top + i * measure_len_mm
            if y > y_bottom + 1e-6:
                break
            du.add_line(x_left, y, x_right, y, color=color, width_mm=bar_width_mm, id=0, tags=["barline"])

    def _draw_debug_grid(self, du: DrawUtil) -> None:
        # Simple fallback: horizontal lines every 10mm with lighter color
        w_mm, h_mm = du.current_page_size_mm()
        margin = float(self.margin)
        x_left = margin
        x_right = max(0.0, w_mm - margin)
        y_top = margin
        y_bottom = max(y_top, margin + h_mm - 2.0 * margin)
        color = (0.2, 0.2, 0.25, 0.8)
        step_mm = 10.0
        width_mm = 0.15
        i = 0
        while True:
            y = y_top + i * step_mm
            if y > y_bottom:
                break
            du.add_line(x_left, y, x_right, y, color=color, width_mm=width_mm, id=0, tags=["grid_line"])
            i += 1
