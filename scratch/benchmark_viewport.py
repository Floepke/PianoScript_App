from __future__ import annotations
import time
from typing import Tuple
from PySide6 import QtGui, QtWidgets
import sys, os
# Ensure project root is importable when running from scratch/
ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from ui.widgets.draw_util import DrawUtil
from ui.widgets.renderer import CairoRenderer, QPainterRenderer

# Synthetic workload: grid lines + staff rectangles + notes + beams + text across a tall page.

def build_workload(page_w_mm: float, page_h_mm: float, density: int = 2000) -> DrawUtil:
    du = DrawUtil()
    du.set_current_page_size_mm(page_w_mm, page_h_mm)
    # Grid background stripes
    stripe_h_mm = 5.0
    y = 0.0
    toggle = False
    while y < page_h_mm:
        color = (0.20, 0.20, 0.20, 1.0) if toggle else (0.18, 0.18, 0.18, 1.0)
        du.add_rectangle(0.0, y, page_w_mm, min(stripe_h_mm, page_h_mm - y),
                         stroke_color=None, fill_color=color, tags=['grid'], hit_rect_mm=(0.0, y, page_w_mm, stripe_h_mm))
        toggle = not toggle
        y += stripe_h_mm
    # Staff lines: 5 lines per system, every 20mm
    line_color = (0.8, 0.8, 0.8, 1.0)
    for sys_idx in range(int(page_h_mm // 20.0)):
        base_y = sys_idx * 20.0 + 5.0
        for i in range(5):
            du.add_line(10.0, base_y + i * 1.5, page_w_mm - 10.0, base_y + i * 1.5,
                        color=line_color, width_mm=0.2, tags=['stave'])
    # Notes: small ovals randomly spread
    import random
    random.seed(42)
    for _ in range(density):
        nx = random.uniform(15.0, page_w_mm - 15.0)
        ny = random.uniform(10.0, page_h_mm - 10.0)
        du.add_oval(nx - 1.5, ny - 1.5, 3.0, 3.0, stroke_color=(0,0,0,1), stroke_width_mm=0.2,
                    fill_color=(0,0,0,1), tags=['note'])
    # Beams: short polylines
    for _ in range(density // 10):
        bx = random.uniform(20.0, page_w_mm - 20.0)
        by = random.uniform(20.0, page_h_mm - 20.0)
        du.add_polyline([(bx, by), (bx+5.0, by)], stroke_color=(0,0,0,1), stroke_width_mm=0.3, tags=['beam'])
    # Text: measure numbers
    for sys_idx in range(int(page_h_mm // 50.0)):
        y = sys_idx * 50.0 + 2.0
        du.add_text(2.0, y, f"Sys {sys_idx}", family="Sans", size_pt=8, color=(1,1,1,1), tags=['text'])
    return du


def bench(renderer_name: str, render_func, du: DrawUtil, px_per_mm: float,
          viewport_px: Tuple[int,int], clip_mm: Tuple[float,float,float,float], dpr: float,
          frames: int = 50) -> float:
    # Warm-up
    img = render_func(du, du.current_page_index(), px_per_mm, clip_mm, viewport_px[0], viewport_px[1], dpr)
    QtWidgets.QApplication.processEvents()
    t0 = time.perf_counter()
    y = clip_mm[1]
    h_mm = clip_mm[3]
    step_mm = h_mm * 0.2
    for i in range(frames):
        clip = (clip_mm[0], y, clip_mm[2], clip_mm[3])
        img = render_func(du, du.current_page_index(), px_per_mm, clip, viewport_px[0], viewport_px[1], dpr)
        y += step_mm
        if y + h_mm > du.current_page_size_mm()[1]:
            y = 0.0
    t1 = time.perf_counter()
    dt = t1 - t0
    print(f"{renderer_name}: {frames} frames in {dt:.3f}s ({frames/dt:.1f} fps)")
    return dt


def main():
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    page_w_mm = 210.0
    page_h_mm = 2000.0  # tall content
    du = DrawUtil()
    du.new_page(page_w_mm, page_h_mm)
    du = build_workload(page_w_mm, page_h_mm, density=3000)
    du.set_current_page_size_mm(page_w_mm, page_h_mm)

    # Viewport settings
    vp_w = 800
    vp_h = 600
    dpr = 1.0
    px_per_mm = vp_w / page_w_mm
    clip_mm = (0.0, 0.0, page_w_mm, vp_h / px_per_mm)

    cairo_r = CairoRenderer()
    qp_r = QPainterRenderer()

    print("Benchmarking viewport rasterization…")
    bench("Cairo", cairo_r.render_viewport, du, px_per_mm, (vp_w, vp_h), clip_mm, dpr, frames=80)
    bench("QPainter", qp_r.render_viewport, du, px_per_mm, (vp_w, vp_h), clip_mm, dpr, frames=80)

    print("Done.")


if __name__ == "__main__":
    main()
