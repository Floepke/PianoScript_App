from __future__ import annotations

from PySide6 import QtCore, QtGui, QtWidgets

from file_model.header import Header, HeaderText, FontSpec


class FontEditor(QtWidgets.QWidget):
    def __init__(self, value: FontSpec, parent=None) -> None:
        super().__init__(parent)
        self._combo = QtWidgets.QFontComboBox(self)
        self._size = QtWidgets.QSpinBox(self)
        self._size.setRange(1, 200)
        self._bold = QtWidgets.QCheckBox("Bold", self)
        self._italic = QtWidgets.QCheckBox("Italic", self)
        self._choose = QtWidgets.QPushButton("Choose...", self)

        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        layout.addWidget(self._combo, 1)
        layout.addWidget(self._size, 0)
        layout.addWidget(self._bold, 0)
        layout.addWidget(self._italic, 0)
        layout.addWidget(self._choose, 0)

        self.set_value(value)
        self._choose.clicked.connect(self._open_dialog)

    def set_value(self, value: FontSpec) -> None:
        try:
            self._combo.setCurrentFont(QtGui.QFont(str(value.family)))
        except Exception:
            pass
        try:
            self._size.setValue(int(value.size_pt))
        except Exception:
            self._size.setValue(10)
        self._bold.setChecked(bool(value.bold))
        self._italic.setChecked(bool(value.italic))

    def value(self) -> FontSpec:
        return FontSpec(
            family=str(self._combo.currentFont().family()),
            size_pt=float(self._size.value()),
            bold=bool(self._bold.isChecked()),
            italic=bool(self._italic.isChecked()),
        )

    def _open_dialog(self) -> None:
        cur = QtGui.QFont(self._combo.currentFont())
        cur.setPointSize(int(self._size.value()))
        cur.setBold(bool(self._bold.isChecked()))
        cur.setItalic(bool(self._italic.isChecked()))
        ok, font = QtWidgets.QFontDialog.getFont(cur, self)
        if not ok:
            return
        try:
            self._combo.setCurrentFont(font)
        except Exception:
            pass
        self._size.setValue(int(font.pointSize()))
        self._bold.setChecked(bool(font.bold()))
        self._italic.setChecked(bool(font.italic()))


