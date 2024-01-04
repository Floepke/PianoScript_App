color1 = 'pink' # background1
color2 = 'pink' # background2
color3 = '#eeeeee' # text
color4 = '#5555ff' # highlight

stylesheet = '''
font-size: 16px;
background-color: #777777;
color: #eeeeee;
selection-background-color: #445577;
selection-color: white;
QMenuBar::item:selected {
    background-color: #555555;
    color: black;
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