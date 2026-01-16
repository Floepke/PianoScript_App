from PySide6 import QtCore, QtGui, QtWidgets
from file_model.SCORE import SCORE
from file_model.file_manager import FileManager
from ui.widgets.toolbar_splitter import ToolbarSplitter
from ui.widgets.cairo_views import CairoEditorWidget
from ui.widgets.tool_selector import ToolSelectorDock
from ui.widgets.snap_size_selector import SnapSizeDock
from ui.widgets.draw_util import DrawUtil
from ui.widgets.draw_view import DrawUtilView
from settings_manager import open_preferences, get_preferences
from engraver.engraver import Engraver
from editor.tool_manager import ToolManager
from editor.editor import Editor


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Pianoscript - (unsaved)")
        self.resize(1200, 800)

        # File management
        self.file_manager = FileManager(self)
        # Install error-backup hook early so any unhandled exception triggers a backup
        self.file_manager.install_error_backup_hook()

        self._create_menus()

        splitter = ToolbarSplitter(QtCore.Qt.Orientation.Horizontal)
        # Hide handle indicator/grip but keep dragging functional
        splitter.setStyleSheet(
            "QSplitter::handle { background: transparent; image: none; }\n"
            "QSplitter::handle:hover { background: transparent; }"
        )
        self.editor = CairoEditorWidget()

        self.du = DrawUtil()
        self.du.new_page(width_mm=210, height_mm=297)

        self.print_view = DrawUtilView(self.du)
        # Engraver instance (single)
        self.engraver = Engraver(self.du, self)
        # When engraving completes, re-render the print view
        self.engraver.engraved.connect(self.print_view.request_render)
        # Provide initial score to engrave
        self._refresh_views_from_score()

        splitter.addWidget(self.editor)
        splitter.addWidget(self.print_view)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)
        self.setCentralWidget(splitter)
        # Hide dock sizer handles and prevent resize cursor changes (docks are fixed-size)
        self.setStyleSheet(
            "QMainWindow::separator { width: 0px; height: 0px; background: transparent; }\n"
            "QMainWindow::separator:hover { background: transparent; }"
        )
        # Place Snap Size dock above the Tool Selector dock on the left
        self.snap_dock = SnapSizeDock(self)
        self.addDockWidget(QtCore.Qt.DockWidgetArea.LeftDockWidgetArea, self.snap_dock)
        self.tool_dock = ToolSelectorDock(self)
        self.addDockWidget(QtCore.Qt.DockWidgetArea.LeftDockWidgetArea, self.tool_dock)
        # Stack vertically: snap (top) above tool selector (bottom)
        self.splitDockWidget(self.snap_dock, self.tool_dock, QtCore.Qt.Orientation.Vertical)
        # Wiring
        # Editor + ToolManager
        self.tool_manager = ToolManager(splitter)
        self.editor_controller = Editor(self.tool_manager)
        self.editor.set_editor(self.editor_controller)
        # Provide FileManager to editor (for undo snapshots)
        self.editor_controller.set_file_manager(self.file_manager)
        # Wire tool selector to Editor controller and set default tool
        self.tool_dock.selector.toolSelected.connect(self.editor_controller.set_tool_by_name)
        self.editor_controller.set_tool_by_name('note')
        self.snap_dock.selector.snapChanged.connect(self._on_snap_changed)
        # 'Fit' button on splitter handle triggers fit action
        splitter.fitRequested.connect(self._fit_print_view_to_page)
        # Default toolbar actions
        splitter.nextRequested.connect(self._next_page)
        splitter.previousRequested.connect(self._previous_page)
        splitter.engraveRequested.connect(self._engrave_now)
        splitter.playRequested.connect(self._play_midi)
        splitter.stopRequested.connect(self._stop_midi)
        # Fit print view to page on startup
        QtCore.QTimer.singleShot(0, self._fit_print_view_to_page)
        # Also request an initial render
        QtCore.QTimer.singleShot(0, self.print_view.request_render)
        # Strip demo timers
        # Center the window on the primary screen shortly after show
        QtCore.QTimer.singleShot(0, self._center_on_primary)

        # After docks are visible, adjust their sizes to fit
        QtCore.QTimer.singleShot(0, self._adjust_docks_to_fit)

        # Page navigation state
        self._page_counter = 0
        self._total_pages_placeholder = 4  # TODO: replace with real page count

    def _create_menus(self) -> None:
        menubar = self.menuBar()

        file_menu = menubar.addMenu("&File")
        edit_menu = menubar.addMenu("&Edit")
        view_menu = menubar.addMenu("&View")

        new_act = QtGui.QAction("New", self)
        open_act = QtGui.QAction("Open…", self)
        save_act = QtGui.QAction("Save", self)
        save_as_act = QtGui.QAction("Save As…", self)
        exit_act = QtGui.QAction("Exit", self)
        exit_act.triggered.connect(self.close)

        file_menu.addAction(new_act)
        file_menu.addAction(open_act)
        file_menu.addAction(save_act)
        file_menu.addAction(save_as_act)
        file_menu.addSeparator()

        export_pdf_act = QtGui.QAction("Export PDF…", self)
        export_pdf_act.triggered.connect(self._export_pdf)
        file_menu.addAction(export_pdf_act)

        file_menu.addSeparator()
        file_menu.addAction(exit_act)

        undo_act = QtGui.QAction("Undo", self)
        undo_act.setShortcut(QtGui.QKeySequence.StandardKey.Undo)
        redo_act = QtGui.QAction("Redo", self)
        redo_act.setShortcut(QtGui.QKeySequence.StandardKey.Redo)
        edit_menu.addAction(undo_act)
        edit_menu.addAction(redo_act)
        prefs_act = QtGui.QAction("Preferences…", self)
        prefs_act.triggered.connect(self._open_preferences)
        edit_menu.addAction(prefs_act)

        view_menu.addAction(QtGui.QAction("Zoom In", self))
        view_menu.addAction(QtGui.QAction("Zoom Out", self))

        # Wire up file actions
        new_act.triggered.connect(self._file_new)
        open_act.triggered.connect(self._file_open)
        save_act.triggered.connect(self._file_save)
        save_as_act.triggered.connect(self._file_save_as)
        # Wire up edit actions
        undo_act.triggered.connect(self._edit_undo)
        redo_act.triggered.connect(self._edit_redo)

    def _export_pdf(self) -> None:
        dlg = QtWidgets.QFileDialog(self)
        dlg.setAcceptMode(QtWidgets.QFileDialog.AcceptMode.AcceptSave)
        dlg.setNameFilter("PDF Files (*.pdf)")
        dlg.setDefaultSuffix("pdf")
        if dlg.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            out_path = dlg.selectedFiles()[0]
            try:
                self.du.save_pdf(out_path)
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, "Export PDF failed", str(e))

    def _open_preferences(self) -> None:
        # Ensure preferences file exists and open in system editor
        open_preferences()

    def _file_new(self) -> None:
        self.file_manager.new()
        self._refresh_views_from_score()
        self._update_title()

    def _file_open(self) -> None:
        sc = self.file_manager.open()
        if sc:
            self._refresh_views_from_score()
            self._update_title()

    def _file_save(self) -> None:
        if self.file_manager.save():
            self._update_title()

    def _file_save_as(self) -> None:
        if self.file_manager.save_as():
            self._update_title()

    def _refresh_views_from_score(self) -> None:
        try:
            sc_dict = self.file_manager.current().get_dict()
        except Exception:
            sc_dict = {}
        self.print_view.set_score(sc_dict)
        # Request engraving via Engraver; render happens on engraved signal
        try:
            self.engraver.engrave(sc_dict)
        except Exception:
            # Fallback: render current content
            self.print_view.request_render()
        # Also refresh the editor view
        self.editor.update()

    def _edit_undo(self) -> None:
        self.editor_controller.undo()
        self._refresh_views_from_score()

    def _edit_redo(self) -> None:
        self.editor_controller.redo()
        self._refresh_views_from_score()

    def _update_title(self) -> None:
        p = self.file_manager.path()
        if p:
            self.setWindowTitle(f"Pianoscript - {str(p)}")
        else:
            self.setWindowTitle("Pianoscript - new project (unsaved)")

    def _page_dimensions_mm(self) -> tuple[float, float]:
        try:
            sc = self.file_manager.current()
            lay = getattr(sc, 'layout', None)
            if lay:
                return float(lay.page_width_mm), float(lay.page_height_mm)
        except Exception:
            pass
        # Fallback to DrawUtil current page size
        try:
            return self.du.current_page_size_mm()
        except Exception:
            return (210.0, 297.0)

    def _fit_print_view_to_page(self) -> None:
        try:
            w_mm, h_mm = self._page_dimensions_mm()
            if w_mm <= 0 or h_mm <= 0:
                return
            splitter = self.centralWidget()
            # Use content width excluding handle to avoid undersizing the print view
            handle_w = 0
            try:
                handle_w = int(splitter.handleWidth())
            except Exception:
                handle_w = 0
            total_w = max(0, splitter.width() - handle_w)
            pv_h = self.print_view.height()
            # Ideal width to fit page exactly by height when scaling by width
            ideal_pv_w = int(round(pv_h * (w_mm / h_mm)))
            editor_w = max(0, total_w - ideal_pv_w)
            splitter.setSizes([editor_w, ideal_pv_w])
            QtCore.QTimer.singleShot(0, self.print_view.request_render)
        except Exception:
            pass

    def _current_score_dict(self) -> dict:
        try:
            return self.file_manager.current().get_dict()
        except Exception:
            return {}

    def _set_page_index(self, index: int) -> None:
        try:
            self.print_view.set_page(index)
        except Exception:
            pass

    def _next_page(self) -> None:
        try:
            self._page_counter += 1
            pageno = self._page_counter % max(1, self._total_pages_placeholder)
            self._set_page_index(pageno)
            self.engraver.engrave(self._current_score_dict())
        except Exception:
            pass

    def _previous_page(self) -> None:
        try:
            self._page_counter -= 1
            pageno = self._page_counter % max(1, self._total_pages_placeholder)
            self._set_page_index(pageno)
            self.engraver.engrave(self._current_score_dict())
        except Exception:
            pass

    def _engrave_now(self) -> None:
        try:
            self.engraver.engrave(self._current_score_dict())
        except Exception:
            pass

    def _play_midi(self) -> None:
        try:
            if not hasattr(self, 'player') or self.player is None:
                from midi.player import Player
                self.player = Player()
            self.player.start()
        except Exception:
            pass

    def _stop_midi(self) -> None:
        try:
            if hasattr(self, 'player') and self.player is not None:
                self.player.stop()
        except Exception:
            pass

    def _adjust_docks_to_fit(self) -> None:
        # Ensure both docks are sized and locked to their fit dimensions
        try:
            if hasattr(self.snap_dock, 'selector'):
                self.snap_dock.selector.adjust_to_fit()
        except Exception:
            pass
        try:
            self.tool_dock.adjust_to_fit()
        except Exception:
            pass

    def resizeEvent(self, ev: QtGui.QResizeEvent) -> None:
        super().resizeEvent(ev)
        # Always refit print view on main window resize
        try:
            self._fit_print_view_to_page()
        except Exception:
            pass

    def _on_snap_changed(self, base: int, divide: int) -> None:
        # Placeholder: integrate with editor snapping later.
        # For now, print to console to verify wiring.
        try:
            print(f"Snap changed: base={base} divide={divide}")
        except Exception:
            pass

    def _demo_add_rect(self) -> None:
        # Removed test drawing logic
        pass

    def _center_on_primary(self) -> None:
        # Move window to the center of the primary screen
        try:
            scr = QtGui.QGuiApplication.primaryScreen()
            if not scr:
                return
            avail = scr.availableGeometry()
            if not avail.isValid():
                return
            fg = self.frameGeometry()
            fg.moveCenter(avail.center())
            self.move(fg.topLeft())
        except Exception:
            pass

    def keyPressEvent(self, ev: QtGui.QKeyEvent) -> None:
        if ev.key() == QtCore.Qt.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(ev)

    def prepare_close(self) -> None:
        # Ensure worker threads are stopped before application exits
        if hasattr(self, "print_view") and self.print_view is not None:
            try:
                self.print_view.shutdown()
            except Exception:
                pass

    def closeEvent(self, ev: QtGui.QCloseEvent) -> None:
        self.prepare_close()
        super().closeEvent(ev)
