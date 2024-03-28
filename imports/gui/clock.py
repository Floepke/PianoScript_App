import sys
from PySide6.QtCore import QTimer, QTime, Qt
from PySide6.QtWidgets import QApplication, QLabel, QWidget, QVBoxLayout

class Clock(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Clock Widget")
        
        self.label = QLabel()
        self.label.setAlignment(Qt.AlignCenter)
        
        layout = QVBoxLayout()
        layout.addWidget(self.label)
        self.setLayout(layout)
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_time)
        self.timer.start(1000)  # Update every second
        
        self.update_time()
        
    def update_time(self):
        current_time = QTime.currentTime()
        time_text = current_time.toString("hh:mm")
        self.label.setText(time_text)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    clock_widget = Clock()
    clock_widget.show()
    sys.exit(app.exec())
