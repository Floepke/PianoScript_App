from PySide6 import QtCore, QtGui, QtWidgets
from icons.icons import get_qicon


class ToolbarHandle(QtWidgets.QSplitterHandle):
    def __init__(self, orientation, parent):
        super().__init__(orientation, parent)
        self.setObjectName("ToolbarHandle")
        parent.setHandleWidth(56)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        # Single 'Fit' button to snap the print view to fit the page exactly.
        self.fit_btn = QtWidgets.QToolButton(self)
        icon = get_qicon('fit', size=(64, 64))
        if icon:
            self.fit_btn.setIcon(icon)
        self.fit_btn.setToolButtonStyle(QtCore.Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.fit_btn.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding,
                                   QtWidgets.QSizePolicy.Policy.Fixed)
        layout.addWidget(self.fit_btn)
        # Emit the splitter's fitRequested signal when clicked
        try:
            self.fit_btn.clicked.connect(parent.fitRequested.emit)
        except Exception:
            pass

        # Contextual tool area managed by ToolManager
        self._toolbar_area = QtWidgets.QWidget(self)
        self._toolbar_layout = QtWidgets.QVBoxLayout(self._toolbar_area)
        self._toolbar_layout.setContentsMargins(0, 0, 0, 0)
        self._toolbar_layout.setSpacing(6)
        layout.addWidget(self._toolbar_area)
        layout.addStretch(1)

        self.setStyleSheet(
            "#ToolbarHandle { background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #3a3f44, stop:1 #2b2f33); }"
        )

    def set_buttons(self, defs: list[dict]):
        # Clear previous buttons
        while self._toolbar_layout.count():
            item = self._toolbar_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
        # Add new buttons
        for d in defs or []:
            name = d.get('name', '')
            icon_name = d.get('icon', '')
            tooltip = d.get('tooltip', name)
            btn = QtWidgets.QToolButton(self._toolbar_area)
            ic = get_qicon(icon_name, size=(32, 32))
            if ic:
                btn.setIcon(ic)
            btn.setToolTip(tooltip)
            btn.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding,
                              QtWidgets.QSizePolicy.Policy.Fixed)
            # Emit contextButtonClicked(name) from parent splitter
            try:
                btn.clicked.connect(lambda _=False, n=name: self.parent().contextButtonClicked.emit(n))
            except Exception:
                pass
            self._toolbar_layout.addWidget(btn)


class ToolbarSplitter(QtWidgets.QSplitter):
    # External trigger to request a fit action
    fitRequested = QtCore.Signal()
    # ToolManager contextual toolbar button clicked
    contextButtonClicked = QtCore.Signal(str)

    def __init__(self, orientation: QtCore.Qt.Orientation, parent=None):
        super().__init__(orientation, parent)
        assert orientation == QtCore.Qt.Orientation.Horizontal, \
            "ToolbarSplitter is intended for horizontal orientation"
        # Allow dragging the sash to fully collapse either child
        self.setChildrenCollapsible(True)
        self.setHandleWidth(56)

    def createHandle(self):
        h = ToolbarHandle(self.orientation(), self)
        # Keep a reference for ToolManager to update contextual buttons
        try:
            self._handle = h
        except Exception:
            pass
        return h

    def set_context_buttons(self, defs: list[dict]):
        try:
            if hasattr(self, '_handle') and self._handle is not None:
                self._handle.set_buttons(defs)
        except Exception:
            pass
