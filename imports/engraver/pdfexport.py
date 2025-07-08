from PySide6.QtGui import QPainter, QPageLayout, QPageSize
from PySide6.QtWidgets import QFileDialog
from PySide6.QtGui import QPainter
from PySide6.QtPrintSupport import QPrinter
from PySide6.QtCore import QMarginsF, QSizeF
from imports.engraver.engraver import pre_render, render


# def pdf_export(io):
#     # Create a QPrinter object
#     printer = QPrinter(QPrinter.HighResolution)
#     printer.setOutputFormat(QPrinter.PdfFormat)
#     printer.setOutputFileName("page.pdf")
#     printer.setPageMargins(QMarginsF(0, 0, 0, 0))

#     # Set the paper size
#     # width in millimeters for A4 paper
#     paper_width = io['score']['properties']['page_width']
#     # height in millimeters for A4 paper
#     paper_height = io['score']['properties']['page_height']
#     printer.setPageSize(
#         QPageSize(QSizeF(paper_width, paper_height), QPageSize.Millimeter))

#     # Create a QPainter object
#     painter = QPainter()

#     # Start the painter with the printer
#     painter.begin(printer)

#     # Render the scene to the printer
#     for page in range(io['total_pages']):
#         io['selected_page'] = page
#         if page > 0:
#             printer.newPage()
#         DOC, leftover_page_space, staff_dimensions, staff_ranges, pageno, linebreaks, draw_scale, render_type = pre_render(
#             io, render_type='pdf')
#         render(io, DOC, leftover_page_space, staff_dimensions,
#                staff_ranges, pageno, linebreaks, draw_scale, render_type)
#         io['gui'].print_scene.render(painter)

#     # End the painter
#     painter.end()


# def pdf_export(io):
#     # Create a QPrinter object
#     printer = QPrinter(QPrinter.HighResolution)
#     printer.setOutputFormat(QPrinter.PdfFormat)
#     printer.setOutputFileName("page.pdf")
#     printer.setPageMargins(QMarginsF(0, 0, 0, 0))

#     # Set the paper size
#     # width in millimeters for A4 paper
#     paper_width = io['score']['properties']['page_width']
#     # height in millimeters for A4 paper
#     paper_height = io['score']['properties']['page_height']
#     printer.setPageSize(QPrinter.setPageSize(
#         QSizeF(paper_width, paper_height)))

#     # Create a QPainter object
#     painter = QPainter()

#     # Start the painter with the printer
#     painter.begin(printer)

#     # Render the scene to the printer
#     for page in range(io['total_pages']):
#         io['selected_page'] = page
#         if page > 0:
#             printer.newPage()
#         DOC, leftover_page_space, staff_dimensions, staff_ranges, pageno, linebreaks, draw_scale = pre_render(
#             io, render_type='pdf')
#         render(io, DOC, leftover_page_space, staff_dimensions,
#                staff_ranges, pageno, linebreaks, draw_scale)
#         io['gui'].print_scene.render(painter)

#     # End the painter
#     painter.end()


def pdf_export(io):

    file_dialog = QFileDialog()
    file_dialog.setAcceptMode(QFileDialog.AcceptSave)
    file_dialog.setDefaultSuffix("pdf")
    file_dialog.setNameFilter("PDF Files (*.pdf)")
    file_path, _ = file_dialog.getSaveFileName(
        None,
        "Export PDF",
        "",
        "PDF Files (*.pdf)"
    )
    if file_path:
        # Ensure the file path ends with .pdf
        if not file_path.lower().endswith('.pdf'):
            file_path += '.pdf'
        # Create a QPrinter object
        printer = QPrinter(QPrinter.HighResolution)
        printer.setOutputFormat(QPrinter.PdfFormat)
        
        # Set the output file name
        printer.setOutputFileName(file_path)

        # Set the paper size
        # width in millimeters for A4 paper
        paper_width = io['score']['properties']['page_width']
        # height in millimeters for A4 paper
        paper_height = io['score']['properties']['page_height']
        page_size = QPageSize(
            QSizeF(paper_width, paper_height), QPageSize.Millimeter)
        page_layout = QPageLayout(
            page_size, QPageLayout.Portrait, QMarginsF(0, 0, 0, 0))
        printer.setPageLayout(page_layout)

        # Create a QPainter object
        painter = QPainter()

        # Start the painter with the printer
        painter.begin(printer)

        # Render the scene to the printer
        for page in range(io['total_pages']):
            io['selected_page'] = page
            if page > 0:
                printer.newPage()
            DOC, leftover_page_space, staff_dimensions, staff_ranges, pageno, linebreaks, draw_scale, barline_times, render_type = pre_render(
                io, render_type='pdf')
            render(io, DOC, leftover_page_space, staff_dimensions,
                   staff_ranges, pageno, linebreaks, draw_scale, barline_times, render_type)
            io['gui'].print_scene.render(painter)

        # End the painter
        painter.end()