class HeaderDialog(QtWidgets.QDialog):
    def __init__(self, parent=None, header: Header | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Header")
        self.setModal(True)
        self.setWindowModality(QtCore.Qt.NonModal)

        self._header = header or Header()

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        form = QtWidgets.QFormLayout()
        form.setContentsMargins(0, 0, 0, 0)
        form.setSpacing(6)
        layout.addLayout(form)

        self._title_text = QtWidgets.QLineEdit(self)
        self._title_text.setText(str(self._header.title.text))
        self._title_font = FontEditor(self._header.title, self)
        self._title_x = QtWidgets.QDoubleSpinBox(self)
        self._title_y = QtWidgets.QDoubleSpinBox(self)
        for sb in (self._title_x, self._title_y):
            sb.setDecimals(2)
            sb.setRange(-1000000.0, 1000000.0)
        self._title_x.setValue(float(getattr(self._header.title, 'x_offset_mm', 0.0) or 0.0))
        self._title_y.setValue(float(getattr(self._header.title, 'y_offset_mm', 0.0) or 0.0))
        form.addRow(QtWidgets.QLabel("Title text:", self), self._title_text)
        form.addRow(QtWidgets.QLabel("Title font:", self), self._title_font)
        form.addRow(QtWidgets.QLabel("Title x offset (mm):", self), self._title_x)
        form.addRow(QtWidgets.QLabel("Title y offset (mm):", self), self._title_y)

        self._composer_text = QtWidgets.QLineEdit(self)
        self._composer_text.setText(str(self._header.composer.text))
        self._composer_font = FontEditor(self._header.composer, self)
        self._composer_x = QtWidgets.QDoubleSpinBox(self)
        self._composer_y = QtWidgets.QDoubleSpinBox(self)
        for sb in (self._composer_x, self._composer_y):
            sb.setDecimals(2)
            sb.setRange(-1000000.0, 1000000.0)
        self._composer_x.setValue(float(getattr(self._header.composer, 'x_offset_mm', 0.0) or 0.0))
        self._composer_y.setValue(float(getattr(self._header.composer, 'y_offset_mm', 0.0) or 0.0))
        form.addRow(QtWidgets.QLabel("Composer text:", self), self._composer_text)
        form.addRow(QtWidgets.QLabel("Composer font:", self), self._composer_font)
        form.addRow(QtWidgets.QLabel("Composer x offset (mm):", self), self._composer_x)
        form.addRow(QtWidgets.QLabel("Composer y offset (mm):", self), self._composer_y)

        self._copyright_text = QtWidgets.QLineEdit(self)
        self._copyright_text.setText(str(self._header.copyright.text))
        self._copyright_font = FontEditor(self._header.copyright, self)
        self._copyright_x = QtWidgets.QDoubleSpinBox(self)
        self._copyright_y = QtWidgets.QDoubleSpinBox(self)
        for sb in (self._copyright_x, self._copyright_y):
            sb.setDecimals(2)
            sb.setRange(-1000000.0, 1000000.0)
        self._copyright_x.setValue(float(getattr(self._header.copyright, 'x_offset_mm', 0.0) or 0.0))
        self._copyright_y.setValue(float(getattr(self._header.copyright, 'y_offset_mm', 0.0) or 0.0))
        form.addRow(QtWidgets.QLabel("Copyright text:", self), self._copyright_text)
        form.addRow(QtWidgets.QLabel("Copyright font:", self), self._copyright_font)
        form.addRow(QtWidgets.QLabel("Copyright x offset (mm):", self), self._copyright_x)
        form.addRow(QtWidgets.QLabel("Copyright y offset (mm):", self), self._copyright_y)

        self._msg = QtWidgets.QLabel("", self)
        pal = self._msg.palette()
        pal.setColor(self._msg.foregroundRole(), QtCore.Qt.GlobalColor.red)
        self._msg.setPalette(pal)
        layout.addWidget(self._msg)

        self._buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel,
            parent=self,
        )
        self._buttons.accepted.connect(self._on_accept_clicked)
        self._buttons.rejected.connect(self.reject)
        layout.addWidget(self._buttons)

    def _on_accept_clicked(self) -> None:
        try:
            _ = self.get_values()
        except Exception:
            self._msg.setText("Invalid header values.")
            return
        self._msg.setText("")
        self.accept()

    def get_values(self) -> Header:
        title_font = self._title_font.value()
        composer_font = self._composer_font.value()
        copyright_font = self._copyright_font.value()
        title = HeaderText(
            text=str(self._title_text.text()),
            family=title_font.family,
            size_pt=title_font.size_pt,
            bold=title_font.bold,
            italic=title_font.italic,
            x_offset_mm=float(self._title_x.value()),
            y_offset_mm=float(self._title_y.value()),
        )
        composer = HeaderText(
            text=str(self._composer_text.text()),
            family=composer_font.family,
            size_pt=composer_font.size_pt,
            bold=composer_font.bold,
            italic=composer_font.italic,
            x_offset_mm=float(self._composer_x.value()),
            y_offset_mm=float(self._composer_y.value()),
        )
        copyright_text = HeaderText(
            text=str(self._copyright_text.text()),
            family=copyright_font.family,
            size_pt=copyright_font.size_pt,
            bold=copyright_font.bold,
            italic=copyright_font.italic,
            x_offset_mm=float(self._copyright_x.value()),
            y_offset_mm=float(self._copyright_y.value()),
        )
        return Header(title=title, composer=composer, copyright=copyright_text)
