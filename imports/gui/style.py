from PySide6.QtGui import QColor

class Style():
    def __init__(self, io):
        
        self.io = io

        # default stylesheet
        self.default_stylesheet = io['app'].styleSheet()

        # colors
        self.color1 = '#ffffff'
        self.color2 = '#ffffff'
        
        # set the mood slider
        self.io['gui'].slider.valueChanged.connect(self.update_mood_slider)
        self.update_mood_slider()

    def update_mood_slider(self):

        slider_y = self.io['gui'].slider.slidery
        if slider_y < 0:
            slider_y = 0
        elif slider_y > 255:
            slider_y = 255

        complementary_color = QColor.fromHsv(
            self.io['gui'].slider.value(), 25, 200)
        self.color1 = complementary_color.name()
        # negative color self.color2
        negative_color = QColor(self.color1).rgb() ^ 0xFFFFFF
        self.color2 = QColor(negative_color).name()

        style = f'''
            QPushButton, QStatusBar, QMenuBar, QMenu, 
            QSpinBox, QRadioButton, QTabBar,
            QSplitter, QMainWindow, QDockWidget,
            QDialog, QListWidget, QLabel, QGroupBox
            {{
                background-color: {self.color1};
                color: {self.color2};
                font-family: Edwin;
                font-size: 16px;
            }}
            QMenuBar, QMenu::item {{
                padding: 7.5px 7.5px
            }}
            QMenuBar::item:selected, QMenu::Item::selected {{
                background-color: white;
                color: black;
            }}
            QLabel, QGroupBox, QCheckBox, QRadioButton {{
                background-color: transparent;
                font-family: Edwin;
                font-size: 16px;
            }}
            QTreeView {{
                background-color: {self.color1};
                color: {self.color2};
                font-family: Edwin;
                font-size: 16px;
            }}
            QTreeView QHeaderView::section {{
                background-color: {self.color1};  /* Change this to the desired color */
                color: {self.color2};  /* Change this to the desired color */
            }}
            QTabWidget QWidget {{
                background-color: {self.color1};
                color: {self.color2};
                font-family: Edwin;
                font-size: 16px;
            }}
        '''

        self.io['app'].setStyleSheet(style)