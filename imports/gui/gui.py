# in CONSTANT.py you can find all constants that are used in the application along with the description.
from PySide6.QtCore import Qt, QSize, QPoint
from PySide6.QtWidgets import QMenu, QSlider, QGraphicsScene
from PySide6.QtWidgets import QSplitter, QVBoxLayout, QHBoxLayout, QWidget, QRadioButton
from PySide6.QtWidgets import QSpinBox, QLabel, QDockWidget, QTreeView
from PySide6.QtGui import QAction, QColor, QBrush, QStandardItemModel, QStandardItem

from imports.editor.graphicsview_editor import GraphicsViewEditor
from imports.engraver.graphics_view_engraver import GraphicsViewEngraver
from imports.gui.dialogs.scoreoptionsdialog import ScoreOptionsDialog
from imports.engraver.pdfexport import pdf_export
from imports.icons.icons import get_icon
from imports.gui.toolbar import ToolBar
from imports.gui.moodslider import MoodSlider
from imports.utils.constants import *
from imports.gui.dialogs.filebrowser import FileBrowser
from imports.gui.clock import Clock

import random
from PySide6.QtWidgets import QSizePolicy


class Gui():
    def __init__(self, main, io):
        self.io = io
        self.main = main

        # Set window properties
        self.main.setWindowTitle('PianoScript')
        self.main.setGeometry(250, 200, 2000, 1000)
        self.main.showMaximized()

        # Create the status bar
        self.statusbar = self.main.statusBar()

        # Create a slider
        self.slider = MoodSlider(Qt.Horizontal, self.main)
        self.slider.setMinimum(0)
        self.slider.setMaximum(255)
        self.slider.setValue(random.randint(0, 255))

        # add a label
        self.label = QLabel()
        self.label.setText(str('Mood Slider ='))
        self.label.setStyleSheet(
            'color: white; font-family: Edwin; font-size: 14px;')

        # Create a layout and add the label and slider to it
        self.slider_layout = QHBoxLayout()
        self.slider_layout.addWidget(self.label)
        self.slider_layout.addWidget(self.slider)

        # Create a widget with the layout and add it to the status bar
        self.slider_widget = QWidget()
        self.slider_widget.setLayout(self.slider_layout)
        self.statusbar.addPermanentWidget(self.slider_widget)
        self.statusbar.addPermanentWidget(Clock())

        # start menu--------------------------------------------------------------------

        self.menu_bar = self.main.menuBar()
        self.menu_bar.setNativeMenuBar(False)

        # Create a File menu
        self.file_menu = QMenu('File', self.main)
        self.new_action = QAction('New', self.main)
        self.new_action.setShortcut('Ctrl+N')
        self.file_menu.addAction(self.new_action)
        self.load_action = QAction('Load', self.main)
        self.load_action.setShortcut('Ctrl+O')
        self.file_menu.addAction(self.load_action)

        # Create the "Recent Files" menu
        self.recent_file_menu = QMenu('Recent Files', self.main)
        self.file_menu.addMenu(self.recent_file_menu)

        self.clear_recent_action = QAction('Clear Recent Files', self.main)
        self.recent_file_menu.addAction(self.clear_recent_action)
        self.recent_file_menu.addSeparator()

        self.import_midi_action = QAction('Load MIDI', self.main)
        self.import_midi_action.setShortcut('Ctrl+I')
        self.import_midi_action.triggered.connect(
            lambda: self.io['fileoperations'].import_midi())
        self.file_menu.addAction(self.import_midi_action)
        self.file_menu.addSeparator()
        self.save_action = QAction('Save', self.main)
        self.save_action.setShortcut('Ctrl+S')
        self.file_menu.addAction(self.save_action)
        self.saveas_action = QAction('Save As', self.main)
        self.saveas_action.setShortcut('Ctrl+Shift+S')
        self.file_menu.addAction(self.saveas_action)
        self.save_template_action = QAction(
            'Set As Default Template...', self.main)
        self.file_menu.addAction(self.save_template_action)

        self.file_menu.addSeparator()

        self.autosave_action = QAction('Autosave', self.main)
        self.autosave_action.setCheckable(True)
        self.autosave_action.setChecked(True)
        self.file_menu.addAction(self.autosave_action)

        self.file_menu.addSeparator()

        self.pdf_export_action = QAction('Export PDF', self.main)
        self.pdf_export_action.triggered.connect(lambda: pdf_export(self.io))
        self.file_menu.addAction(self.pdf_export_action)

        self.mid_export_action = QAction('Export MIDI', self.main)
        self.mid_export_action.triggered.connect(
            lambda: self.io['midi'].export_midi())
        self.file_menu.addAction(self.mid_export_action)

        self.file_menu.addSeparator()
        self.exit_action = QAction('Exit', self.main)
        self.exit_action.setShortcut('Ctrl+Q')
        self.file_menu.addAction(self.exit_action)
        self.menu_bar.addMenu(self.file_menu)
        self.main.setMenuWidget(self.menu_bar)

        # Create an Edit menu
        self.edit_menu = QMenu('Edit', self.main)
        self.undo_action = QAction('Undo', self.main)
        self.edit_menu.addAction(self.undo_action)
        self.redo_action = QAction('Redo', self.main)
        self.edit_menu.addAction(self.redo_action)
        self.edit_menu.addSeparator()
        self.cut_action = QAction('Cut', self.main)
        self.edit_menu.addAction(self.cut_action)
        self.copy_action = QAction('Copy', self.main)
        self.edit_menu.addAction(self.copy_action)
        self.paste_action = QAction('Paste', self.main)
        self.edit_menu.addAction(self.paste_action)
        self.menu_bar.addMenu(self.edit_menu)

        # Create a View menu
        self.view_menu = QMenu('View', self.main)
        self.zoom_in_action = QAction('Zoom In', self.main)
        self.view_menu.addAction(self.zoom_in_action)
        self.zoom_out_action = QAction('Zoom Out', self.main)
        self.view_menu.addAction(self.zoom_out_action)
        self.menu_bar.addMenu(self.view_menu)
        self.view_menu.addSeparator()

        self.toggle_grid_selector_dock_action = QAction(
            'Grid Selector', self.main)
        self.toggle_grid_selector_dock_action.setCheckable(True)
        self.toggle_grid_selector_dock_action.setChecked(True)
        self.toggle_grid_selector_dock_action.triggered.connect(
            lambda: self.grid_selector_dock.setVisible(not self.grid_selector_dock.isVisible()))
        self.view_menu.addAction(self.toggle_grid_selector_dock_action)

        self.toggle_tool_dock_action = QAction('Tool Selector', self.main)
        self.toggle_tool_dock_action.setCheckable(True)
        self.toggle_tool_dock_action.setChecked(True)
        self.toggle_tool_dock_action.triggered.connect(
            lambda: self.tool_dock.setVisible(not self.tool_dock.isVisible()))
        self.view_menu.addAction(self.toggle_tool_dock_action)

        self.toggle_file_dock_action = QAction('File Browser', self.main)
        self.toggle_file_dock_action.setCheckable(True)
        self.toggle_file_dock_action.setChecked(True)
        self.toggle_file_dock_action.triggered.connect(
            lambda: self.file_dock.setVisible(not self.file_dock.isVisible()))
        self.view_menu.addAction(self.toggle_file_dock_action)

        # Create a Settings menu
        self.settings_menu = QMenu('Settings', self.main)
        self.grid_edit_action = QAction('Grid Editor', self.main)
        self.grid_edit_action.setShortcut('g')
        self.settings_menu.addAction(self.grid_edit_action)
        self.line_break_editor_action = QAction('Line break Editor', self.main)
        self.line_break_editor_action.setShortcut('l')
        self.settings_menu.addAction(self.line_break_editor_action)
        self.score_options_action = QAction('Score Options', self.main)
        self.score_options_action.setShortcut('s')
        self.score_options_action.triggered.connect(
            lambda: ScoreOptionsDialog(self.io).exec())
        self.settings_menu.addAction(self.score_options_action)
        self.settings_menu.addSeparator()
        self.auto_engrave_action = QAction('Auto engrave', self.main)
        self.auto_engrave_action.setCheckable(True)
        self.auto_engrave_action.setChecked(True)
        self.settings_menu.addAction(self.auto_engrave_action)
        self.menu_bar.addMenu(self.settings_menu)
        self.set_midi_out_port_action = QAction('Set MIDI out port', self.main)
        self.settings_menu.addAction(self.set_midi_out_port_action)

        self.pianoscripts_menu = QMenu('Scripts', self.main)
        self.menu_bar.addMenu(self.pianoscripts_menu)

        # end menu--------------------------------------------------------------------

        # Create the editor view
        self.editor_scene = QGraphicsScene(self.main)
        self.editor_scene.setBackgroundBrush(QColor(BACKGROUND_COLOR))
        self.editor_view = GraphicsViewEditor(
            self.editor_scene, self.io, self.main)
        # set minimum width of the editor
        # self.editor_view.setMinimumWidth(400)
        # Set the focus policy to Qt.StrongFocus to accept focus by tabbing and clicking
        self.editor_view.setFocusPolicy(Qt.StrongFocus)

        # Set the focus to the editor view
        self.editor_view.setFocus()

        # Create the print view
        self.print_scene = QGraphicsScene(self.main)
        self.print_scene.setBackgroundBrush(QColor(BACKGROUND_COLOR))
        self.print_view = GraphicsViewEngraver(
            self.print_scene, self.io, self.main)

        # Create the toolbar
        self.toolbar_widget = QWidget()
        self.toolbar_widget.setFixedWidth(30)
        self.toolbar = ToolBar(self.io)
        self.toolbar_layout = QVBoxLayout()
        self.toolbar_layout.addWidget(self.toolbar)
        self.toolbar_layout.setContentsMargins(0, 0, 0, 0)
        self.toolbar_widget.setLayout(self.toolbar_layout)

        # Create a resizable splitter
        self.splitter = QSplitter(self.main)
        self.splitter.addWidget(self.editor_view)
        self.splitter.addWidget(self.toolbar_widget)
        self.splitter.addWidget(self.print_view)
        self.splitter.setHandleWidth(10)

        # Set the initial sizes of the widgets in the splitter
        main_window_width = self.main.frameGeometry().width()
        middle_position = main_window_width // 2
        self.splitter.setSizes([middle_position, 30, middle_position])

        # Set up the main layout
        self.central_widget = QWidget(self.main)
        self.central_widget.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.main.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)
        self.layout.addWidget(self.splitter)

        # Create a dockable widget
        self.grid_selector_dock = QDockWidget('Grid Selector', self.main)
        self.grid_selector_dock.setAllowedAreas(
            Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea | Qt.BottomDockWidgetArea | Qt.TopDockWidgetArea)
        self.grid_selector_dock.setObjectName('ToolDock')
        self.main.addDockWidget(Qt.LeftDockWidgetArea, self.grid_selector_dock)

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
        self.grid_selector_label.setToolTip(
            'Select the base length of the grid(1=whole 2=half 4=quarter etc)')

        # create a set of radiobuttons for selecting the base length of the grid: 1, 2, 4, 8, 16, 32, 64, 128
        self.radio_layout = QVBoxLayout()
        base_lengths = ['1 Whole', '2 Half', '4 Quarter',
                        '8 Eight', '16 ...', '32', '64', '128']
        for length in base_lengths:
            radio_button = QRadioButton(length)
            self.radio_layout.addWidget(radio_button)
            radio_button.clicked.connect(
                lambda: self.io['calc'].process_grid())
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
        self.divide_spin_box.valueChanged.connect(
            lambda: self.io['calc'].process_grid())

        # create label in the dockable widget under the spinbox
        self.Xlabel = QLabel('multiply (*) by:')
        self.Xlabel.setToolTip('Multiply the base length by this number.')

        # create a spinbox in the dockable widget
        self.multiply_spin_box = QSpinBox()
        self.multiply_spin_box.setMaximum(100)
        self.multiply_spin_box.setMinimum(1)
        self.multiply_spin_box.setValue(1)
        # create a callback function for the spinbox
        self.multiply_spin_box.valueChanged.connect(
            lambda: self.io['calc'].process_grid())

        # add the widgets to the dockable widget
        self.gs_dock_layout.addWidget(self.grid_selector_label, 0)
        self.gs_dock_layout.addLayout(self.radio_layout)
        self.gs_dock_layout.addWidget(self.Dlabel, 0)
        self.gs_dock_layout.addWidget(self.divide_spin_box, 0)
        self.gs_dock_layout.addWidget(self.Xlabel, 0)
        self.gs_dock_layout.addWidget(self.multiply_spin_box, 0)

        # Create a second dockable widget on the left side
        self.tool_dock = QDockWidget('Tool Selector', self.main)
        self.tool_dock.setAllowedAreas(
            Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea | Qt.BottomDockWidgetArea | Qt.TopDockWidgetArea)
        self.tool_dock.setObjectName('ToolDock')
        self.main.addDockWidget(Qt.LeftDockWidgetArea, self.tool_dock)
        # self.tool_dock.setStyleSheet("""background-color: #678;""")

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
        self.tool_selector = QTreeView()
        self.tool_selector.setModel(self.create_tree_model())
        self.tool_selector.header().hide()
        self.tool_selector.setEditTriggers(
            QTreeView.EditTrigger.NoEditTriggers)
        self.tool_selector.setIconSize(QSize(40, 40))
        # set indent size
        self.tool_selector.setIndentation(0)
        # set single selection
        self.tool_selector.setSelectionMode(
            QTreeView.SelectionMode.SingleSelection)
        # self.tree_view.setStyleSheet('background-color: #666666; color: #ffffff')
        self.tool_selector.expandAll()

        # add the widgets to the dockable widget
        self.tool_layout.addWidget(self.tool_label)
        self.tool_layout.addWidget(self.tool_selector)
        # connect the treeview to the select_tool function
        self.tool_selector.clicked.connect(self.tree_view_click)
        # select the note tool by default
        self.tool_selector.setCurrentIndex(
            self.tool_selector.model().index(0, 0))
        self.last_selected_child = None

        # create file browser
        # Create a second dockable widget on the left side
        self.file_dock = QDockWidget('File browser', self.main)
        self.file_dock.setAllowedAreas(
            Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea | Qt.BottomDockWidgetArea | Qt.TopDockWidgetArea)
        self.file_dock.setObjectName('FileBrowserDock')  # Set the object name
        self.main.addDockWidget(Qt.RightDockWidgetArea, self.file_dock)

        self.file_browser_layout = QVBoxLayout()
        self.file_browser = FileBrowser(self.io)
        self.file_browser.setMinimumHeight(400)

        self.file_dock.setWidget(self.file_browser)

    def change_hue(self, value):
        self.colorThread.set_hue(value)

    def change_color(self, color):
        self.setStyleSheet(f"background-color: {color.name()}")

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
            'Harmony': [
                'note',
                'gracenote',
            ],
            'Layout': [
                'beam',
                'linebreak'
            ],
            'Phrase': [
                'countline',
                'text',
                'slur',
                'finger',
                'tempo'
            ]
        }
        for folder in tree:
            # Create a parent item for the first branch
            parent = QStandardItem(folder)
            parent.setBackground(QBrush(QColor("#777777"))
                                 )  # Set background color
            # Set foreground (text) color
            parent.setForeground(QBrush(QColor("white")))
            parent.setSelectable(False)
            model.appendRow(parent)
            for item in tree[folder]:
                # Create a child item with an icon
                icon_name = str(item) + '.png'
                icon = get_icon(icon_name)
                child = QStandardItem(icon, item)
                # Set row height of child item
                child.setSizeHint(QSize(0, 50))
                # Set background color
                child.setBackground(QBrush(QColor("white")))
                # Set foreground (text) color
                child.setForeground(QBrush(QColor("black")))
                parent.appendRow(child)

        return model

    def tree_view_click(self, index):
        if self.tool_selector.model().hasChildren(index):
            # if it's a parent
            if self.last_selected_child.parent() == index:
                # if the last selected child is a child of the clicked parent
                if self.tool_selector.isExpanded(index):
                    self.tool_selector.collapse(index)
                    return
                else:
                    self.tool_selector.expand(index)
                    self.tool_selector.setCurrentIndex(
                        self.last_selected_child)
                    return
            else:
                # if the last selected child is not a child of the clicked parent
                if self.tool_selector.isExpanded(index):
                    self.tool_selector.collapse(index)
                else:
                    self.tool_selector.expand(index)
                self.tool_selector.setCurrentIndex(self.last_selected_child)
                return

        # if index is a child
        else:
            self.last_selected_child = index
            self.io['maineditor'].select_tool(index.data())

        self.editor_view.setFocus()

    def previous_page(self):
        self.io['selected_page'] -= 1
        self.io['maineditor'].update('page_change')

    def next_page(self):
        self.io['selected_page'] += 1
        self.io['maineditor'].update('page_change')

    def refresh(self):
        self.io['maineditor'].update('page_change')
