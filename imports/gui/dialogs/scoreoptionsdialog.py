from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QTabWidget
from PySide6.QtWidgets import QWidget, QFormLayout, QCheckBox, QDoubleSpinBox
from PySide6.QtWidgets import QScrollArea, QPushButton, QComboBox, QLabel, QGridLayout
from PySide6.QtWidgets import QPushButton, QLineEdit, QColorDialog, QGroupBox
from PySide6.QtGui import QColor


class ScoreOptionsDialog(QDialog):
    def __init__(self, io, parent=None):
        super().__init__(parent)
        self.io = io

        self.resize(700, 500)
        self.setWindowTitle("Score Options")

        layout = QVBoxLayout(self)
        tab_widget = QTabWidget(self)
        layout.addWidget(tab_widget)

        # Create header tab
        header_tab = QWidget()
        header_layout = QVBoxLayout(header_tab)
        header_scroll = QScrollArea()
        header_scroll.setWidgetResizable(True)
        header_scroll.setWidget(header_tab)
        tab_widget.addTab(header_scroll, 'Header')

        # Add header properties to header tab
        header_form_layout = QFormLayout()
        header_form_layout.setFieldGrowthPolicy(
            QFormLayout.AllNonFixedFieldsGrow)

        self.title = QLineEdit(str(self.io['score']['header']['title']))
        self.composer = QLineEdit(str(self.io['score']['header']['composer']))
        self.copyright = QLineEdit(
            str(self.io['score']['header']['copyright']))
        self.app_name = QLineEdit(str(self.io['score']['header']['app_name']))
        self.app_version = QLineEdit(
            str(self.io['score']['header']['app_version']))
        self.timestamp = QLineEdit(
            str(self.io['score']['header']['timestamp']))
        self.genre = QLineEdit(str(self.io['score']['header']['genre']))
        self.comment = QLineEdit(str(self.io['score']['header']['comment']))

        header_form_layout.addRow('Title:', self.title)
        header_form_layout.addRow('Composer:', self.composer)
        header_form_layout.addRow('Copyright:', self.copyright)
        header_form_layout.addRow('App Name:', self.app_name)
        header_form_layout.addRow('App Version:', self.app_version)
        header_form_layout.addRow('Timestamp:', self.timestamp)
        header_form_layout.addRow('Genre:', self.genre)
        header_form_layout.addRow('Comment:', self.comment)

        header_layout.addLayout(header_form_layout)

        # Create properties tab
        properties_tab = QWidget()
        properties_form_layout = QFormLayout()
        properties_layout = QVBoxLayout(properties_tab)

        properties_layout.addLayout(properties_form_layout)
        properties_layout.addStretch(1)  # Add this line

        properties_scroll = QScrollArea()
        properties_scroll.setWidgetResizable(True)
        properties_scroll.setWidget(properties_tab)
        properties_scroll.setMinimumWidth(300)
        tab_widget.addTab(properties_scroll, 'Doc Properties')

        self.page_width = QDoubleSpinBox()
        self.page_width.setRange(10, 10000)
        self.page_width.setValue(
            float(self.io['score']['properties']['page_width']))

        self.page_height = QDoubleSpinBox()
        self.page_height.setRange(10, 10000)
        self.page_height.setValue(
            float(self.io['score']['properties']['page_height']))

        self.page_margin_left = QDoubleSpinBox()
        self.page_margin_left.setRange(0, 1000)
        self.page_margin_left.setValue(
            float(self.io['score']['properties']['page_margin_left']))

        self.page_margin_right = QDoubleSpinBox()
        self.page_margin_right.setRange(0, 1000)
        self.page_margin_right.setValue(
            float(self.io['score']['properties']['page_margin_right']))

        self.page_margin_up = QDoubleSpinBox()
        self.page_margin_up.setRange(0, 1000)
        self.page_margin_up.setValue(
            float(self.io['score']['properties']['page_margin_up']))

        self.page_margin_down = QDoubleSpinBox()
        self.page_margin_down.setRange(0, 1000)
        self.page_margin_down.setValue(
            float(self.io['score']['properties']['page_margin_down']))

        self.draw_scale = QDoubleSpinBox()
        self.draw_scale.setRange(0.1, 10)
        self.draw_scale.setSingleStep(0.05)
        self.draw_scale.setValue(
            float(self.io['score']['properties']['draw_scale']))

        self.header_height = QDoubleSpinBox()
        self.header_height.setRange(0, 1000)
        self.header_height.setValue(
            float(self.io['score']['properties']['header_height']))

        self.footer_height = QDoubleSpinBox()
        self.footer_height.setRange(0, 1000)
        self.footer_height.setValue(
            float(self.io['score']['properties']['footer_height']))

        self.black_note_rule = QComboBox()
        # , 'DownExceptCollision', 'UpExceptCollision', 'OnlyChordUp'
        self.black_note_rule.addItems(['Up', 'Down'])
        self.black_note_rule.setCurrentText(
            self.io['score']['properties']['black_note_rule'])

        self.threeline_scale = QDoubleSpinBox()
        self.threeline_scale.setRange(0.1, 10)
        self.threeline_scale.setSingleStep(0.05)
        self.threeline_scale.setValue(
            float(self.io['score']['properties']['threeline_scale']))

        self.stop_sign_style = QComboBox()
        self.stop_sign_style.addItems(['PianoScript', 'Klavarskribo'])
        self.stop_sign_style.setCurrentText(
            self.io['score']['properties']['stop_sign_style'])

        self.continuation_dot_style = QComboBox()
        self.continuation_dot_style.addItems(['PianoScript', 'Klavarskribo'])
        self.continuation_dot_style.setCurrentText(
            self.io['score']['properties']['continuation_dot_style'])

        self.color_right_midinote = QComboBox()
        self.color_right_midinote.addItems(
            ['lightpink', 'lightgreen', 'lightskyblue', 'gold', '#aaa', '#bbb', '#ccc', '#ddd', '#eee'])
        self.color_right_midinote.setEditable(True)
        self.color_right_midinote.setCurrentText(
            self.io['score']['properties']['color_right_midinote'])

        self.color_left_midinote = QComboBox()
        self.color_left_midinote.addItems(
            ['lightpink', 'lightgreen', 'lightskyblue', 'gold', '#aaa', '#bbb', '#ccc', '#ddd', '#eee'])
        self.color_left_midinote.setEditable(True)
        self.color_left_midinote.setCurrentText(
            self.io['score']['properties']['color_left_midinote'])

        properties_form_layout.addRow('Page Width:', self.page_width)
        properties_form_layout.addRow('Page Height:', self.page_height)
        properties_form_layout.addRow(
            'Page Margin Left:', self.page_margin_left)
        properties_form_layout.addRow(
            'Page Margin Right:', self.page_margin_right)
        properties_form_layout.addRow('Page Margin Up:', self.page_margin_up)
        properties_form_layout.addRow(
            'Page Margin Down:', self.page_margin_down)
        properties_form_layout.addRow('Draw Scale:', self.draw_scale)
        properties_form_layout.addRow('Header Height:', self.header_height)
        properties_form_layout.addRow('Footer Height:', self.footer_height)
        properties_form_layout.addRow('Black Note Rule:', self.black_note_rule)
        properties_form_layout.addRow('ThreeLine Scale:', self.threeline_scale)
        properties_form_layout.addRow('Stop Sign Style:', self.stop_sign_style)
        properties_form_layout.addRow(
            'Continuation Dot Style:', self.continuation_dot_style)
        properties_form_layout.addRow(
            'Color Right Midinote:', self.color_right_midinote)
        properties_form_layout.addRow(
            'Color Left Midinote:', self.color_left_midinote)

        properties_layout.addLayout(properties_form_layout)

        # Create elements tab
        elements_tab = QWidget()
        elements_layout = QVBoxLayout(elements_tab)
        elements_scroll = QScrollArea()
        elements_scroll.setWidgetResizable(True)
        elements_scroll.setWidget(elements_tab)
        tab_widget.addTab(elements_scroll, 'Elements on/off')
        elements_form_layout = QFormLayout()
        elements_form_layout.setFieldGrowthPolicy(
            QFormLayout.AllNonFixedFieldsGrow)
        
        # build all checkboxes from the .pianoscript file; all keys that have 'onoff' in the keyname will be automatically added to the dialog
        for onoff in self.io['score']['properties'].keys():
            if 'onoff' in onoff:
                # create a checkbox
                checkbox = QCheckBox()
                checkbox.setChecked(self.io['score']['properties'][onoff])
                # add the checkbox to the form layout
                elements_form_layout.addRow(f'{onoff}: ', checkbox)
                # create an instance variable for the checkbox
                setattr(self, f'{onoff}', checkbox)

        elements_layout.addLayout(elements_form_layout)

        # Add the tab widget to the layout
        layout.addWidget(tab_widget)

        # Create OK and Cancel buttons
        close_button = QPushButton('Close')
        apply_button = QPushButton('Apply')
        close_button.clicked.connect(lambda: self.accept())
        apply_button.clicked.connect(lambda: self.validate(close=False))

        # Add the buttons to a layout
        button_layout = QHBoxLayout()
        button_layout.addWidget(close_button)
        button_layout.addWidget(apply_button)
        layout.addLayout(button_layout)

    def validate(self, close: bool):
        '''Validate the data entered in the dialog'''

        # header tab
        self.io['score']['header']['title'] = self.title.text()
        self.io['score']['header']['composer'] = self.composer.text()
        self.io['score']['header']['copyright'] = self.copyright.text()
        self.io['score']['header']['app_name'] = self.app_name.text()
        self.io['score']['header']['app_version'] = self.app_version.text()
        self.io['score']['header']['timestamp'] = self.timestamp.text()
        self.io['score']['header']['genre'] = self.genre.text()
        self.io['score']['header']['comment'] = self.comment.text()

        # properties tab
        self.io['score']['properties']['page_width'] = self.page_width.value()
        self.io['score']['properties']['page_height'] = self.page_height.value()
        self.io['score']['properties']['page_margin_left'] = self.page_margin_left.value()
        self.io['score']['properties']['page_margin_right'] = self.page_margin_right.value()
        self.io['score']['properties']['page_margin_up'] = self.page_margin_up.value()
        self.io['score']['properties']['page_margin_down'] = self.page_margin_down.value()
        self.io['score']['properties']['draw_scale'] = self.draw_scale.value()
        self.io['score']['properties']['header_height'] = self.header_height.value()
        self.io['score']['properties']['footer_height'] = self.footer_height.value()
        self.io['score']['properties']['black_note_rule'] = self.black_note_rule.currentText()
        self.io['score']['properties']['threeline_scale'] = self.threeline_scale.value()
        self.io['score']['properties']['stop_sign_style'] = self.stop_sign_style.currentText()
        self.io['score']['properties']['continuation_dot_style'] = self.continuation_dot_style.currentText()
        self.io['score']['properties']['color_right_midinote'] = self.color_right_midinote.currentText()
        self.io['score']['properties']['color_left_midinote'] = self.color_left_midinote.currentText()

        # onoff tab; we read all properties that have 'onoff' in the key name which are always bool in .pianoscript files.
        for key in self.io['score']['properties'].keys():
            if 'onoff' in key:
                self.io['score']['properties'][key] = getattr(self, key).isChecked()

        self.io['maineditor'].update('score_options')


class ColorPicker(QWidget):
    def __init__(self, initial_color, validate, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout()
        self.button = QPushButton("Colorpicker", self)
        self.button.clicked.connect(self.on_button_clicked)
        self.line_edit = QLineEdit(initial_color, self)
        self.layout.addWidget(self.button)
        self.layout.addWidget(self.line_edit)
        self.setLayout(self.layout)
        self.validate = validate

    def on_button_clicked(self):
        color = QColorDialog.getColor(QColor(self.line_edit.text()), self)
        if color.isValid():
            self.line_edit.setText(color.name())
        self.validate()
