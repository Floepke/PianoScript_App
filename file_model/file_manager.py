from __future__ import annotations

from pathlib import Path
from typing import Optional, Tuple
import os
import sys
from datetime import datetime

from PySide6.QtWidgets import QFileDialog, QMessageBox, QWidget

from file_model.SCORE import SCORE
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

    FILE_FILTER = "PianoScript Score (*.piano);;All Files (*)"

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        self._parent: Optional[QWidget] = parent
        self._current: SCORE = SCORE().new()
        self._path: Optional[Path] = None
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
        self._path = None
        self._dirty = False
        return self._current

    def replace_current(self, new_score: SCORE) -> None:
        """Replace the current SCORE instance (used by undo/redo)."""
        self._current = new_score
        # Autosave on any model replacement (e.g., undo/redo application)
        self.autosave_current()
        # Consider undo/redo a model change relative to last explicit save
        self._dirty = True

    def open(self) -> Optional[SCORE]:
        """Open a .piano file via a native file dialog and load into SCORE."""
        start_dir = str(self._path.parent if self._path else self._last_dir)
        fname, _ = QFileDialog.getOpenFileName(
            self._parent,
            "Open Score",
            start_dir,
            self.FILE_FILTER,
        )
        if not fname:
            return None
        try:
            self._current = SCORE().load(fname)
            self._path = Path(fname)
            self._last_dir = self._path.parent
            self._dirty = False
            # Track last opened file in appdata
            try:
                adm = get_appdata_manager()
                adm.set("last_opened_file", str(self._path))
                adm.save()
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
            self._current = SCORE().load(path)
            self._path = Path(path)
            self._last_dir = self._path.parent
            self._dirty = False
            try:
                adm = get_appdata_manager()
                adm.set("last_opened_file", str(self._path))
                adm.save()
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
            self.FILE_FILTER,
        )
        if not fname:
            return False
        target = self._ensure_piano_suffix(Path(fname))
        try:
            self._current.save(str(target))
            self._path = target
            self._last_dir = target.parent
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
    def confirm_save_for_action(self, action_description: str) -> bool:
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

        # If auto-save is enabled, skip prompting and proceed
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
