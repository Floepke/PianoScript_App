# in CONSTANT.py you can find all constants that are used in the application along with the description.
from imports.utils.constants import *

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMenu
from PySide6.QtWidgets import QGraphicsScene
from PySide6.QtWidgets import QSplitter, QVBoxLayout, QWidget, QRadioButton
from PySide6.QtWidgets import QSpinBox
from PySide6.QtWidgets import QLabel, QDockWidget, QTreeView
from PySide6.QtGui import QAction
from PySide6.QtGui import QColor, QBrush
from imports.editor.graphicsview_editor import GraphicsViewEditor
from imports.utils.fileoprations import FileOperations
from imports.engraver.graphics_view_engraver import GraphicsViewEngraver
# import QIcon
from PySide6.QtGui import QIcon
from PySide6.QtGui import QStandardItemModel, QStandardItem

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

        self.menu_bar = self.main.menuBar()
        self.menu_bar.setNativeMenuBar(False)

        # # Create a toolbar
        # self.toolbar = QToolBar(self.main)
        # #self.main.addToolBar(self.toolbar)

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

        # # Create a QToolButton
        # self.file_button = QToolButton(self.main)
        # self.file_button.setText('File')
        # self.file_button.setMenu(self.file_menu)
        # self.file_button.setPopupMode(QToolButton.InstantPopup)

        # add the menu to the mainwindow
        self.menu_bar.addMenu(self.file_menu)
        self.main.setMenuWidget(self.menu_bar)

        # # Add the QToolButton to the QToolBar
        # self.toolbar.addWidget(self.file_button)

        #end menu--------------------------------------------------------------------

        # Create the editor view
        self.editor_scene = QGraphicsScene(self.main)
        self.editor_scene.setBackgroundBrush(QColor(BACKGROUND_COLOR_EDITOR_PRINT))
        self.editor_view = GraphicsViewEditor(self.editor_scene, self.io, self.main)

        # Create the print view
        self.print_scene = QGraphicsScene(self.main)
        self.print_scene.setBackgroundBrush(QColor(BACKGROUND_COLOR_EDITOR_PRINT))
        self.print_view = GraphicsViewEngraver(self.print_scene, self.io, self.main)

        # Create a resizable splitter
        self.splitter = QSplitter(self.main)
        self.splitter.addWidget(self.editor_view)
        self.splitter.addWidget(self.print_view)
        self.splitter.setHandleWidth(20)

        # Set the initial sizes of the widgets in the splitter
        self.splitter.setSizes([10, self.splitter.width()])

        # Set up the main layout
        self.central_widget = QWidget(self.main)
        self.main.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)
        self.layout.addWidget(self.splitter)

        # Create a dockable widget
        self.grid_selector_dock = QDockWidget('Grid Selector', self.main)
        self.grid_selector_dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        # self.grid_selector_dock.setFixedWidth(200)
        self.main.addDockWidget(Qt.LeftDockWidgetArea, self.grid_selector_dock)
        # set stylesheet
        self.grid_selector_dock.setStyleSheet("""background-color: #555555;""")

        # create a layout in the dockable widget
        self.gs_dock_layout = QVBoxLayout()
        
        # Create a QWidget, set the layout on it
        self.gs_dock = QWidget()
        self.gs_dock.setLayout(self.gs_dock_layout)
        self.gs_dock.setMaximumHeight(400)

        # Set the QWidget as the widget for the dock widget
        self.grid_selector_dock.setWidget(self.gs_dock)

        # create label in the dockable widget
        self.grid_selector_label = QLabel('Tick: 128.0')
        self.grid_selector_label.setToolTip('Select the base length of the grid(1=whole 2=half 4=quarter etc)')

        # create a set of radiobuttons for selecting the base length of the grid: 1, 2, 4, 8, 16, 32, 64, 128
        self.radio_layout = QVBoxLayout()
        base_lengths = ['1 Whole', '2 Half', '4 Quarter', '8 Eight', '16 ...', '32', '64', '128']
        for length in base_lengths:
            radio_button = QRadioButton(length)
            self.radio_layout.addWidget(radio_button)
            radio_button.clicked.connect(lambda: self.io['calc'].process_grid())
        self.radio_layout.itemAt(3).widget().setChecked(True)

        # create label in the dockable widget under the listbox
        self.Dlabel = QLabel('divide (÷) by:')
        self.Dlabel.setToolTip('Divide the base length by this number.')

        # create a spinbox in the dockable widget under the listbox
        self.divide_spin_box = QSpinBox()
        self.divide_spin_box.setMaximum(100)
        self.divide_spin_box.setMinimum(1)
        self.divide_spin_box.setValue(1)
        # create a callback function for the spinbox
        self.divide_spin_box.valueChanged.connect(lambda: self.io['calc'].process_grid())

        # create label in the dockable widget under the spinbox
        self.Xlabel = QLabel('multiply (*) by:')
        self.Xlabel.setToolTip('Multiply the base length by this number.')

        # create a spinbox in the dockable widget
        self.multiply_spin_box = QSpinBox()
        self.multiply_spin_box.setMaximum(100)
        self.multiply_spin_box.setMinimum(1)
        self.multiply_spin_box.setValue(1)
        # create a callback function for the spinbox
        self.multiply_spin_box.valueChanged.connect(lambda: self.io['calc'].process_grid())

        # add the widgets to the dockable widget
        self.gs_dock_layout.addWidget(self.grid_selector_label, 0)
        self.gs_dock_layout.addLayout(self.radio_layout)
        self.gs_dock_layout.addWidget(self.Dlabel, 0)
        self.gs_dock_layout.addWidget(self.divide_spin_box, 0)
        self.gs_dock_layout.addWidget(self.Xlabel, 0)
        self.gs_dock_layout.addWidget(self.multiply_spin_box, 0)

        
        # Create a second dockable widget on the left side
        self.tool_dock = QDockWidget('Tool Selector', self.main)
        self.tool_dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        # self.tool_dock.setFixedWidth(200)
        self.main.addDockWidget(Qt.LeftDockWidgetArea, self.tool_dock)
        self.tool_dock.setStyleSheet("""background-color: #555555;""")

        # create a layout in the dockable widget
        self.tool_layout = QVBoxLayout()
        # Create a QWidget, set the layout on it
        self.tool_widget = QWidget()
        self.tool_widget.setLayout(self.tool_layout)
        # Set the QWidget as the widget for the dock widget
        self.tool_dock.setWidget(self.tool_widget)
        # create label in the dockable widget
        self.tool_label = QLabel('Tool: note')
        self.tool_label.setToolTip('Select the tool you want to use.')
        
        # Create a QTreeView and set the model (create_tree_model is defined below)
        self.tree_view = QTreeView()
        self.tree_view.setModel(self.create_tree_model())
        self.tree_view.header().hide()
        self.tree_view.setEditTriggers(QTreeView.NoEditTriggers)
        # set indent size
        self.tree_view.setIndentation(0)
        # set single selection
        self.tree_view.setSelectionMode(QTreeView.SingleSelection)
        # set single click open folder
        self.tree_view.clicked.connect(lambda index: self.tree_view.setExpanded(index, not self.tree_view.isExpanded(index)))
        # set background color
        self.tree_view.setStyleSheet('background-color: #666666; color: #ffffff')
        # Add the tree view to the layout
        # set the folding unfolded
        self.tree_view.expandAll()
        # set color of any selected item
        self.tree_view.setStyleSheet('QTreeView::item:selected {background-color: grey; color: #ffffff}')
        self.tool_layout.addWidget(self.tool_label)
        self.tool_layout.addWidget(self.tree_view)
        

        # self.tool_listbox.currentTextChanged.connect(lambda v: self.io['maineditor'].select_tool(v))

        # add the widgets to the dockable widget
        self.tool_layout.addLayout(self.tool_layout)


    def show(self):
        self.main.show()


    def create_tree_model(self):
        '''
            creates a tree model for the tool selector.
            the tree model is a dictionary where the keys are the folders/category and the values are lists of tools.
            the for loop tries to load an icon from the imports/icons folder with the name of the tool.    
        '''

        # Create a QStandardItemModel
        model = QStandardItemModel()

        tree = {
            'Harmony':[
                'note',
                'ornament',
                ],
            'Layout':[
                'staffsizer',
                'beam'
                ],
            'Phrase':[
                'countline',
                'bpm',
                'slur'
            ],
            'Measure symbols':[
                'pedal',
                'startrepeat',
                'endrepeat',
                'starthook',
                'endhook',
                ]
        }
        for folder in tree:
            # Create a parent item for the first branch
            parent = QStandardItem(folder)
            parent.setBackground(QBrush(QColor("#007aff")))  # Set background color
            parent.setForeground(QBrush(QColor("white")))  # Set foreground (text) color
            parent.setSelectable(False)
            model.appendRow(parent)
            for item in tree[folder]:
                # Create a child item with an icon
                icon = QIcon(f'imports/icons/{item}.png')
                child = QStandardItem(icon, item)
                child.setBackground(QBrush(QColor("white")))  # Set background color
                child.setForeground(QBrush(QColor("black")))  # Set foreground (text) color
                parent.appendRow(child)

        return model

    