from PySide6.QtGui import QPainter
from PySide6.QtPrintSupport import QPrinter
from imports.engraver.engraver import render
# import QMarginsF
from PySide6.QtCore import QMarginsF

def printer(io):
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
    render(io, pageno=0, render_type='pdf')
    io['gui'].print_scene.render(painter)
    printer.newPage()
    render(io, pageno=1, render_type='pdf')
    io['gui'].print_scene.render(painter)

    # End the painter
    painter.end()