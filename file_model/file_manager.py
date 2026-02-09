from __future__ import annotations

from pathlib import Path
from typing import Optional, Tuple
import os
import sys
from datetime import datetime

from PySide6.QtWidgets import QFileDialog, QMessageBox, QWidget

from file_model.SCORE import SCORE, EditorSettings, MetaData
from file_model.header import Header, HeaderText
from file_model.base_grid import BaseGrid
from file_model.appstate import AppState
from file_model.layout import Layout
from utils.CONSTANT import UTILS_SAVE_DIR
from settings_manager import get_preferences_manager
from appdata_manager import get_appdata_manager


class FileManager:
    """
    Manages creating, opening, and saving SCORE files with native dialogs.

    - Holds the current SCORE instance and its filesystem path
    - Uses SCORE.new(), SCORE.load(path), and SCORE.save(path)
    - Provides new(), open(), save(), and save_as() methods
    """

    # Open dialog: show both .piano and .mid/.midi by default
    OPEN_FILE_FILTER = "Supported Files (*.piano *.mid *.midi);;keyTAB Score (*.piano);;MIDI File (*.mid *.midi);;All Files (*)"
    # Save dialog: prefer only .piano
    SAVE_FILE_FILTER = "keyTAB Score (*.piano);;All Files (*)"

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        self._parent: Optional[QWidget] = parent
        self._current: SCORE = SCORE().new()
        self._path: Optional[Path] = None
        # Initialize last_dir from appdata if available, else home
        try:
            adm = get_appdata_manager()
            last_dir_str = str(adm.get("last_file_dialog_dir", "") or "")
            self._last_dir: Path = Path(last_dir_str) if last_dir_str else Path.home()
        except Exception:
            self._last_dir: Path = Path.home()
        self._dirty: bool = False
        # Ensure the autosave directory exists on initialization
        os.makedirs(UTILS_SAVE_DIR, exist_ok=True)

    # Accessors
    def current(self) -> SCORE:
        return self._current

    def path(self) -> Optional[Path]:
        return self._path

    def set_parent(self, parent: Optional[QWidget]) -> None:
        self._parent = parent

    # Core operations
    def new(self) -> SCORE:
        """Create a new SCORE and clear the current path."""
        self._current = SCORE().new()
        try:
            adm = get_appdata_manager()
            template = adm.get("score_template", {})
            if isinstance(template, dict) and template:
                self._apply_score_template(template)
            else:
                template = adm.get("layout_template", {})
                if isinstance(template, dict) and template:
                    self._apply_layout_template(template)
        except Exception:
            pass
        self._path = None
        self._dirty = False
        return self._current

    def _apply_layout_template(self, template: dict) -> None:
        layout = getattr(self._current, 'layout', None)
        if layout is None:
            return
        valid_fields = {f.name for f in getattr(Layout, '__dataclass_fields__', {}).values()}
        for key, value in template.items():
            if key not in valid_fields:
                continue
            try:
                setattr(layout, key, value)
            except Exception:
                continue

    def _apply_score_template(self, template: dict) -> None:
        if not isinstance(template, dict):
            return
        score = self._current
        data = dict(template or {})
        data.pop('events', None)

        def _build_header(entry: dict) -> Header:
            base = Header()
            if not isinstance(entry, dict):
                return base
            def _text_from(d: dict | None, fallback: HeaderText) -> HeaderText:
                if not isinstance(d, dict):
                    return fallback
                return HeaderText(
                    text=str(d.get('text', fallback.text)),
                    family=str(d.get('family', fallback.family)),
                    size_pt=float(d.get('size_pt', fallback.size_pt)),
                    bold=bool(d.get('bold', fallback.bold)),
                    italic=bool(d.get('italic', fallback.italic)),
                    x_offset_mm=float(d.get('x_offset_mm', fallback.x_offset_mm)),
                    y_offset_mm=float(d.get('y_offset_mm', fallback.y_offset_mm)),
                )
            title = _text_from(data.get('header', {}).get('title') if isinstance(data.get('header', {}), dict) else None, base.title)
            composer = _text_from(data.get('header', {}).get('composer') if isinstance(data.get('header', {}), dict) else None, base.composer)
            copyright_text = _text_from(data.get('header', {}).get('copyright') if isinstance(data.get('header', {}), dict) else None, base.copyright)
            return Header(title=title, composer=composer, copyright=copyright_text)

        try:
            layout_data = data.get('layout')
            if isinstance(layout_data, dict):
                score.layout = Layout(**layout_data)
        except Exception:
            pass
        try:
            score.header = _build_header(data.get('header', {}) if isinstance(data.get('header', {}), dict) else {})
        except Exception:
            pass
        try:
            editor_data = data.get('editor')
            if isinstance(editor_data, dict):
                score.editor = EditorSettings(**editor_data)
        except Exception:
            pass
        try:
            app_state_data = data.get('app_state')
            if isinstance(app_state_data, dict):
                score.app_state = AppState(**app_state_data)
        except Exception:
            pass
        try:
            meta_data = data.get('meta_data')
            if isinstance(meta_data, dict):
                score.meta_data = MetaData(**meta_data)
        except Exception:
            pass
        try:
            base_grid = data.get('base_grid')
            if isinstance(base_grid, list):
                score.base_grid = [BaseGrid(**bg) if isinstance(bg, dict) else BaseGrid() for bg in base_grid]
        except Exception:
            pass

    def replace_current(self, new_score: SCORE) -> None:
        """Replace the current SCORE instance (used by undo/redo)."""
        self._current = new_score
        # Autosave on any model replacement (e.g., undo/redo application)
        self.autosave_current()
        # Consider undo/redo a model change relative to last explicit save
        self._dirty = True

    def load(self) -> Optional[SCORE]:
        """Load a .piano file via a native file dialog and load into SCORE."""
        start_dir = str(self._path.parent if self._path else self._last_dir)
        fname, _ = QFileDialog.getOpenFileName(
            self._parent,
            "Load Score",
            start_dir,
            self.OPEN_FILE_FILTER,
        )
        if not fname:
            return None
        try:
            suffix = Path(fname).suffix.lower()
            if suffix in (".mid", ".midi"):
                # Load MIDI via midi_loader to new SCORE; keep project path unset
                try:
                    from midi.midi_loader import midi_load
                    self._current = midi_load(fname)
                except Exception as exc:
                    raise RuntimeError(f"Failed to load MIDI: {exc}")
                self._path = None
                self._last_dir = Path(fname).parent
                try:
                    adm = get_appdata_manager()
                    adm.set("last_file_dialog_dir", str(self._last_dir))
                    adm.save()
                except Exception:
                    pass
                # Imported from external format; mark dirty until explicitly saved
                self._dirty = True
                try:
                    adm = get_appdata_manager()
                    adm.set("last_opened_file", str(fname))
                    adm.save()
                    self._push_recent_file(str(fname))
                except Exception:
                    pass
                return self._current
            else:
                # Native keyTAB file
                self._current = SCORE().load(fname)
                self._path = Path(fname)
                self._last_dir = self._path.parent
                try:
                    adm = get_appdata_manager()
                    adm.set("last_file_dialog_dir", str(self._last_dir))
                    adm.save()
                except Exception:
                    pass
                self._dirty = False
                # Track last opened file in appdata
                try:
                    adm = get_appdata_manager()
                    adm.set("last_opened_file", str(self._path))
                    adm.save()
                    self._push_recent_file(str(self._path))
                except Exception:
                    pass
                return self._current
        except Exception as exc:
            self._show_error("Failed to open score", f"{exc}")
            return None

    def open_path(self, path: str) -> Optional[SCORE]:
        """Programmatically open a .piano file from a given path.

        Returns the SCORE on success, None on failure.
        """
        try:
            suffix = Path(path).suffix.lower()
            if suffix in (".mid", ".midi"):
                from midi.midi_loader import midi_load
                self._current = midi_load(path)
                self._path = None
                self._last_dir = Path(path).parent
                self._dirty = True
                try:
                    adm = get_appdata_manager()
                    adm.set("last_opened_file", str(path))
                    adm.save()
                    self._push_recent_file(str(path))
                except Exception:
                    pass
                return self._current
            else:
                self._current = SCORE().load(path)
                self._path = Path(path)
                self._last_dir = self._path.parent
                self._dirty = False
                try:
                    adm = get_appdata_manager()
                    adm.set("last_opened_file", str(self._path))
                    adm.save()
                    self._push_recent_file(str(self._path))
                except Exception:
                    pass
                return self._current
        except Exception as exc:
            self._show_error("Failed to open score", f"{exc}")
            return None

    def save(self) -> bool:
        """Save to the current path, or prompt Save As if none."""
        if self._path is None:
            return self.save_as()
        try:
            self._current.save(str(self._path))
            self._dirty = False
            try:
                adm = get_appdata_manager()
                adm.set("last_opened_file", str(self._path))
                adm.save()
            except Exception:
                pass
            return True
        except Exception as exc:
            self._show_error("Failed to save score", f"{exc}")
            return False

    def save_as(self) -> bool:
        """Prompt for a path and save the current SCORE there."""
        start_dir = str(self._path.parent if self._path else self._last_dir)
        fname, _ = QFileDialog.getSaveFileName(
            self._parent,
            "Save Score As",
            start_dir,
            self.SAVE_FILE_FILTER,
        )
        if not fname:
            return False
        target = self._ensure_piano_suffix(Path(fname))
        try:
            self._current.save(str(target))
            self._path = target
            self._last_dir = target.parent
            try:
                adm = get_appdata_manager()
                adm.set("last_file_dialog_dir", str(self._last_dir))
                adm.save()
            except Exception:
                pass
            self._dirty = False
            try:
                adm = get_appdata_manager()
                adm.set("last_opened_file", str(self._path))
                adm.save()
            except Exception:
                pass
            return True
        except Exception as exc:
            self._show_error("Failed to save score", f"{exc}")
            return False

    # Confirmation helpers for destructive actions
    def confirm_save_for_action(self, action_description: str, force_prompt: bool = False) -> bool:
        """If dirty, ask to save before proceeding with an action.

        Returns True to proceed, False to cancel the action.

        - Yes: save (Save As if no path). Proceed only if save succeeds.
        - No: proceed without saving.
        - Cancel: abort the action.
        """
        # Always snapshot the session so state can be restored even if action discards changes
        try:
            self.autosave_current()
        except Exception:
            pass

        # If auto-save is enabled, skip prompting and proceed unless forced
        if not force_prompt:
            try:
                pm = get_preferences_manager()
                if bool(pm.get("auto_save", True)):
                    return True
            except Exception:
                # Default to enabled behavior on errors
                return True

        if not self.is_dirty():
            return True
        if self._parent is None:
            # In non-GUI context, default to proceed
            return True
        msg = QMessageBox(self._parent)
        msg.setIcon(QMessageBox.Question)
        msg.setWindowTitle("Save changes?")
        msg.setText(f"Do you want to save changes before {action_description}?")
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)
        msg.setDefaultButton(QMessageBox.Yes)
        result = msg.exec()

        if result == QMessageBox.Yes:
            success = self.save() if (self._path is not None) else self.save_as()
            return bool(success)
        elif result == QMessageBox.No:
            return True
        else:
            return False

    # Helpers
    def _ensure_piano_suffix(self, p: Path) -> Path:
        if p.suffix.lower() != ".piano":
            p = p.with_suffix(".piano")
        return p

    def _show_error(self, title: str, text: str) -> None:
        if self._parent is None:
            # If no parent (non-GUI context), silently ignore GUI messagebox
            return
        msg = QMessageBox(self._parent)
        msg.setIcon(QMessageBox.Critical)
        msg.setWindowTitle(title)
        msg.setText(text)
        msg.exec()

    # Autosave and error-backup utilities
    def autosave_current(self) -> None:
        """Save the current SCORE to the session file in appdata (JSON)."""
        target = Path(UTILS_SAVE_DIR) / "session.piano"
        try:
            self._current.save(str(target))
        except Exception:
            pass

    def _push_recent_file(self, path: str) -> None:
        try:
            p = str(path or "").strip()
            if not p:
                return
            adm = get_appdata_manager()
            recent = adm.get("recent_files", []) or []
            if not isinstance(recent, list):
                recent = []
            recent = [str(x) for x in recent if str(x).strip()]
            recent = [x for x in recent if x != p]
            recent.insert(0, p)
            recent = recent[:100]
            adm.set("recent_files", recent)
            adm.save()
        except Exception:
            pass

    def on_model_changed(self) -> None:
        """Handle model change: autosave to project and session based on settings."""
        # Always write a session copy so we can restore work
        self.autosave_current()
        auto_save_enabled = False
        try:
            pm = get_preferences_manager()
            auto_save_enabled = bool(pm.get("auto_save", True))
        except Exception:
            auto_save_enabled = True
        if auto_save_enabled:
            # Save to project file if we have a path
            if self._path is not None:
                ok = self.save()
                if not ok:
                    # if saving failed, keep dirty flag so user is warned on exit
                    self._dirty = True
                else:
                    self._dirty = False
            else:
                # No project path yet; keep dirty but session is saved
                self._dirty = True
        else:
            # Only mark dirty without saving project file
            self._dirty = True

    def install_error_backup_hook(self) -> None:
        """Install a global excepthook to save a timestamped backup on errors."""
        # Preserve the original hook
        original_hook = sys.excepthook

        def _hook(exctype, value, tb):
            # Save timestamped error backup; format: dd-mm-YYYY-HH.MM.SS
            ts = datetime.now().strftime("%d-%m-%Y-%H.%M.%S")
            fname = f"pianoscript_error_backup_{ts}.piano"
            target = Path(UTILS_SAVE_DIR) / fname
            try:
                self._current.save(str(target))
            except Exception:
                # If backup saving itself fails, continue to report the exception
                pass
            # Delegate to original hook to print traceback to terminal
            original_hook(exctype, value, tb)

        sys.excepthook = _hook

    def load_session_if_available(self) -> bool:
        """Load session.piano from appdata into current score; keep path unset.

        Returns True if a session was restored.
        """
        session_path = Path(UTILS_SAVE_DIR) / "session.piano"
        if not session_path.exists():
            return False
        try:
            sc = SCORE().load(str(session_path))
            # Do not treat the session file as the project path
            self._current = sc
            self._path = None
            self._dirty = True
            return True
        except Exception:
            return False

    # ---- Close confirmation ----
    def confirm_close(self) -> bool:
        """Ask user to save before quitting with Yes/No/Cancel.

        Returns True to proceed with closing the app, False to cancel.

        - Yes: attempts to save (Save As if no path); proceeds only on success
        - No: proceeds without saving
        - Cancel: aborts closing
        """
        # Always snapshot the session so state restores exactly on next startup
        try:
            self.autosave_current()
        except Exception:
            pass

        # If auto-save is enabled, no prompt; project has been saved on edits
        try:
            pm = get_preferences_manager()
            if bool(pm.get("auto_save", True)):
                return True
        except Exception:
            return True

        if self._parent is None:
            return True

        msg = QMessageBox(self._parent)
        msg.setIcon(QMessageBox.Question)
        msg.setWindowTitle("Save before exiting?")
        msg.setText("Do you want to save changes before quitting?")
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)
        msg.setDefaultButton(QMessageBox.Yes)
        result = msg.exec()

        if result == QMessageBox.Yes:
            success = self.save() if (self._path is not None) else self.save_as()
            return bool(success)
        elif result == QMessageBox.No:
            return True
        else:
            return False

    # ---- Dirty tracking helpers ----
    def mark_dirty(self) -> None:
        self._dirty = True

    def clear_dirty(self) -> None:
        self._dirty = False

    def is_dirty(self) -> bool:
        return bool(self._dirty)
