# in CONSTANT.py you can find all constants that are used in the application along with the description.
from imports.utils.constants import *

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMenu, QToolButton
from PySide6.QtWidgets import QGraphicsScene, QGraphicsRectItem
from PySide6.QtWidgets import QSplitter, QVBoxLayout, QWidget
from PySide6.QtWidgets import QToolBar, QLineEdit, QSpinBox, QScrollArea
from PySide6.QtWidgets import QLabel, QDockWidget, QListWidget
from PySide6.QtGui import QAction
from PySide6.QtGui import QColor
from imports.editor.graphicsview_editor import GraphicsViewEditor
from imports.utils.fileoprations import FileOperations
from imports.engraver.graphics_view_engraver import GraphicsViewEngraver

BACKGROUND_COLOR = QColor('#eeeeee')

class Gui():
    def __init__(self, main, io):
        self.io = io
        self.main = main
        
        # Set window properties
        self.main.setWindowTitle('PianoScript')
        self.main.setGeometry(100, 100, 800, 600)

        # Create the status bar
        self.statusbar = self.main.statusBar()
        self.statusbar.showMessage(STATUSBAR_DEFAULT_TEXT)

        #start menu--------------------------------------------------------------------

        # Create a toolbar
        self.toolbar = QToolBar(self.main)
        self.main.addToolBar(self.toolbar)

        # Create a QMenu
        self.file_menu = QMenu('File', self.main)

        # Add actions to the QMenu
        self.new_action = QAction('New', self.main)
        self.file_menu.addAction(self.new_action)

        self.load_action = QAction('Load', self.main)
        self.file_menu.addAction(self.load_action)

        self.save_action = QAction('Save', self.main)
        self.file_menu.addAction(self.save_action)

        self.saveas_action = QAction('Save As', self.main)
        self.file_menu.addAction(self.saveas_action)

        self.file_menu.addSeparator()

        self.exit_action = QAction('Exit', self.main)
        self.file_menu.addAction(self.exit_action)

        # Create a QToolButton
        self.file_button = QToolButton(self.main)
        self.file_button.setText('File')
        self.file_button.setMenu(self.file_menu)
        self.file_button.setPopupMode(QToolButton.InstantPopup)

        # Add the QToolButton to the QToolBar
        self.toolbar.addWidget(self.file_button)

        #end menu--------------------------------------------------------------------

        # Create the editor view
        self.editor_scene = QGraphicsScene(self.main)
        self.editor_scene.setBackgroundBrush(BACKGROUND_COLOR)
        self.editor_view = GraphicsViewEditor(self.editor_scene, self.io, self.main)

        # Create the print view
        self.print_scene = QGraphicsScene(self.main)
        self.print_scene.setBackgroundBrush(BACKGROUND_COLOR)
        self.print_view = GraphicsViewEngraver(self.print_scene, self.io, self.main)

        # Create a resizable splitter
        self.splitter = QSplitter(self.main)
        self.splitter.addWidget(self.editor_view)
        self.splitter.addWidget(self.print_view)
        self.splitter.setHandleWidth(20)

        # Set the initial sizes of the widgets in the splitter
        self.splitter.setSizes([1000, self.splitter.width()])

        # Set up the main layout
        self.central_widget = QWidget(self.main)
        self.main.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)
        self.layout.addWidget(self.splitter)

        # Create a dockable widget
        self.dock_widget = QDockWidget('Tool box', self.main)
        self.dock_widget.setStyleSheet('''QDockWidget {border: 1px solid black;}''')
        self.dock_widget.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.dock_widget.setFixedWidth(200)
        self.main.addDockWidget(Qt.LeftDockWidgetArea, self.dock_widget)

        # create a layout in the dockable widget
        self.dock_layout = QVBoxLayout()
        self.dock_widget.setLayout(self.dock_layout)

        # Create a container widget and set the layout to it
        container_widget = QWidget()
        container_widget.setLayout(self.dock_layout)
        container_widget.setMaximumHeight(250)

        # Create a QScrollArea
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)  # Allow the scroll area to resize its contents
        self.scroll.setWidget(container_widget)  # Set the container widget as the contents of the scroll area

        # Set the scroll area as the widget for the dock widget
        self.dock_widget.setWidget(self.scroll)

        # create a listbox in the dockable widget
        self.length_listbox = QListWidget()
        self.length_listbox.addItems(['1', '2', '4', '8', '16', '32', '64', '128'])
        item_height = self.length_listbox.sizeHintForRow(0)
        num_items = self.length_listbox.count()
        self.length_listbox.setMaximumHeight(item_height * num_items)
        # set default value
        self.length_listbox.setCurrentRow(3)
        # create a callback function for the listbox
        self.length_listbox.currentTextChanged.connect(lambda: self.io['calc'].process_grid())

        # create label in the dockable widget under the listbox
        self.Dlabel = QLabel('divide (÷) by:')

        # create a spinbox in the dockable widget under the listbox
        self.divide_spin_box = QSpinBox()
        self.divide_spin_box.setMaximum(100)
        self.divide_spin_box.setMinimum(1)
        self.divide_spin_box.setValue(1)
        # create a callback function for the spinbox
        self.divide_spin_box.valueChanged.connect(lambda: self.io['calc'].process_grid())

        # create label in the dockable widget under the spinbox
        self.Xlabel = QLabel('multiply (*) by:')

        # create a spinbox in the dockable widget
        self.multiply_spin_box = QSpinBox()
        self.multiply_spin_box.setMaximum(100)
        self.multiply_spin_box.setMinimum(1)
        self.multiply_spin_box.setValue(1)
        # create a callback function for the spinbox
        self.multiply_spin_box.valueChanged.connect(lambda: self.io['calc'].process_grid())

        # Add more widgets as needed...

        self.dock_layout.addWidget(self.length_listbox, 0)
        self.dock_layout.addWidget(self.Dlabel, 0)
        self.dock_layout.addWidget(self.divide_spin_box, 0)
        self.dock_layout.addWidget(self.Xlabel, 0)
        self.dock_layout.addWidget(self.multiply_spin_box, 0)

        # Set the container widget to the dockable widget
        self.dock_widget.setWidget(container_widget)

    def show(self):
        self.main.show()

    