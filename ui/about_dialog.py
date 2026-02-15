from __future__ import annotations

from pathlib import Path
from PySide6 import QtCore, QtGui, QtWidgets


class AboutDialog(QtWidgets.QDialog):
    """Shows app licensing and third-party attributions."""

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("About keyTAB")
        self.setModal(True)
        self.setMinimumWidth(420)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(10)

        header = QtWidgets.QLabel(
            """
            <h2 style="margin-bottom: 4px;">keyTAB</h2>
            <div>An alternative music notation editor.</div>
            """
        )
        header.setTextFormat(QtCore.Qt.TextFormat.RichText)
        header.setWordWrap(True)
        header.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeft | QtCore.Qt.AlignmentFlag.AlignTop)
        layout.addWidget(header)

        body = QtWidgets.QLabel(self._credits_html())
        body.setTextFormat(QtCore.Qt.TextFormat.RichText)
        body.setOpenExternalLinks(True)
        body.setWordWrap(True)
        layout.addWidget(body)

        btns = QtWidgets.QDialogButtonBox(self)
        btns.setStandardButtons(QtWidgets.QDialogButtonBox.StandardButton.Close)

        open_notices_btn = QtWidgets.QPushButton("Open third-party notices")
        open_notices_btn.clicked.connect(self._open_third_party_notices)
        btns.addButton(open_notices_btn, QtWidgets.QDialogButtonBox.ButtonRole.ActionRole)

        open_licenses_btn = QtWidgets.QPushButton("Open licenses folder")
        open_licenses_btn.clicked.connect(self._open_license_folder)
        btns.addButton(open_licenses_btn, QtWidgets.QDialogButtonBox.ButtonRole.ActionRole)

        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def _credits_html(self) -> str:
        return (
            """
            <p><b>Project license:</b> MIT License.</p>
            <p><b>Credits and third-party components:</b></p>
            <ul style="margin-top: 4px;">
                <li>User-provided SoundFont (.sf2/.sf3).</li>
                <li>FluidSynth — LGPL-2.1-or-later.</li>
                <li>PySide6 / Qt — LGPL-3.0.</li>
                <li>pretty_midi, mido, python-rtmidi, numpy — permissive licenses.</li>
            </ul>
            <p>See the bundled license texts and THIRD_PARTY_NOTICES for details.</p>
            """
        )

    def _open_third_party_notices(self) -> None:
        path = self._root_path() / "THIRD_PARTY_NOTICES.md"
        self._open_path(path)

    def _open_license_folder(self) -> None:
        path = self._root_path() / "licenses"
        self._open_path(path)

    def _root_path(self) -> Path:
        return Path(__file__).resolve().parent.parent

    def _open_path(self, path: Path) -> None:
        try:
            if path.exists():
                QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(str(path)))
        except Exception:
            pass
