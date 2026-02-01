from PySide6 import QtCore, QtGui, QtWidgets
from typing import Optional
import sys
from datetime import datetime
from file_model.SCORE import SCORE
from file_model.file_manager import FileManager
from ui.widgets.toolbar_splitter import ToolbarSplitter
from ui.widgets.cairo_views import CairoEditorWidget
from ui.widgets.tool_selector import ToolSelectorDock
from ui.widgets.snap_size_selector import SnapSizeDock
from ui.widgets.draw_util import DrawUtil
from ui.widgets.draw_view import DrawUtilView
from settings_manager import open_preferences, get_preferences
from appdata_manager import get_appdata_manager
from engraver.engraver import Engraver
from editor.tool_manager import ToolManager
from editor.editor import Editor


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("keyTAB - new project (unsaved)")
        self.resize(1200, 800)

        # File management
        self.file_manager = FileManager(self)
        
        # Install error-backup hook early so any unhandled exception triggers a backup
        self.file_manager.install_error_backup_hook()

        self._create_menus()

        self.splitter = ToolbarSplitter(QtCore.Qt.Orientation.Horizontal)
        # Hide handle indicator/grip but keep dragging functional
        self.splitter.setStyleSheet(
            "QSplitter::handle { background: transparent; image: none; }\n"
            "QSplitter::handle:hover { background: transparent; }"
        )
        
        # Editor view with external scrollbar for static viewport scrolling
        self.editor_canvas = CairoEditorWidget()
        self.editor_vscroll = QtWidgets.QScrollBar(QtCore.Qt.Orientation.Vertical)
        
        # For external code, expose the canvas under the same name
        self.editor = self.editor_canvas

        self.du = DrawUtil()
        self.du.new_page(width_mm=210, height_mm=297)

        self.print_view = DrawUtilView(self.du)
        
        # Engraver instance (single)
        self.engraver = Engraver(self.du, self)
        
        # When engraving completes, re-render the print view
        self.engraver.engraved.connect(self.print_view.request_render)
        
        # Startup restore: prefer opening the last saved project; else restore unsaved session; else new
        try:
            adm2 = get_appdata_manager()
            was_saved = bool(adm2.get("last_session_saved", False))
            saved_path = str(adm2.get("last_session_path", "") or "")
        except Exception:
            was_saved = False
            saved_path = ""
        opened = False
        status_msg = ""
        if was_saved and saved_path:
            try:
                from pathlib import Path as _Path
                if _Path(saved_path).exists():
                    self.file_manager.open_path(saved_path)
                    opened = True
                    status_msg = f"Opened last saved project: {saved_path}"
            except Exception:
                opened = False
        if not opened:
            # If the last session wasn't saved, try restoring the session snapshot
            restored = False
            try:
                restored = self.file_manager.load_session_if_available()
            except Exception:
                restored = False
            if not restored:
                # Fallback to last explicitly opened/saved project if available
                try:
                    last_path = str(adm2.get("last_opened_file", "") or "")
                except Exception:
                    last_path = ""
                if last_path:
                    try:
                        from pathlib import Path as _Path
                        if _Path(last_path).exists():
                            self.file_manager.open_path(last_path)
                            status_msg = f"Opened last project: {last_path}"
                        else:
                            self.file_manager.new()
                            status_msg = "Started new project"
                    except Exception:
                        self.file_manager.new()
                        status_msg = "Started new project"
                else:
                    # Nothing to restore; start fresh
                    self.file_manager.new()
                    status_msg = "Started new project"
            else:
                status_msg = "Restored unsaved session"

        # Provide initial score to engrave and update titlebar
        self._refresh_views_from_score()
        # Show startup status on the status bar
        try:
            if status_msg:
                self._status(status_msg, 5000)
        except Exception:
            pass

        self._update_title()

        # Build a container with the canvas and external vertical scrollbar
        editor_container = QtWidgets.QWidget()
        editor_layout = QtWidgets.QHBoxLayout(editor_container)
        editor_layout.setContentsMargins(0, 0, 0, 0)
        editor_layout.setSpacing(0)
        editor_layout.addWidget(self.editor_canvas, stretch=1)
        editor_layout.addWidget(self.editor_vscroll, stretch=0)
        self.splitter.addWidget(editor_container)
        self.splitter.addWidget(self.print_view)
        self.splitter.setStretchFactor(0, 3)
        self.splitter.setStretchFactor(1, 2)
        self.setCentralWidget(self.splitter)
        # Status bar for lightweight app messages
        try:
            self._statusbar = QtWidgets.QStatusBar(self)
            self.setStatusBar(self._statusbar)
        except Exception:
            self._statusbar = None
        # Ensure the editor is the main focus target
        try:
            self.setFocusPolicy(QtCore.Qt.FocusPolicy.StrongFocus)
            self.setFocusProxy(self.editor_canvas)
            self.editor_canvas.setFocus()
        except Exception:
            pass
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
        # Avoid docks stealing focus from the editor
        try:
            self.snap_dock.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)
            self.tool_dock.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)
            self.print_view.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)
            self.editor_vscroll.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)
        except Exception:
            pass
        # Wiring
        # Editor + ToolManager
        self.tool_manager = ToolManager(self.splitter)
        self.editor_controller = Editor(self.tool_manager)
        self.editor.set_editor(self.editor_controller)
        # Provide editor to ToolManager so tools can use editor wrappers
        try:
            self.tool_manager.set_editor(self.editor_controller)
        except Exception:
            pass
        # Provide FileManager to editor (for undo snapshots)
        self.editor_controller.set_file_manager(self.file_manager)
        # Wire tool selector to Editor controller
        self.tool_dock.selector.toolSelected.connect(self.editor_controller.set_tool_by_name)
        # Also persist tool selection to appdata
        try:
            self.tool_dock.selector.toolSelected.connect(self._on_tool_selected)
        except Exception:
            pass
        # Persist snap changes and update editor
        self.snap_dock.selector.snapChanged.connect(self._on_snap_changed)
        # Restore last tool and snap size from appdata; fallback to defaults
        try:
            adm_restore = get_appdata_manager()
            last_tool = str(adm_restore.get("selected_tool", "note") or "note")
            try:
                self.tool_dock.selector.set_selected_tool(last_tool, emit=True)
            except Exception:
                self.editor_controller.set_tool_by_name('note')
            sb = int(adm_restore.get("snap_base", 8) or 8)
            sd = int(adm_restore.get("snap_divide", 1) or 1)
            try:
                self.snap_dock.selector.set_snap(sb, sd, emit=True)
            except Exception:
                pass
        except Exception:
            # Fallback defaults
            try:
                self.editor_controller.set_tool_by_name('note')
            except Exception:
                pass
        # 'Fit' button on splitter handle triggers fit action
        self.splitter.fitRequested.connect(self._fit_print_view_to_page)
        self.splitter.fitRequested.connect(self._force_redraw)
        # Default toolbar actions
        self.splitter.nextRequested.connect(self._next_page)
        self.splitter.nextRequested.connect(self._force_redraw)
        self.splitter.previousRequested.connect(self._previous_page)
        self.splitter.previousRequested.connect(self._force_redraw)
        self.splitter.engraveRequested.connect(self._engrave_now)
        self.splitter.engraveRequested.connect(self._force_redraw)
        self.splitter.playRequested.connect(self._play_midi)
        self.splitter.playRequested.connect(self._force_redraw)
        self.splitter.stopRequested.connect(self._stop_midi)
        self.splitter.stopRequested.connect(self._force_redraw)
        # FX synth editor
        self.splitter.fxRequested.connect(self._open_fx_editor)
        # Contextual tool buttons should also force redraw
        self.splitter.contextButtonClicked.connect(lambda *_: self._force_redraw())
        # Restore splitter sizes from last session if available; else fall back to fit
        adm = get_appdata_manager()
        saved_sizes = adm.get("splitter_sizes", None)
        if isinstance(saved_sizes, list) and len(saved_sizes) == 2 and sum(int(v) for v in saved_sizes) > 0:
            # Apply after layout has settled
            QtCore.QTimer.singleShot(0, lambda: self.splitter.setSizes([int(saved_sizes[0]), int(saved_sizes[1])]))
            # Disable startup fit behavior
            self.is_startup = False
        else:
            # Fit print view to page on startup (schedule to catch late geometry)
            QtCore.QTimer.singleShot(200, self._fit_print_view_to_page)
        # Also request an initial render
        QtCore.QTimer.singleShot(0, self.print_view.request_render)
        # Strip demo timers
        # Center the window on the primary screen shortly after show
        QtCore.QTimer.singleShot(0, self._center_on_primary)

        # After docks are visible, adjust their sizes to fit
        QtCore.QTimer.singleShot(0, self._adjust_docks_to_fit)

        # Page navigation state
        self._page_counter = 0

        self._total_pages_placeholder = 2  # TODO: replace with real page count

        # Connect external scrollbar to the editor canvas
        try:
            self.editor.viewportMetricsChanged.connect(self._on_editor_metrics)
            self.editor_vscroll.valueChanged.connect(self._on_editor_scroll_changed)
            # Keep external scrollbar in sync with wheel-driven scroll from the editor
            self.editor.scrollLogicalPxChanged.connect(self.editor_vscroll.setValue)
        except Exception:
            pass

        # Fit state tracking
        self.is_fit = False

        self.is_startup = True

        # Initialize player (MIDI or Synth)
        try:
            from midi.player import Player
            self.player = Player()
        except Exception:
            # Player initialization is optional at startup
            self.player = None
        # Playhead overlay timer (60 Hz)
        try:
            self._playhead_timer = QtCore.QTimer(self)
            self._playhead_timer.setTimerType(QtCore.Qt.TimerType.PreciseTimer)
            self._playhead_timer.setInterval(20)
            self._playhead_timer.timeout.connect(self._update_playhead_overlay)
        except Exception:
            self._playhead_timer = None
        # Apply stored synth settings if any
        try:
            adm_init = get_appdata_manager()
            if str(adm_init.get("playback_type", "midi_port")) == "internal_synth":
                if not hasattr(self, 'player') or self.player is None:
                    from midi.player import Player
                    self.player = Player()
                lw = adm_init.get("synth_left_wavetable", []) or []
                rw = adm_init.get("synth_right_wavetable", []) or []
                # Apply preferred audio device first
                dev = str(adm_init.get("audio_output_device", "") or "")
                if dev and hasattr(self.player, 'set_audio_output_device'):
                    try:
                        self.player.set_audio_output_device(dev)
                    except Exception:
                        pass
                if lw and rw:
                    import numpy as _np
                    self.player.set_wavetables(_np.asarray(lw, dtype=_np.float32), _np.asarray(rw, dtype=_np.float32))
                self.player.set_adsr(float(adm_init.get("synth_attack", 0.005) or 0.005),
                                     float(adm_init.get("synth_decay", 0.05) or 0.05),
                                     float(adm_init.get("synth_sustain", 0.6) or 0.6),
                                     float(adm_init.get("synth_release", 0.1) or 0.1))
                try:
                    # Apply persisted master gain
                    if hasattr(self.player, 'set_gain'):
                        self.player.set_gain(float(adm_init.get("synth_gain", 0.35) or 0.35))
                    # Apply persisted humanize (detune cents)
                    if hasattr(self.player, 'set_humanize_detune_cents'):
                        self.player.set_humanize_detune_cents(float(adm_init.get("synth_humanize_cents", 3.0) or 3.0))
                    # Apply persisted humanize interval (seconds)
                    if hasattr(self.player, 'set_humanize_interval_s'):
                        self.player.set_humanize_interval_s(float(adm_init.get("synth_humanize_interval_s", 1.0) or 1.0))
                except Exception:
                    pass
        except Exception:
            pass

    def keyPressEvent(self, ev: QtGui.QKeyEvent) -> None:
        # Space toggles play/stop from the editor's time cursor (with note chasing)
        try:
            if ev.key() == QtCore.Qt.Key_Space:
                if not hasattr(self, 'player') or self.player is None:
                    from midi.player import Player
                    self.player = Player()
                if hasattr(self.player, 'is_playing') and self.player.is_playing():
                    self.player.stop()
                    # Clear playhead overlay immediately on stop
                    try:
                        self._clear_playhead_overlay()
                    except Exception:
                        pass
                else:
                    # Get start time from editor time cursor; default to 0.0
                    try:
                        t_units = float(getattr(self.editor_controller, 'time_cursor', 0.0) or 0.0)
                    except Exception:
                        t_units = 0.0
                    # Use unified helper to handle port selection prompt and retry
                    self._play_midi_with_prompt(start_units=t_units)
                ev.accept()
                return
        except Exception:
            pass
        # Hitting Escape should trigger app close (with save prompt)
        try:
            if ev.key() == QtCore.Qt.Key_Escape:
                self.close()
                ev.accept()
                return
        except Exception:
            pass
        super().keyPressEvent(ev)

    def closeEvent(self, ev: QtGui.QCloseEvent) -> None:
        # Ask FileManager for Yes/No/Cancel before quitting
        try:
            proceed = self.file_manager.confirm_close()
        except Exception:
            proceed = True
        if proceed:
            # Persist splitter sizes for next run
            try:
                sizes = self.splitter.sizes()
                adm = get_appdata_manager()
                adm.set("splitter_sizes", sizes)
            except Exception:
                pass
            ev.accept()
        else:
            ev.ignore()

    def _create_menus(self) -> None:
        menubar = self.menuBar()
        # Ensure macOS uses an in-window menubar (not the global system menubar)
        try:
            if sys.platform == "darwin":
                menubar.setNativeMenuBar(False)
        except Exception:
            pass

        # Create menus in normal left-to-right order (File, Edit, View, Playback)
        file_menu = menubar.addMenu("&File")
        edit_menu = menubar.addMenu("&Edit")
        view_menu = menubar.addMenu("&View")
        playback_menu = menubar.addMenu("&Playback")

        # File actions
        new_act = QtGui.QAction("New", self)
        open_act = QtGui.QAction("Load...", self)
        save_act = QtGui.QAction("Save", self)
        save_as_act = QtGui.QAction("Save As...", self)
        exit_act = QtGui.QAction("Exit", self)
        exit_act.triggered.connect(self.close)

        file_menu.addAction(new_act)
        file_menu.addAction(open_act)
        file_menu.addAction(save_act)
        file_menu.addAction(save_as_act)
        file_menu.addSeparator()

        export_pdf_act = QtGui.QAction("Export PDF...", self)
        export_pdf_act.triggered.connect(self._export_pdf)
        file_menu.addAction(export_pdf_act)

        # MIDI Output port chooser (under Playback menu)
        midi_port_act = QtGui.QAction("Set MIDI Output Port...", self)
        midi_port_act.triggered.connect(self._choose_midi_port)
        playback_menu.addAction(midi_port_act)

        # Playback Mode submenu (under Playback menu)
        pm_submenu = playback_menu.addMenu("Playback Mode")
        grp = QtGui.QActionGroup(self)
        act_midi = QtGui.QAction("External MIDI Port", self, checkable=True)
        act_synth = QtGui.QAction("Internal Synth", self, checkable=True)
        grp.addAction(act_midi)
        grp.addAction(act_synth)
        pm_submenu.addAction(act_midi)
        pm_submenu.addAction(act_synth)
        # Initialize from appdata
        try:
            adm = get_appdata_manager()
            mode = str(adm.get("playback_type", "midi_port") or "midi_port")
            if mode == "internal_synth":
                act_synth.setChecked(True)
            else:
                act_midi.setChecked(True)
        except Exception:
            act_midi.setChecked(True)
        # Handlers
        act_midi.triggered.connect(lambda: self._set_playback_mode("midi_port"))
        act_synth.triggered.connect(lambda: self._set_playback_mode("internal_synth"))

        # Audio output device chooser for internal synth (under Playback menu)
        audio_dev_act = QtGui.QAction("Set Audio Output Device...", self)
        audio_dev_act.triggered.connect(self._choose_audio_device)
        playback_menu.addAction(audio_dev_act)

        # System audio test tone (under Playback menu)
        sys_tone_act = QtGui.QAction("Play System Audio Test Tone", self)
        sys_tone_act.triggered.connect(self._play_system_test_tone)
        playback_menu.addAction(sys_tone_act)

        file_menu.addSeparator()
        file_menu.addAction(exit_act)

        # Edit actions
        undo_act = QtGui.QAction("Undo", self)
        undo_act.setShortcut(QtGui.QKeySequence.StandardKey.Undo)
        redo_act = QtGui.QAction("Redo", self)
        # Use platform-aware Redo shortcut to avoid ambiguity; explicit combos handled in editor
        try:
            redo_act.setShortcut(QtGui.QKeySequence.StandardKey.Redo)
        except Exception:
            pass
        edit_menu.addAction(undo_act)
        edit_menu.addAction(redo_act)
        # Cut/Copy/Paste actions (platform-aware shortcuts)
        cut_act = QtGui.QAction("Cut", self)
        cut_act.setShortcut(QtGui.QKeySequence.StandardKey.Cut)
        copy_act = QtGui.QAction("Copy", self)
        copy_act.setShortcut(QtGui.QKeySequence.StandardKey.Copy)
        paste_act = QtGui.QAction("Paste", self)
        paste_act.setShortcut(QtGui.QKeySequence.StandardKey.Paste)
        edit_menu.addSeparator()
        edit_menu.addAction(cut_act)
        edit_menu.addAction(copy_act)
        edit_menu.addAction(paste_act)
        # Delete selection action with visible shortcuts (Delete, Backspace)
        delete_act = QtGui.QAction("Delete", self)
        try:
            delete_act.setShortcuts([
                QtGui.QKeySequence(QtGui.QKeySequence.StandardKey.Delete),
                QtGui.QKeySequence(QtGui.QKeySequence.StandardKey.Backspace)
            ])
        except Exception:
            # Fallback: set single Delete shortcut
            try:
                delete_act.setShortcut(QtGui.QKeySequence(QtGui.QKeySequence.StandardKey.Delete))
            except Exception:
                pass
        edit_menu.addAction(delete_act)
        # Separator between Delete and Preferences
        edit_menu.addSeparator()
        prefs_act = QtGui.QAction("Preferences…", self)
        prefs_act.triggered.connect(self._open_preferences)
        edit_menu.addAction(prefs_act)
        # Quick synth test tone for troubleshooting (under Playback menu)
        test_tone_act = QtGui.QAction("Play Synth Test Tone", self)
        test_tone_act.triggered.connect(self._play_test_tone)
        playback_menu.addAction(test_tone_act)

        # View actions
        view_menu.addAction(QtGui.QAction("Zoom In", self))
        view_menu.addAction(QtGui.QAction("Zoom Out", self))

        # Wire up triggers
        new_act.triggered.connect(self._file_new)
        open_act.triggered.connect(self._file_open)
        save_act.triggered.connect(self._file_save)
        save_as_act.triggered.connect(self._file_save_as)
        undo_act.triggered.connect(self._edit_undo)
        redo_act.triggered.connect(self._edit_redo)
        cut_act.triggered.connect(self._edit_cut)
        copy_act.triggered.connect(self._edit_copy)
        paste_act.triggered.connect(self._edit_paste)
        delete_act.triggered.connect(self._edit_delete)

        # ---- Clock label manually positioned at menubar's right edge ----
        try:
            self._clock_label = QtWidgets.QLabel(menubar)
            self._clock_label.setObjectName("menuClock")
            # Match menubar font/palette for native look
            try:
                self._clock_label.setFont(menubar.font())
                self._clock_label.setPalette(menubar.palette())
            except Exception:
                pass
            # Vertically center text within the menubar height
            self._clock_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignVCenter)
            # Non-interactive
            self._clock_label.setAttribute(QtCore.Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
            self._clock_label.setContentsMargins(0, 0, 0, 0)
            self._clock_label.setStyleSheet("")
            self._update_clock()
            # Update every second
            self._clock_timer = QtCore.QTimer(self)
            self._clock_timer.setInterval(1000)
            self._clock_timer.timeout.connect(self._update_clock)
            self._clock_timer.start()
            # Keep position updated on menubar resize
            menubar.installEventFilter(self)
            QtCore.QTimer.singleShot(0, self._position_clock)
        except Exception:
            pass

    def _choose_midi_port(self) -> None:
        try:
            # Ensure player exists
            if not hasattr(self, 'player') or self.player is None:
                from midi.player import Player
                self.player = Player()
            # If not in MIDI mode, inform user
            try:
                adm = get_appdata_manager()
                if str(adm.get("playback_type", "midi_port")) != "midi_port":
                    QtWidgets.QMessageBox.information(self, "Playback Mode", "Switch to 'External MIDI Port' mode to choose a port.")
                    return
            except Exception:
                pass
            # Query ports
            try:
                names = self.player.list_output_ports()
            except Exception:
                names = []
            if not names:
                try:
                    QtWidgets.QMessageBox.warning(self, "MIDI Output", "No MIDI output ports found.")
                except Exception:
                    print("No MIDI output ports found.")
                return
            # Simple chooser dialog
            item, ok = QtWidgets.QInputDialog.getItem(self, "Select MIDI Output", "Port:", names, 0, False)
            if not ok:
                return
            try:
                self.player.set_output_port(str(item))
            except Exception as exc:
                try:
                    QtWidgets.QMessageBox.critical(self, "MIDI Output", f"Failed to open port: {exc}")
                except Exception:
                    print(f"Failed to open port: {exc}")
        except Exception:
            pass

    def _update_clock(self) -> None:
        try:
            now = datetime.now()
            timestr = now.strftime("%H:%M:%S")
            if hasattr(self, "_clock_label") and self._clock_label is not None:
                self._clock_label.setText(timestr)
                # Re-position in case width changed
                self._position_clock()
        except Exception:
            pass

    def _position_clock(self) -> None:
        try:
            menubar = self.menuBar()
            if not hasattr(self, "_clock_label") or self._clock_label is None:
                return
            rect = menubar.rect()
            sh = self._clock_label.sizeHint()
            # Height equals menubar height to align vertically; width to hint
            self._clock_label.resize(sh.width(), rect.height())
            x = max(0, rect.width() - self._clock_label.width() - 8)
            self._clock_label.move(x, 0)
            self._clock_label.show()
        except Exception:
            pass

    def _export_pdf(self) -> None:
        dlg = QtWidgets.QFileDialog(self)
        dlg.setAcceptMode(QtWidgets.QFileDialog.AcceptMode.AcceptSave)
        dlg.setNameFilter("PDF Files (*.pdf)")
        dlg.setDefaultSuffix("pdf")
        if dlg.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            out_path = dlg.selectedFiles()[0]
            try:
                from utils.CONSTANT import ENGRAVER_LAYERING
                self.du.save_pdf(out_path, layering=ENGRAVER_LAYERING)
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, "Export PDF failed", str(e))

    def _status(self, message: str, timeout_ms: int = 3000) -> None:
        """Show a transient message on the status bar."""
        try:
            sb = self.statusBar() if hasattr(self, 'statusBar') else None
            if sb is not None:
                sb.showMessage(str(message), int(max(0, timeout_ms)))
        except Exception:
            pass

    def _open_preferences(self) -> None:
        # Ensure preferences file exists and open in system editor
        open_preferences()

    def _file_new(self) -> None:
        # If there are unsaved changes, confirm save before starting a new project
        if not self.file_manager.confirm_save_for_action("creating a new project"):
            return
        self.file_manager.new()
        self._refresh_views_from_score()
        # Provide current score to editor for drawers needing direct access
        try:
            self.editor_controller.set_score(self.file_manager.current())
            # Reset undo stack for new project
            self.editor_controller.reset_undo_stack()
        except Exception:
            pass
        self._update_title()

    def _file_open(self) -> None:
        # If there are unsaved changes, confirm save before opening another project
        if not self.file_manager.confirm_save_for_action("opening another project"):
            return
        sc = self.file_manager.load()
        if sc:
            self._refresh_views_from_score()
            try:
                self.editor_controller.set_score(self.file_manager.current())
                # Reset undo stack after opening existing project
                self.editor_controller.reset_undo_stack()
            except Exception:
                pass
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

    @QtCore.Slot(int, int, float, float)
    def _on_editor_metrics(self, content_px: int, viewport_px: int, px_per_mm: float, dpr: float) -> None:
        # External QScrollBar works in logical pixels
        scale = max(1.0, dpr)
        max_scroll = max(0, int(round((content_px - viewport_px) / scale)))
        self.editor_vscroll.setRange(0, max_scroll)
        # Page step ~ 80% of viewport height (logical px)
        self.editor_vscroll.setPageStep(int(max(1, round(0.8 * viewport_px / scale))))
        # Single step ~ 40mm in logical pixels (independent of editor zoom)
        base_mm_per_step = 40.0
        device_px_step = base_mm_per_step * px_per_mm
        logical_px_step = int(max(1, round(device_px_step / scale)))
        self.editor_vscroll.setSingleStep(logical_px_step)
        # Clamp current value within new range to avoid unbounded wheel scroll
        cur = int(self.editor_vscroll.value())
        if cur > max_scroll:
            self.editor_vscroll.setValue(max_scroll)

    @QtCore.Slot(int)
    def _on_editor_scroll_changed(self, value: int) -> None:
        self.editor.set_scroll_logical_px(value)

    def _edit_undo(self) -> None:
        self.editor_controller.undo()
        self._refresh_views_from_score()
        try:
            self.editor_controller.set_score(self.file_manager.current())
        except Exception:
            pass

    def _edit_redo(self) -> None:
        self.editor_controller.redo()
        self._refresh_views_from_score()
        try:
            self.editor_controller.set_score(self.file_manager.current())
        except Exception:
            pass

    def _edit_copy(self) -> None:
        try:
            self.editor_controller.copy_selection()
            self._status("Copied selection", 1200)
        except Exception:
            pass

    def _edit_cut(self) -> None:
        try:
            self.editor_controller.cut_selection()
            self._refresh_views_from_score()
            try:
                self.editor_controller.set_score(self.file_manager.current())
            except Exception:
                pass
            self._status("Cut selection", 1200)
        except Exception:
            pass

    def _edit_paste(self) -> None:
        try:
            self.editor_controller.paste_selection_at_cursor()
            self._refresh_views_from_score()
            try:
                self.editor_controller.set_score(self.file_manager.current())
            except Exception:
                pass
            self._status("Pasted selection", 1200)
        except Exception:
            pass

    def _edit_delete(self) -> None:
        try:
            deleted = False
            if hasattr(self.editor_controller, 'delete_selection'):
                res = self.editor_controller.delete_selection()
                deleted = bool(res)
            if deleted:
                self._refresh_views_from_score()
                try:
                    self.editor_controller.set_score(self.file_manager.current())
                except Exception:
                    pass
                self._status("Deleted selection", 1200)
            else:
                self._status("No selection to delete", 1200)
        except Exception:
            pass

    def _update_title(self) -> None:
        p = self.file_manager.path()
        if p:
            self.setWindowTitle(f"keyTAB - existing project ({str(p)})")
        else:
            self.setWindowTitle("keyTAB - new project (unsaved)")

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

    def _fit_print_view_to_page(self, *_args) -> None:
        """Toggle fit/hidden state and ensure in-between positions snap to fit.

        Behavior:
        - If currently fitted (self.is_fit): hide the print view.
        - Else: run the fit logic.
        - If not hidden and not fitted (in-between): run the fit logic.
        """
        splitter = self.centralWidget()
        if splitter is None:
            return
        
        print("Fitting print view to page...")

        # Helper: compute desired fit sizes
        def compute_fit_sizes() -> tuple[int, int]:
            w_mm, h_mm = self._page_dimensions_mm()
            if w_mm <= 0 or h_mm <= 0:
                return (splitter.width(), 0)
            # Exclude handle width to compute available content width
            try:
                handle_w = int(splitter.handleWidth())
            except Exception:
                handle_w = 0
            total_w = max(0, splitter.width() - handle_w)
            # Use splitter height (more stable at startup/maximized) for fit computations
            pv_h = max(1, splitter.height())
            ideal_pv_w = int(round(pv_h * (w_mm / h_mm)))
            # Clamp to available width to avoid oversizing when maximized/startup
            pv_w = min(max(0, ideal_pv_w), total_w)
            editor_w = max(0, total_w - pv_w)
            return (editor_w, pv_w)

        # Current sizes and state
        sizes = splitter.sizes() or [splitter.width(), 0]
        cur_editor_w = int(sizes[0]) if sizes else splitter.width()
        cur_pv_w = int(sizes[1]) if len(sizes) > 1 else 0
        fitted_editor_w, fitted_pv_w = compute_fit_sizes()

        # on startup, we always start fitted
        if self.is_startup:
            self.is_startup = False
            splitter.setSizes([fitted_editor_w, fitted_pv_w])
            QtCore.QTimer.singleShot(0, self.print_view.request_render)
            return

        # Determine if hidden or fitted (with small tolerance)
        hidden = (cur_pv_w <= 0)
        fit_tolerance = 2
        fitted = (abs(cur_pv_w - fitted_pv_w) <= fit_tolerance and abs(cur_editor_w - fitted_editor_w) <= fit_tolerance)
        self.is_fit = fitted

        if self.is_fit:
            # Hide the print view
            splitter.setSizes([cur_editor_w + cur_pv_w, 0])
            self.is_fit = False
            return

        # If not hidden and not fitted (in-between), or hidden: run fit logic
        if (not hidden and not fitted) or hidden:
            splitter.setSizes([fitted_editor_w, fitted_pv_w])
            QtCore.QTimer.singleShot(0, self.print_view.request_render)
            self.is_fit = True
            return

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
        # Delegate to unified helper without a time cursor start
        self._play_midi_with_prompt(start_units=None)

    def _stop_midi(self) -> None:
        try:
            if hasattr(self, 'player') and self.player is not None:
                self.player.stop()
            # Clear playhead overlay when stopping
            self._clear_playhead_overlay()
        except Exception:
            pass

    def _play_midi_with_prompt(self, start_units: Optional[float]) -> None:
        """Play SCORE, prompting for MIDI port if unavailable, then retry once.

        If start_units is provided, starts from the editor's time cursor; otherwise
        plays the full score.
        """
        try:
            if not hasattr(self, 'player') or self.player is None:
                from midi.player import Player
                self.player = Player()
            sc = self.file_manager.current()
            # If internal synth mode, no port prompt
            try:
                adm = get_appdata_manager()
                if str(adm.get("playback_type", "midi_port")) == "internal_synth":
                    if start_units is None:
                        self.player.play_score(sc)
                    else:
                        self.player.play_from_time_cursor(float(start_units or 0.0), sc)
                    # Start playhead timer
                    self._start_playhead_timer()
                    # Show playback debug status
                    self._show_play_debug_status()
                    return
            except Exception:
                pass
            # First attempt
            try:
                if start_units is None:
                    self.player.play_score(sc)
                else:
                    self.player.play_from_time_cursor(float(start_units or 0.0), sc)
                # Start playhead timer
                self._start_playhead_timer()
                self._show_play_debug_status()
                return
            except Exception:
                # Likely missing or failed MIDI port; prompt user to select one
                try:
                    self._choose_midi_port()
                except Exception:
                    pass
                # Retry once after selection
                try:
                    if start_units is None:
                        self.player.play_score(sc)
                    else:
                        self.player.play_from_time_cursor(float(start_units or 0.0), sc)
                    # Start playhead timer
                    self._start_playhead_timer()
                    self._show_play_debug_status()
                    return
                except Exception as exc2:
                    # Fallback to internal synth automatically
                    try:
                        self._status("No usable MIDI port. Switching to Internal Synth.", 3000)
                        self._set_playback_mode("internal_synth")
                        if start_units is None:
                            self.player.play_score(sc)
                        else:
                            self.player.play_from_time_cursor(float(start_units or 0.0), sc)
                        # Start playhead timer
                        self._start_playhead_timer()
                        self._show_play_debug_status()
                        return
                    except Exception:
                        # Notify user if still failing
                        try:
                            QtWidgets.QMessageBox.critical(self, "Playback", f"Playback failed: {exc2}")
                        except Exception:
                            print(f"Playback failed: {exc2}")
        except Exception:
            pass

    def _start_playhead_timer(self) -> None:
        try:
            if hasattr(self, '_playhead_timer') and self._playhead_timer is not None:
                if not self._playhead_timer.isActive():
                    self._playhead_timer.start()
            # Immediate update for responsiveness
            self._update_playhead_overlay()
        except Exception:
            pass

    def _show_play_debug_status(self) -> None:
        try:
            if hasattr(self, 'player') and self.player is not None and hasattr(self.player, 'get_debug_status'):
                info = self.player.get_debug_status()
                mode = info.get('playback_type', '')
                bpm = info.get('bpm', 0)
                ev = info.get('events', 0)
                if mode == 'internal_synth':
                    dev = info.get('device', '') or 'default'
                    gain = info.get('gain', 0.0)
                    self._status(f"Playing (Synth) • {ev} notes • {bpm:.0f} BPM • Device: {dev} • Gain: {gain:.2f}", 3000)
                else:
                    port = info.get('midi_port', '') or '(auto)'
                    self._status(f"Playing (MIDI) • {ev} notes • {bpm:.0f} BPM • Port: {port}", 3000)
        except Exception:
            pass

    def _update_playhead_overlay(self) -> None:
        try:
            if hasattr(self, 'player') and self.player is not None and hasattr(self.player, 'is_playing') and self.player.is_playing():
                units = None
                try:
                    units = self.player.get_playhead_units() if hasattr(self.player, 'get_playhead_units') else None
                except Exception:
                    units = None
                # Update editor playhead and trigger overlay refresh
                try:
                    self.editor_controller.playhead_units = units
                except Exception:
                    pass
                try:
                    if hasattr(self.editor, 'request_overlay_refresh'):
                        self.editor.request_overlay_refresh()
                    else:
                        self.editor.update()
                except Exception:
                    pass
            else:
                # Not playing: clear and stop timer
                self._clear_playhead_overlay()
        except Exception:
            pass

    def _clear_playhead_overlay(self) -> None:
        try:
            if hasattr(self, '_playhead_timer') and self._playhead_timer is not None and self._playhead_timer.isActive():
                self._playhead_timer.stop()
        except Exception:
            pass
        try:
            self.editor_controller.playhead_units = None
            if hasattr(self.editor, 'request_overlay_refresh'):
                self.editor.request_overlay_refresh()
            else:
                self.editor.update()
        except Exception:
            pass

    # FX window removed
    def _open_fx_editor(self) -> None:
        try:
            # Show simple wavetable/ADSR editor and apply settings
            from ui.widgets.wavetable_editor import WavetableEditor
            dlg = WavetableEditor(self)
            try:
                dlg.setModal(False)
                dlg.setWindowModality(QtCore.Qt.WindowModality.NonModal)
            except Exception:
                pass
            # Initialize from appdata
            adm = get_appdata_manager()
            def on_apply(left, right, a, d, s, r, g, h, hi):
                try:
                    if not hasattr(self, 'player') or self.player is None:
                        from midi.player import Player
                        self.player = Player()
                    self.player.set_wavetables(left, right)
                    self.player.set_adsr(a, d, s, r)
                    if hasattr(self.player, 'set_gain'):
                        self.player.set_gain(float(g))
                    if hasattr(self.player, 'set_humanize_detune_cents'):
                        self.player.set_humanize_detune_cents(float(h))
                    if hasattr(self.player, 'set_humanize_interval_s'):
                        self.player.set_humanize_interval_s(float(hi))
                    adm.set("synth_left_wavetable", [float(x) for x in list(left)])
                    adm.set("synth_right_wavetable", [float(x) for x in list(right)])
                    adm.set("synth_attack", float(a))
                    adm.set("synth_decay", float(d))
                    adm.set("synth_sustain", float(s))
                    adm.set("synth_release", float(r))
                    adm.set("synth_gain", float(g))
                    adm.set("synth_humanize_cents", float(h))
                    adm.set("synth_humanize_interval_s", float(hi))
                    adm.save()
                    self._status("Synth updated", 1500)
                except Exception:
                    pass
            dlg.wavetablesApplied.connect(on_apply)
            # Keep dialog reference to avoid GC while modeless
            try:
                self._fx_dialog = dlg
            except Exception:
                pass
            dlg.show()
        except Exception:
            pass

    def _set_playback_mode(self, mode: str) -> None:
        try:
            if not hasattr(self, 'player') or self.player is None:
                from midi.player import Player
                self.player = Player()
            try:
                self.player.stop()
            except Exception:
                pass
            try:
                # Persist and update player
                adm = get_appdata_manager()
                adm.set("playback_type", str(mode))
                adm.save()
                if hasattr(self.player, 'set_playback_type'):
                    self.player.set_playback_type(str(mode))
            except Exception:
                pass
            self._status(f"Playback mode: {'Internal Synth' if mode=='internal_synth' else 'External MIDI Port'}", 2500)
        except Exception:
            pass

    def _play_test_tone(self) -> None:
        try:
            # Ensure player and synth exist
            if not hasattr(self, 'player') or self.player is None:
                from midi.player import Player
                self.player = Player()
            # Switch to synth temporarily if needed
            try:
                if hasattr(self.player, 'set_playback_type'):
                    self.player.set_playback_type('internal_synth')
            except Exception:
                pass
            # Use synth directly if available
            try:
                from synth.wavetable_synth import WavetableSynth
            except Exception:
                WavetableSynth = None  # type: ignore
            if WavetableSynth is None:
                self._status("Synth backend unavailable", 2500)
                return
            # Trigger A4 (MIDI 69) for ~1 second
            if hasattr(self.player, '_synth') and self.player._synth is None:
                try:
                    self.player._synth = WavetableSynth()
                except Exception:
                    pass
            if hasattr(self.player, '_synth') and self.player._synth is not None:
                try:
                    # Apply preferred audio device if set
                    try:
                        dev = str(get_appdata_manager().get("audio_output_device", "") or "")
                        if dev and hasattr(self.player, 'set_audio_output_device'):
                            self.player.set_audio_output_device(dev)
                    except Exception:
                        pass
                    # Ensure any previous playback is stopped
                    try:
                        self.player._synth.all_notes_off()
                    except Exception:
                        pass
                    self.player._synth.note_on(69, 110)
                    QtCore.QTimer.singleShot(1000, lambda: self.player._synth.note_off(69))
                    dev = getattr(self.player._synth, '_device_name', '') or 'default'
                    self._status(f"Synth test tone → {dev}", 2000)
                except Exception:
                    pass
        except Exception:
            pass

    def _choose_audio_device(self) -> None:
        try:
            import sounddevice as sd
        except Exception:
            QtWidgets.QMessageBox.critical(self, "Audio", "sounddevice not available")
            return
        try:
            devices = sd.query_devices()
            outputs = [d for d in devices if int(d.get('max_output_channels', 0)) > 0]
            if not outputs:
                QtWidgets.QMessageBox.warning(self, "Audio", "No audio output devices found.")
                return
            names = [str(d.get('name', '')) for d in outputs]
            # Preselect previously saved device if available
            pref = str(get_appdata_manager().get("audio_output_device", "") or "")
            default_index = names.index(pref) if pref in names else 0
            item, ok = QtWidgets.QInputDialog.getItem(self, "Select Audio Output", "Device:", names, default_index, False)
            if not ok:
                return
            name = str(item)
            adm = get_appdata_manager()
            adm.set("audio_output_device", name)
            adm.save()
            # Apply to synth if present
            try:
                if not hasattr(self, 'player') or self.player is None:
                    from midi.player import Player
                    self.player = Player()
                if hasattr(self.player, 'set_audio_output_device'):
                    self.player.set_audio_output_device(name)
            except Exception:
                pass
            self._status(f"Audio device set: {name}", 2500)
        except Exception as exc:
            try:
                QtWidgets.QMessageBox.critical(self, "Audio", f"Failed to list devices: {exc}")
            except Exception:
                pass

    def _play_system_test_tone(self) -> None:
        try:
            import numpy as _np
            import sounddevice as sd
            import threading as _th
            sr = 48000
            dur = 1.5
            t = _np.arange(int(sr * dur), dtype=_np.float32) / sr
            wave = _np.sin(2 * _np.pi * 440.0 * t).astype(_np.float32)
            stereo = _np.column_stack([wave, wave])
            # Preferred device
            name = str(get_appdata_manager().get("audio_output_device", "") or "")
            dev = name if name else 'default'
            # Stop any previous playback
            try:
                sd.stop()
            except Exception:
                pass
            # Play in a short background thread using OutputStream to avoid finished_callback errors
            def _play_stream():
                stream = None
                try:
                    stream = sd.OutputStream(samplerate=sr, channels=2, dtype='float32', device=name if name else None)
                    stream.start()
                    stream.write(stereo)
                except Exception:
                    pass
                finally:
                    try:
                        if stream is not None:
                            stream.stop()
                            stream.close()
                    except Exception:
                        pass
            _th.Thread(target=_play_stream, daemon=True).start()
            self._status(f"System test tone → {dev}", 2000)
        except Exception as exc:
            try:
                QtWidgets.QMessageBox.critical(self, "Audio", f"Test tone failed: {exc}")
            except Exception:
                pass

    def _force_redraw(self, *_args) -> None:
        # Rebuild editor caches and hit-rects for immediate tool feedback
        if hasattr(self, 'editor_controller') and self.editor_controller is not None:
            self.editor_controller.draw_frame()
        # Also refresh the canvas overlays so guide stem direction updates instantly
        try:
            if hasattr(self, 'editor') and self.editor is not None:
                if hasattr(self.editor, 'request_overlay_refresh'):
                    self.editor.request_overlay_refresh()
                else:
                    # Fallback: normal repaint
                    self.editor.update()
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
        ...

    def _on_snap_changed(self, base: int, divide: int) -> None:
        # Update editor snap size units and request a redraw
        try:
            size_units = self.snap_dock.selector.get_snap_size()
            if hasattr(self, 'editor_controller') and self.editor_controller is not None:
                self.editor_controller.set_snap_size_units(size_units)
                self.editor_controller.draw_frame()
                
            if hasattr(self, 'editor_canvas') and self.editor_canvas is not None:
                self.editor_canvas.update()
            # Persist to appdata
            try:
                adm = get_appdata_manager()
                adm.set("snap_base", int(base))
                adm.set("snap_divide", int(divide))
                adm.save()
            except Exception:
                pass
        except Exception:
            pass

    def _on_tool_selected(self, name: str) -> None:
        # Persist selected tool to appdata
        try:
            adm = get_appdata_manager()
            adm.set("selected_tool", str(name))
            adm.save()
        except Exception:
            pass

    def _demo_add_rect(self) -> None:
        # Removed test drawing logic
        pass

    def _center_on_primary(self) -> None:
        # Move window to the center of the primary screen
        try:
            # If the window is maximized or fullscreen, do not attempt to center
            if self.isMaximized() or self.isFullScreen():
                return
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

    # Duplicate keyPressEvent removed; using the earlier implementation for Escape handling

    def prepare_close(self) -> None:
        # Ensure worker threads are stopped before application exits
        # Persist window state to appdata
        try:
            adm = get_appdata_manager()
            adm.set("window_maximized", bool(self.isMaximized()))
            try:
                geom_b64 = bytes(self.saveGeometry().toBase64()).decode("ascii")
                adm.set("window_geometry", geom_b64)
            except Exception:
                pass
            # Save current splitter sizes for next startup
            try:
                sp = self.centralWidget()
                if sp is not None and hasattr(sp, 'sizes'):
                    sizes = list(sp.sizes())
                    adm.set("splitter_sizes", [int(sizes[0]) if sizes else 0, int(sizes[1]) if len(sizes) > 1 else 0])
            except Exception:
                pass
            # Persist whether the session is currently saved to a project file
            try:
                fm = getattr(self, 'file_manager', None)
                if fm is not None:
                    # Session considered saved if we have a project path and it's not dirty
                    was_saved = bool(fm.path() is not None and not fm.is_dirty())
                    adm.set("last_session_saved", was_saved)
                    adm.set("last_session_path", str(fm.path() or ""))
            except Exception:
                pass
            adm.save()
        except Exception:
            pass
        # Stop clock timer gracefully
        try:
            if hasattr(self, "_clock_timer") and self._clock_timer is not None:
                self._clock_timer.stop()
        except Exception:
            pass
        # Stop audio playback gracefully
        try:
            if hasattr(self, 'player') and self.player is not None:
                self.player.stop()
        except Exception:
            pass
        # Stop playhead timer and clear overlay
        try:
            self._clear_playhead_overlay()
        except Exception:
            pass
        # Close FX dialog if open
        try:
            if hasattr(self, '_fx_dialog') and self._fx_dialog is not None:
                self._fx_dialog.close()
                self._fx_dialog = None
        except Exception:
            pass
        if hasattr(self, "print_view") and self.print_view is not None:
            try:
                self.print_view.shutdown()
            except Exception:
                pass

    def closeEvent(self, ev: QtGui.QCloseEvent) -> None:
        # Unified close handling: confirm save, then prepare and accept
        try:
            proceed = self.file_manager.confirm_close()
        except Exception:
            proceed = True
        if proceed:
            # Persist sizes via prepare_close
            try:
                self.prepare_close()
            except Exception:
                pass
            ev.accept()
        else:
            ev.ignore()
