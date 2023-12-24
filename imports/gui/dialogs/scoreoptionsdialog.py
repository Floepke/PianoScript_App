from PySide6.QtWidgets import QDialog, QVBoxLayout, QTabWidget, QWidget, QGridLayout, QLabel, QCheckBox, QSpinBox, QDoubleSpinBox, QLineEdit, QApplication, QFrame
import datetime


class ScoreOptionsDialog(QDialog):
    def __init__(self, json_data, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        tab_widget = QTabWidget(self)
        layout.addWidget(tab_widget)

        # Create header tab
        header_tab = QWidget()
        header_layout = QGridLayout(header_tab)
        tab_widget.addTab(header_tab, "Header")

        # Add header properties to header tab
        header_properties = json_data["header"]
        row = 0
        col = 0
        for key, value in header_properties.items():
            label = QLabel(f"{key}:")
            header_layout.addWidget(label, row, col)
            col += 1
            if isinstance(value, bool):
                checkbox = QCheckBox()
                checkbox.setChecked(value)
                header_layout.addWidget(checkbox, row, col)
            elif isinstance(value, int):
                spinbox = QSpinBox()
                spinbox.setValue(value)
                header_layout.addWidget(spinbox, row, col)
            elif isinstance(value, float):
                spinbox = QDoubleSpinBox()
                spinbox.setValue(value)
                header_layout.addWidget(spinbox, row, col)
            elif isinstance(value, str):
                line_edit = QLineEdit()
                line_edit.setText(value)
                header_layout.addWidget(line_edit, row, col)
            # Add a separator
            separator = QFrame()
            separator.setFrameShape(QFrame.VLine)
            separator.setFrameShadow(QFrame.Sunken)
            header_layout.addWidget(separator, row, col)
            col += 1
            if col >= 3:
                col = 0
                row += 1

        # Create properties tab
        properties_tab = QWidget()
        properties_layout = QGridLayout(properties_tab)
        tab_widget.addTab(properties_tab, "Properties")

        # Add properties to properties tab
        properties = json_data["properties"]
        row = 0
        col = 0
        for key, value in properties.items():
            label = QLabel(f"{key}:")
            properties_layout.addWidget(label, row, col)
            col += 1
            if isinstance(value, bool):
                checkbox = QCheckBox()
                checkbox.setChecked(value)
                properties_layout.addWidget(checkbox, row, col)
            elif isinstance(value, int):
                spinbox = QSpinBox()
                spinbox.setValue(value)
                properties_layout.addWidget(spinbox, row, col)
            elif isinstance(value, float):
                spinbox = QDoubleSpinBox()
                spinbox.setValue(value)
                properties_layout.addWidget(spinbox, row, col)
            elif isinstance(value, str):
                line_edit = QLineEdit()
                line_edit.setText(value)
                properties_layout.addWidget(line_edit, row, col)
            col += 1
            if col >= 3:
                col = 0
                row += 1

if __name__ == "__main__":
    json_structure = {
            "header":{
                "title":{
                    "text":"Untitled",
                    "x-offset":0,
                    "y-offset":0,
                    "visible":True
                },
                "composer":{
                    "text":"PianoScript",
                    "x-offset":0,
                    "y-offset":0,
                    "visible":True
                },
                "copyright":{
                    "text":"\u00a9 PianoScript 2023",
                    "x-offset":0,
                    "y-offset":0,
                    "visible":True
                },
                "app-name":"pianoscript",
                "app-version":1.0,
                "timestamp":datetime.datetime.now().strftime("%d-%m-%Y_%H:%M:%S"),
                "genre":"",
                "comment":""
            },
            "properties":{
                "page-width":210,
                "page-height":297,
                "page-margin-left":10,
                "page-margin-right":10,
                "page-margin-up":10,
                "page-margin-down":10,
                "draw-scale":1,
                "header-height":10,
                "footer-height":10,
                "minipiano":True,
                "engraver":"pianoscript vertical",
                "color-right-hand-midinote":"#c8c8c8",
                "color-left-hand-midinote":"#c8c8c8",
                "editor-zoom":80,
                "staffonoff":True,
                "stemonoff":True,
                "beamonoff":True,
                "noteonoff":True,
                "midinoteonoff":True,
                "notestoponoff":True,
                "pagenumberingonoff":True,
                "barlinesonoff":True,
                "basegridonoff":True,
                "countlineonoff":True,
                "measurenumberingonoff":True,
                "accidentalonoff":True,
                "staff":[
                    {
                        "onoff":True,
                        "name":"Staff 1",
                        "staff-number":0,
                        "staff-scale":1.0
                    },
                    {
                        "onoff":False,
                        "name":"Staff 2",
                        "staff-number":1,
                        "staff-scale":1.0
                    },
                    {
                        "onoff":False,
                        "name":"Staff 3",
                        "staff-number":2,
                        "staff-scale":1.0
                    },
                    {
                        "onoff":False,
                        "name":"Staff 4",
                        "staff-number":3,
                        "staff-scale":1.0
                    }
                ],
                "soundingdotonoff":True,
                "black-note-style":"PianoScript",
                "threelinescale":1,
                "stop-sign-style":"PianoScript",
                "leftdotonoff":True
            },
            "events":{
                "grid":[
                    {
                "tag":"grid",
                "amount":4,
                "numerator":4,
                "denominator":4,
                "grid":4,
                "visible":True
            }
            ],
            "note":[],
            "ornament":[],
            "text":[],
            "beam":[],
            "bpm":[],
            "slur":[],
            "pedal":[],
            "linebreak":[
            {
                "tag":"linebreak",
                "time":0,
                "margin-staff1-left":10,
                "margin-staff1-right":10,
                "margin-staff2-left":10,
                "margin-staff2-right":10,
                "margin-staff3-left":10,
                "margin-staff3-right":10,
                "margin-staff4-left":10,
                "margin-staff4-right":10
            }
            ],
            "countline":[],
            "staffsizer":[],
            "startrepeat":[],
            "endrepeat":[],
            "starthook":[],
            "endhook":[]
        }
    }
    app = QApplication([])
    dialog = ScoreOptionsDialog(json_structure)
    dialog.exec()
