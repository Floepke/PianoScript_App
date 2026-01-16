from PySide6 import QtCore, QtGui, QtWidgets
from icons.icons import get_qicon


class ToolbarHandle(QtWidgets.QSplitterHandle):
    def __init__(self, orientation, parent):
        super().__init__(orientation, parent)
        self.setObjectName("ToolbarHandle")
        parent.setHandleWidth(50)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        # Square button size to match ToolSelector list row height
        self._button_size = 35
        # Default toolbar (top to bottom): fit, next, previous, engrave, play, stop
        self.fit_btn = QtWidgets.QToolButton(self)
        ic = get_qicon('fit', size=(64, 64))
        if ic:
            self.fit_btn.setIcon(ic)
        else:
            self.fit_btn.setText("Fit")
        self.fit_btn.setIconSize(QtCore.QSize(self._button_size - 6, self._button_size - 6))
        self.fit_btn.setFixedSize(self._button_size, self._button_size)
        layout.addWidget(self.fit_btn)
        try:
            self.fit_btn.clicked.connect(parent.fitRequested.emit)
        except Exception:
            pass

        self.next_btn = QtWidgets.QToolButton(self)
        icn = get_qicon('next', size=(64, 64))
        if icn:
            self.next_btn.setIcon(icn)
        self.next_btn.setIconSize(QtCore.QSize(self._button_size - 6, self._button_size - 6))
        self.next_btn.setFixedSize(self._button_size, self._button_size)
        layout.addWidget(self.next_btn)
        try:
            self.next_btn.clicked.connect(parent.nextRequested.emit)
        except Exception:
            pass

        self.prev_btn = QtWidgets.QToolButton(self)
        icp = get_qicon('previous', size=(64, 64))
        if icp:
            self.prev_btn.setIcon(icp)
        self.prev_btn.setIconSize(QtCore.QSize(self._button_size - 6, self._button_size - 6))
        self.prev_btn.setFixedSize(self._button_size, self._button_size)
        layout.addWidget(self.prev_btn)
        try:
            self.prev_btn.clicked.connect(parent.previousRequested.emit)
        except Exception:
            pass

        self.engrave_btn = QtWidgets.QToolButton(self)
        ice = get_qicon('engrave', size=(64, 64))
        if ice:
            self.engrave_btn.setIcon(ice)
        self.engrave_btn.setIconSize(QtCore.QSize(self._button_size - 6, self._button_size - 6))
        self.engrave_btn.setFixedSize(self._button_size, self._button_size)
        layout.addWidget(self.engrave_btn)
        try:
            self.engrave_btn.clicked.connect(parent.engraveRequested.emit)
        except Exception:
            pass

        self.play_btn = QtWidgets.QToolButton(self)
        icplay = get_qicon('play', size=(64, 64))
        if icplay:
            self.play_btn.setIcon(icplay)
        self.play_btn.setIconSize(QtCore.QSize(self._button_size - 6, self._button_size - 6))
        self.play_btn.setFixedSize(self._button_size, self._button_size)
        layout.addWidget(self.play_btn)
        try:
            self.play_btn.clicked.connect(parent.playRequested.emit)
        except Exception:
            pass

        self.stop_btn = QtWidgets.QToolButton(self)
        icstop = get_qicon('stop', size=(64, 64))
        if icstop:
            self.stop_btn.setIcon(icstop)
        self.stop_btn.setIconSize(QtCore.QSize(self._button_size - 6, self._button_size - 6))
        self.stop_btn.setFixedSize(self._button_size, self._button_size)
        layout.addWidget(self.stop_btn)
        try:
            self.stop_btn.clicked.connect(parent.stopRequested.emit)
        except Exception:
            pass

        # Visual separator between default toolbar and contextual toolbar
        sep = QtWidgets.QFrame(self)
        sep.setFrameShape(QtWidgets.QFrame.Shape.HLine)
        sep.setFrameShadow(QtWidgets.QFrame.Shadow.Sunken)
        layout.addWidget(sep)

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
            ic = get_qicon(icon_name, size=(64, 64))
            if ic:
                btn.setIcon(ic)
            btn.setToolTip(tooltip)
            btn.setIconSize(QtCore.QSize(self._button_size - 6, self._button_size - 6))
            btn.setFixedSize(self._button_size, self._button_size)
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
    # Default toolbar actions
    nextRequested = QtCore.Signal()
    previousRequested = QtCore.Signal()
    engraveRequested = QtCore.Signal()
    playRequested = QtCore.Signal()
    stopRequested = QtCore.Signal()

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
