import os, sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from ui.widgets.draw_util import DrawUtil


def main():
    du = DrawUtil()
    du.new_page(210.0, 297.0)
    du.add_line(10.0, 10.0, 200.0, 10.0, width_mm=0.3, id=1, tags=["top"])
    du.add_rectangle(20.0, 20.0, 40.0, 30.0, stroke_color=(0,0,0,1), fill_color=(0.2,0.6,0.9,0.3), id=2)
    du.add_text(25.0, 35.0, "Hello DrawUtil", family="Sans", size_pt=12.0, id=3)
    out_path = "scratch/out.pdf"
    du.save_pdf(out_path)
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
