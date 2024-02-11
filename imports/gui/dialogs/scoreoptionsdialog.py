from imports.utils.constants import SCORE_TEMPLATE

from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget, QFormLayout, QLabel, QCheckBox, QSpinBox, QDoubleSpinBox, QLineEdit, QScrollArea, QPushButton, QComboBox
from PySide6.QtCore import Qt

class ScoreOptionsDialog(QDialog):
    def __init__(self, io, parent=None):
        super().__init__(parent)
        self.io = io
        
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
        header_form_layout.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)

        self.title = QLineEdit(str(self.io['score']['header']['title']))
        self.composer = QLineEdit(str(self.io['score']['header']['composer']))
        self.copyright = QLineEdit(str(self.io['score']['header']['copyright']))
        self.app_name = QLineEdit(str(self.io['score']['header']['app_name']))
        self.app_version = QLineEdit(str(self.io['score']['header']['app_version']))
        self.timestamp = QLineEdit(str(self.io['score']['header']['timestamp']))
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
        properties_layout = QVBoxLayout(properties_tab)
        properties_scroll = QScrollArea()
        properties_scroll.setWidgetResizable(True)
        properties_scroll.setWidget(properties_tab)
        tab_widget.addTab(properties_scroll, 'Properties')

        properties_form_layout = QFormLayout()
        properties_form_layout.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)

        self.page_width = QDoubleSpinBox()
        self.page_width.setRange(10, 10000)
        self.page_width.setValue(float(self.io['score']['properties']['page_width']))
        
        self.page_height = QDoubleSpinBox()
        self.page_height.setRange(10, 10000)
        self.page_height.setValue(float(self.io['score']['properties']['page_height']))
        
        # self.page_margin_left = QDoubleSpinBox(float(self.io['score']['properties']['page_margin_left']))
        # self.page_margin_right = QDoubleSpinBox(float(self.io['score']['properties']['page_margin_right']))
        # self.page_margin_up = QDoubleSpinBox(float(self.io['score']['properties']['page_margin_up']))
        # self.page_margin_down = QDoubleSpinBox(float(self.io['score']['properties']['page_margin_down']))
        # self.draw_scale = QDoubleSpinBox(float(self.io['score']['properties']['draw_scale']))
        # self.header_height = QDoubleSpinBox(float(self.io['score']['properties']['header_height']))
        # self.footer_height = QDoubleSpinBox(float(self.io['score']['properties']['footer_height']))
        # self.black_note_rule = QComboBox((self.io['score']['properties']['black_note_rule']))
        # self.threeline_scale = QDoubleSpinBox(float(self.io['score']['properties']['threeline_scale']))
        # self.stop_sign_style = QComboBox()
        # self.stop_sign_style.addItems(['PianoScript', 'Klavarskribo'])
        # self.stop_sign_style.setCurrentIndex(0)
        # self.continuation_dot_style = QComboBox()
        # self.staff_onoff = QCheckBox()
        # self.minipiano_onoff = QCheckBox()
        # self.stem_onoff = QCheckBox()
        # self.beam_onoff = QCheckBox()
        # self.note_onoff = QCheckBox()
        # self.midinote_onoff = QCheckBox()
        # self.notestop_onoff = QCheckBox()
        # self.page_numbering_onoff = QCheckBox()
        # self.barlines_onoff = QCheckBox()
        # self.basegrid_onoff = QCheckBox()
        # self.countline_onoff = QCheckBox()
        # self.measure_numbering_onoff = QCheckBox()
        # self.accidental_onoff = QCheckBox()
        # self.soundingdot_onoff = QCheckBox()
        # self.leftdot_onoff = QCheckBox()

        properties_form_layout.addRow('Page Width:', self.page_width)
        properties_form_layout.addRow('Page Height:', self.page_height)
        # properties_form_layout.addRow('Page Margin Left:', self.page_margin_left)
        # properties_form_layout.addRow('Page Margin Right:', self.page_margin_right)
        # properties_form_layout.addRow('Page Margin Up:', self.page_margin_up)
        # properties_form_layout.addRow('Page Margin Down:', self.page_margin_down)
        # properties_form_layout.addRow('Draw Scale:', self.draw_scale)
        # properties_form_layout.addRow('Header Height:', self.header_height)
        # properties_form_layout.addRow('Footer Height:', self.footer_height)
        # properties_form_layout.addRow('Black Note Rule:', self.black_note_rule)
        # properties_form_layout.addRow('ThreeLine Scale:', self.threeline_scale)
        # properties_form_layout.addRow('Stop Sign Style:', self.stop_sign_style)
        # properties_form_layout.addRow('Continuation Dot Style:', self.continuation_dot_style)
        # properties_form_layout.addRow('Staff:', self.staff_onoff)
        # properties_form_layout.addRow('MiniPiano:', self.minipiano_onoff)
        # properties_form_layout.addRow('Stem:', self.stem_onoff)
        # properties_form_layout.addRow('Beam:', self.beam_onoff)
        # properties_form_layout.addRow('Note:', self.note_onoff)
        # properties_form_layout.addRow('MidiNote:', self.midinote_onoff)
        # properties_form_layout.addRow('NoteStop:', self.notestop_onoff)
        # properties_form_layout.addRow('Page Numbering:', self.page_numbering_onoff)
        # properties_form_layout.addRow('Barlines:', self.barlines_onoff)
        # properties_form_layout.addRow('Basegrid:', self.basegrid_onoff)
        # properties_form_layout.addRow('Countline:', self.countline_onoff)
        # properties_form_layout.addRow('Measure Numbering:', self.measure_numbering_onoff)
        # properties_form_layout.addRow('Accidental:', self.accidental_onoff)
        # properties_form_layout.addRow('SoundingDot:', self.soundingdot_onoff)
        # properties_form_layout.addRow('LeftDot:', self.leftdot_onoff)

        properties_layout.addLayout(properties_form_layout)

        # Create OK and Cancel buttons
        ok_button = QPushButton('OK')
        cancel_button = QPushButton('Cancel')

        # Connect the OK button to the accept slot
        ok_button.clicked.connect(self.validate)

        # Connect the Cancel button to the reject slot
        cancel_button.clicked.connect(self.reject)

        # Add the buttons to a layout
        button_layout = QHBoxLayout()
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)

    
    def validate(self):
        
        header_tab = [self.title, self.composer, self.copyright, 
                      self.app_name, self.app_version, self.timestamp, 
                      self.genre, self.comment]
        self.io['score']['header']['title'] = self.title.text()
        self.io['score']['header']['composer'] = self.composer.text()
        self.io['score']['header']['copyright'] = self.copyright.text()
        self.io['score']['header']['app_name'] = self.app_name.text()
        self.io['score']['header']['app_version'] = self.app_version.text()
        self.io['score']['header']['timestamp'] = self.timestamp.text()
        self.io['score']['header']['genre'] = self.genre.text()
        self.io['score']['header']['comment'] = self.comment.text()

        self.io['score']['properties']['page_width'] = self.page_width.value()
        self.io['score']['properties']['page_height'] = self.page_height.value()
        
        self.io['maineditor'].update('loadfile')
        
        
        self.accept()