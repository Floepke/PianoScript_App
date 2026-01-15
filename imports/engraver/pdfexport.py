from PySide6.QtGui import QPainter, QPageLayout, QPageSize
from PySide6.QtWidgets import QFileDialog, QProgressDialog
from PySide6.QtGui import QPainter
from PySide6.QtPrintSupport import QPrinter
from PySide6.QtCore import QMarginsF, QSizeF, Qt, QCoreApplication
from imports.engraver.engraver import pre_render, render

def pdf_export(io):

    file_dialog = QFileDialog()
    # set default prefilled filename
    default_filename = io['score']['header']['title']
    file_dialog.selectFile(default_filename)

    file_dialog.setAcceptMode(QFileDialog.AcceptSave)
    file_dialog.setDefaultSuffix("pdf")
    file_dialog.setNameFilter("PDF Files (*.pdf)")

    file_path, _ = file_dialog.getSaveFileName(
        None,
        "Export PDF",
        io['score']['header']['title'] + '.pdf',
        "PDF Files (*.pdf)"
    )
    if file_path:
        # Ensure the file path ends with .pdf
        if not file_path.lower().endswith('.pdf'):
            file_path += '.pdf'
        
        # Create progress dialog
        total_pages = io['total_pages']
        progress = QProgressDialog("Preparing PDF export...", "Cancel", 0, total_pages, None)
        progress.setWindowModality(Qt.WindowModal)
        progress.setWindowTitle("Exporting PDF")
        progress.setMinimumDuration(0)  # Show immediately
        progress.show()
        QCoreApplication.processEvents()  # Force UI update
        
        # Create a QPrinter object
        printer = QPrinter(QPrinter.HighResolution)
        printer.setOutputFormat(QPrinter.PdfFormat)
        
        # Set the output file name
        printer.setOutputFileName(file_path)

        # Set the paper size
        paper_width = io['score']['properties']['page_width']
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
        for page in range(total_pages):
            # Check if user cancelled
            if progress.wasCanceled():
                break
                
            # Update progress
            progress.setValue(page)
            progress.setLabelText(f"Rendering page {page + 1} of {total_pages}...")
            QCoreApplication.processEvents()  # Force UI update
            
            io['selected_page'] = page
            if page > 0:
                printer.newPage()
            DOC, leftover_page_space, staff_dimensions, staff_ranges, pageno, linebreaks, draw_scale, barline_times, render_type = pre_render(
                io, render_type='pdf')
            render(io, DOC, leftover_page_space, staff_dimensions,
                   staff_ranges, pageno, linebreaks, draw_scale, barline_times, render_type)
            io['gui'].print_scene.render(painter)

        # Complete progress
        progress.setValue(total_pages)
        progress.close()

        # End the painter
        painter.end()