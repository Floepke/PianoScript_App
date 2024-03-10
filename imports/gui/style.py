color1 = "#140714"
color2 = "#ffdddd"

STYLE = f'''
QTreeView, QGraphicsView, 
QMainWindow, QToolBar, QToolBar,
QToolBar QAction, 
QMainWindow QMenuBar, QMenu, 
QRadioButton, QLabel, QDockWidget, 
QSplitter, QDialog, QVBoxLayout, QHBoxLayout {{
    background-color: {color1};
    color: {color2};
    font-size: 16px;
    font-family: Bookman Old Style;
}}
QMenuBar::item, QMenuBar::item:selected {{
    background-color: {color1};
    color: {color2};
}}
QTabWidget, QTabWidget::pane, QTabWidget::tab-bar {{
    background-color: {color1};
    color: {color2};
}}
QTabWidget::tab-bar::tab:selected {{
    background-color: {color2};
    color: {color1};
}}
QPushButton {{
    background-color: #000000;
    color: {color2};
}}
'''

# Now you can use the STYLE variable in your PyQt application