from __future__ import annotations

from pathlib import Path
from typing import Optional, Tuple
import os
import sys
from datetime import datetime

from PySide6.QtWidgets import QFileDialog, QMessageBox, QWidget

from file_model.SCORE import SCORE
from utils.CONSTANT import UTILS_SAVE_DIR


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
        return self._current

    def replace_current(self, new_score: SCORE) -> None:
        """Replace the current SCORE instance (used by undo/redo)."""
        self._current = new_score
        # Autosave on any model replacement (e.g., undo/redo application)
        self.autosave_current()

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
            return True
        except Exception as exc:
            self._show_error("Failed to save score", f"{exc}")
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
        """Save the current SCORE to the user's autosave file."""
        target = Path(UTILS_SAVE_DIR) / "pianoscript_prev_session.piano"
        self._current.save(str(target))

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
