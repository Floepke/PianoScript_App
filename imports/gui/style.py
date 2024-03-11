color1 = "#140714"
color2 = "#ffdddd"
color3 = '#000000'

STYLE = f'''
QGroupBox, QListWidget,
QLabel, QComboBox, QSpinBox,
QTreeView, QGraphicsView, 
QMainWindow, QToolBar, QToolBar,
QToolBar QAction, QGroupBox, QTabWidget, QTabWidget::pane, QTabWidget::tab-bar, QTabWidget::tab,
QMainWindow QMenuBar, QMenu, QLineEdit, QComboBox,
QRadioButton, QLabel, QDockWidget, 
QSplitter, QDialog, QVBoxLayout, QHBoxLayout {{
    background-color: {color1};
    color: {color2};
    font-size: 16px;
    font-family: Bookman Old Style;
    font-color: {color2};
}}
QMenuBar::item, QMenuBar::item:selected {{
    background-color: {color1};
    color: {color2};
}}
QTabWidget, QTabWidget::pane, QTabWidget::tab-bar {{
    background-color: {color1};
    color: {color2};
}}
QPushButton {{
    background-color: {color1};
    color: {color2};
}}
QSlider::groove:horizontal {{
    border: 15px solid #999999;
    height: 15px; /* the groove expands to the size of the slider by default. by giving it a height, it has a fixed size */
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #B1B1B1, stop:1 #c4c4c4);
    margin: 2px 0;
}}

QSlider::add-page:horizontal {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {color1}, stop:1 {color3});
}}

QSlider::sub-page:horizontal {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {color3}, stop:1 {color1});
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
    background-color: {color1};
    color: {color2};
}}
QTabWidget QWidget {{
    background-color: {color1};
}}
QTabBar::tab {{
    background-color: {color1};
    color: {color2};
}}

QTabBar::tab:selected {{
    background-color: {color2};
    color: {color1};
}}
QSpinBox {{
    background-color: {color2};
    color: {color1};
}}
StatusBar {{
    background-color: {color1};
    color: {color2};
}}
'''

# Now you can use the STYLE variable in your PyQt application