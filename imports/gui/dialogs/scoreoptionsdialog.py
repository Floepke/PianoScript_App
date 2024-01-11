from imports.utils.constants import SCORE_TEMPLATE

from PySide6.QtWidgets import QDialog, QVBoxLayout, QTabWidget, QWidget, QFormLayout, QLabel, QCheckBox, QSpinBox, QDoubleSpinBox, QLineEdit, QScrollArea
from PySide6.QtCore import Qt

class ScoreOptionsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        
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
        header_properties = SCORE_TEMPLATE['header']
        header_form_layout = QFormLayout()
        for key, value in header_properties.items():
            label = QLabel(f'{key}:')
            if isinstance(value, bool):
                checkbox = QCheckBox()
                checkbox.setChecked(value)
                header_form_layout.addRow(label, checkbox)
            elif isinstance(value, int):
                spinbox = QSpinBox()
                spinbox.setValue(value)
                header_form_layout.addRow(label, spinbox)
            elif isinstance(value, float):
                spinbox = QDoubleSpinBox()
                spinbox.setValue(value)
                header_form_layout.addRow(label, spinbox)
            elif isinstance(value, str):
                line_edit = QLineEdit()
                line_edit.setText(value)
                header_form_layout.addRow(label, line_edit)
        header_layout.addLayout(header_form_layout)

        # Create properties tab
        properties_tab = QWidget()
        properties_layout = QVBoxLayout(properties_tab)
        properties_scroll = QScrollArea()
        properties_scroll.setWidgetResizable(True)
        properties_scroll.setWidget(properties_tab)
        tab_widget.addTab(properties_scroll, 'Properties')

        # Add properties to properties tab
        properties = SCORE_TEMPLATE['properties']
        properties_form_layout = QFormLayout()
        properties_layout.alignment()
        for key, value in properties.items():
            label = QLabel(f'{key}:')
            if isinstance(value, bool):
                checkbox = QCheckBox()
                checkbox.setChecked(value)
                properties_form_layout.addRow(label, checkbox)
            elif isinstance(value, int):
                spinbox = QSpinBox()
                spinbox.setValue(value)
                properties_form_layout.addRow(label, spinbox)
            elif isinstance(value, float):
                spinbox = QDoubleSpinBox()
                spinbox.setValue(value)
                properties_form_layout.addRow(label, spinbox)
            elif isinstance(value, str):
                line_edit = QLineEdit()
                line_edit.setText(value)
                properties_form_layout.addRow(label, line_edit)
            elif isinstance(value, dict):
                continue
        properties_layout.addLayout(properties_form_layout)