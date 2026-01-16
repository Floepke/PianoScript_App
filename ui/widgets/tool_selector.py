from __future__ import annotations
from PySide6 import QtCore, QtGui, QtWidgets
from icons.icons import get_qicon

TOOL_ITEMS = [
    ('note', 'note'),
    ('grace_note', 'grace_note'),
    ('count_line', 'count_line'),
    ('line_break', 'line_break'),
    ('beam', 'beam'),
    #('pedal', 'pedal'),
    ('slur', 'slur'),
    ('start_repeat', 'repeats'),
    ('end_repeat', 'repeats'),
    ('text', 'text'),
]


class ToolSelectorWidget(QtWidgets.QListWidget):
    toolSelected = QtCore.Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        # Icon size reduced by a quarter from 48 -> 36
        self.setIconSize(QtCore.QSize(36, 36))
        self.setUniformItemSizes(True)
        self.setSpacing(4)
        # Fill available dock width and avoid extra inner borders/scrollbars
        self.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding,
                           QtWidgets.QSizePolicy.Policy.Preferred)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
        # Remove any inner margins to match Snap Size listbox appearance
        self.setContentsMargins(0, 0, 0, 0)
        self.setViewportMargins(0, 0, 0, 0)
        self.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)
        self.itemSelectionChanged.connect(self._emit_selected)
        self._populate()

    def _emit_selected(self) -> None:
        items = self.selectedItems()
        if items:
            name = items[0].data(QtCore.Qt.ItemDataRole.UserRole)
            if isinstance(name, str):
                self.toolSelected.emit(name)

    def _populate(self) -> None:
        self.clear()
        for tool_name, icon_name in TOOL_ITEMS:
            # Request high-DPI crisp icon at 36x36 CSS pixels
            icon = get_qicon(icon_name, size=(36, 36)) or QtGui.QIcon()
            it = QtWidgets.QListWidgetItem(icon, tool_name.replace('_', ' ').capitalize())
            it.setData(QtCore.Qt.ItemDataRole.UserRole, tool_name)
            # Make row height comfortably fit the 36px icon + padding
            it.setSizeHint(QtCore.QSize(it.sizeHint().width(), 42))
            self.addItem(it)
        # Select 'note' tool initially (visually and functionally)
        for i in range(self.count()):
            it = self.item(i)
            if it.data(QtCore.Qt.ItemDataRole.UserRole) == 'note':
                self.setCurrentItem(it)
                # Emit selection to update editor
                self._emit_selected()
                break


class ToolSelectorDock(QtWidgets.QDockWidget):
    def __init__(self, parent=None):
        super().__init__("Tools", parent)
        self.setObjectName("ToolSelectorDock")
        self.setAllowedAreas(QtCore.Qt.DockWidgetArea.LeftDockWidgetArea | QtCore.Qt.DockWidgetArea.RightDockWidgetArea)
        self.setFeatures(QtWidgets.QDockWidget.DockWidgetFeature.DockWidgetMovable |
                         QtWidgets.QDockWidget.DockWidgetFeature.DockWidgetFloatable)
        # Wrap the list in a container with small margins to match Snap Size indent
        container = QtWidgets.QWidget(self)
        lay = QtWidgets.QVBoxLayout(container)
        lay.setContentsMargins(6, 6, 6, 6)
        lay.setSpacing(6)
        self.selector = ToolSelectorWidget(container)
        lay.addWidget(self.selector)
        self.setWidget(container)
        try:
            self.selector.toolSelected.connect(self._on_tool_selected_update_title)
        except Exception:
            pass

    def showEvent(self, ev: QtGui.QShowEvent) -> None:
        super().showEvent(ev)
        try:
            self.adjust_to_fit()
            self._update_title()
        except Exception:
            pass

    def adjust_to_fit(self) -> None:
        """Lock only the dock width (match Snap Size dock) and
        ensure the list spans the full dock width. Height is left
        unmanaged per UI preference.
        """
        try:
            lst = self.selector
            # Ensure the list uses the full available dock width
            lst.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding,
                              QtWidgets.QSizePolicy.Policy.Preferred)

            # Lock width to match the Snap Size dock width, if available
            snap_w = self.width()
            mw = self.parent()
            try:
                if hasattr(mw, 'snap_dock') and isinstance(mw.snap_dock, QtWidgets.QDockWidget):
                    snap_w = int(mw.snap_dock.width())
            except Exception:
                pass
            if snap_w > 0:
                self.setMinimumWidth(snap_w)
                self.setMaximumWidth(snap_w)
        except Exception:
            pass

    def _on_tool_selected_update_title(self, name: str) -> None:
        self._update_title()

    def _update_title(self) -> None:
        try:
            # Reflect current selection in the title bar
            items = self.selector.selectedItems()
            if items:
                name = items[0].data(QtCore.Qt.ItemDataRole.UserRole)
                label = str(items[0].text())
                self.setWindowTitle(f"Tool: {label}")
            else:
                self.setWindowTitle("Tool: (none)")
        except Exception:
            pass
