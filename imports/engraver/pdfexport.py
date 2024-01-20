from PySide6.QtGui import QPainter
from PySide6.QtPrintSupport import QPrinter
from imports.engraver.engraver import render

def printer(io):
    # Create a QPrinter object
    printer = QPrinter(QPrinter.HighResolution)
    printer.setOutputFormat(QPrinter.PdfFormat)
    printer.setOutputFileName("page.pdf")

    # Create a QPainter object
    painter = QPainter()

    # Start the painter with the printer
    painter.begin(printer)

    # Render the scene to the printer
    render(io)
    io['gui'].print_scene.render(painter)

    # End the painter
    painter.end()