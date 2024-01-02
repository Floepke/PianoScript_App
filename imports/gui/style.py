stylesheet = '''
QWidget {
    background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                stop:0 #666666, stop:1 #222222);
    color: #FFFFFF;
}
QToolBar, QDockWidget {
    background-color: #555555;
}
QGraphicsView {
    border: 1px solid qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                stop:0 #666666, stop:1 #222222);
}
QSplitter::handle {
    background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                stop:0 #666666, stop:1 #222222);
}
QStatusBar, QMenuBar, QMenu {
    background-color: #222222;
}
QGraphicsView QScrollBar {
    background-color: #555555;
}
'''

# stylesheet = '''
# QMainWindow {
#     background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
#                                 stop:0 #666666, stop:1 #222222);
#     color: #FFFFFF;
# }
# QToolBar {
#     background-color: #555555;
#     color: #555555;
# }
# QDockWidget {
#     background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
#                                 stop:0 #666666, stop:1 #222222);
#     color: #FFFFFF;
# }
# QLineEdit, QSpinBox, QLabel {
#     background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
#                                 stop:0 #666666, stop:1 #222222);
#     color: #FFFFFF;
# }
# QGraphicsView {
#     background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
#                                 stop:0 #666666, stop:1 #222222);
#     border: 1px solid qlineargradient(x1:0, y1:0, x2:0, y2:1,
#                                 stop:0 #666666, stop:1 #222222);
# }
# QSplitter::handle {
#     background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
#                                 stop:0 #666666, stop:1 #222222);
#     color: #FFFFFF;
# }
# QDockWidget {
#     background-color: #555555;  /* Set the overall background color, including title bar */
#     color: #FFFFFF;  /* Set the text color */
# }
# QMenuBar {
#     background-color: #555555;
#     color: #FFFFFF;
# }
# QDockWidget {
#     border: 1px solid black;
# }
# QStatusbar {
#     background-color: #555555;
#     color: #FFFFFF;
# }
# QMenu {
#     background-color: #555555;
#     color: pink;
# }
# '''