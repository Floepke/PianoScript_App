from PySide6.QtCore import Qt
from PySide6.QtWidgets import QGraphicsView
from PySide6.QtWidgets import QGraphicsScene, QGraphicsRectItem
from PySide6.QtWidgets import QSplitter, QVBoxLayout, QWidget
from PySide6.QtWidgets import QToolBar, QLineEdit, QSpinBox
from PySide6.QtWidgets import QLabel, QDockWidget
from PySide6.QtGui import QAction
from PySide6.QtGui import QColor
from imports.gui.canvas import GraphicsView

BACKGROUND_COLOR = QColor('#eeeeee')

class Gui():
    def __init__(self, main):
        self.main = main
        
        # Set window properties
        self.main.setWindowTitle("PianoScript")
        self.main.setGeometry(100, 100, 800, 600)

        # Create the status bar
        self.statusbar = self.main.statusBar()
        self.statusbar.showMessage("Ready")

        # Create the file menu
        menubar = self.main.menuBar()
        file_menu = menubar.addMenu("File")
        file_menu.addAction(QAction("Open", triggered=self.open_file))
        file_menu.addAction(QAction("Save", triggered=self.save_file))
        file_menu.addAction(QAction("Exit", triggered=self.main.close))

        # Create a toolbar
        toolbar = QToolBar("Toolbar", self.main)
        self.main.addToolBar(toolbar)

        # Create actions for the toolbar
        action1 = QAction("Cut", self.main)
        action1.triggered.connect(self.cut)
        toolbar.addAction(action1)

        action2 = QAction("Copy", self.main)
        action2.triggered.connect(self.copy)
        toolbar.addAction(action2)

        action3 = QAction("Paste", self.main)
        action3.triggered.connect(self.paste)
        toolbar.addAction(action3)

        # Create the editor view
        self.editor_scene = QGraphicsScene(self.main)
        self.editor_scene.setBackgroundBrush(BACKGROUND_COLOR)
        # self.editor_scene.setSceneRect(0, 0, 400, 400)
        self.editor_view = GraphicsView(self.editor_scene, self.main)
        self.editor_scene.addItem(QGraphicsRectItem(0, 0, 200, 1500))

        # Create the print view
        self.print_scene = QGraphicsScene(self.main)
        self.print_scene.setBackgroundBrush(BACKGROUND_COLOR)
        self.print_view = GraphicsView(self.print_scene, self.main)

        # Create a resizable splitter
        self.splitter = QSplitter(self.main)
        self.splitter.addWidget(self.editor_view)
        self.splitter.addWidget(self.print_view)
        self.splitter.setHandleWidth(20)

        # Set up the main layout
        central_widget = QWidget(self.main)
        self.main.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.addWidget(self.splitter)

        # Create a dockable widget
        self.dock_widget = QDockWidget("Dockable Widget", self.main)
        self.dock_widget.setStyleSheet("""
        QDockWidget {
            border: 1px solid black;
        }
        """)
        self.dock_widget.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.main.addDockWidget(Qt.LeftDockWidgetArea, self.dock_widget)
        

        # Add widgets to the dockable widget
        dock_layout = QVBoxLayout()
        self.entry_box = QLineEdit("Type something")
        self.entry_box.setToolTip("Type something here")
        self.spin_box = QSpinBox()
        self.spin_box.setToolTip("Adjust the spin box")
        self.label = QLabel("Label:")
        self.label.setToolTip("This is a label")
        dock_layout.addWidget(self.entry_box)
        dock_layout.addWidget(self.spin_box)
        dock_layout.addWidget(self.label)
        self.dock_widget.setLayout(dock_layout)

    def show(self):
        self.main.show()

    def open_file(self):
        pass  # Implement file opening logic here

    def save_file(self):
        pass  # Implement file saving logic here

    def cut(self):
        pass  # Implement cut logic here

    def copy(self):
        pass  # Implement copy logic here

    def paste(self):
        pass  # Implement paste logic here

    