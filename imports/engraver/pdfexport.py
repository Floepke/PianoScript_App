from PySide6.QtGui import QPainter
from PySide6.QtPrintSupport import QPrinter
from imports.engraver.engraver import pre_render, render
# import QMarginsF
from PySide6.QtCore import QMarginsF

def pdf_export(io):
    # Create a QPrinter object
    printer = QPrinter(QPrinter.HighResolution)
    printer.setOutputFormat(QPrinter.PdfFormat)
    printer.setOutputFileName("page.pdf")
    printer.setPageMargins(QMarginsF(0, 0, 0, 0))

    # Create a QPainter object
    painter = QPainter()

    # Start the painter with the printer
    painter.begin(printer)

    # Render the scene to the printer
    for page in range(io['total_pages']):
        io['selected_page'] = page
        if page > 0:printer.newPage()
        DOC, leftover_page_space, staff_dimensions, staff_ranges, pageno, linebreaks, draw_scale = pre_render(io, render_type='pdf')
        render(io, DOC, leftover_page_space, staff_dimensions, staff_ranges, pageno, linebreaks, draw_scale)
        io['gui'].print_scene.render(painter)

    # End the painter
    painter.end()