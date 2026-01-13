from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, 
                               QLabel, QDoubleSpinBox, QCheckBox, QComboBox, 
                               QPushButton, QColorDialog, QGridLayout, QWidget,
                               QFrame)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from imports.utils.constants import SCORE_TEMPLATE
import copy


class ColorButton(QPushButton):
    """Custom button that displays and allows editing of colors"""
    def __init__(self, color_hex="#000000"):
        super().__init__()
        self.color_hex = color_hex
        self.setFixedSize(50, 30)
        self.update_color()
        self.clicked.connect(self.choose_color)
    
    def update_color(self):
        self.setStyleSheet(f"background-color: {self.color_hex}; border: 1px solid #ccc;")
    
    def choose_color(self):
        color = QColorDialog.getColor(QColor(self.color_hex), self)
        if color.isValid():
            self.color_hex = color.name()
            self.update_color()
    
    def get_color(self):
        return self.color_hex
    
    def set_color(self, color_hex):
        self.color_hex = color_hex
        self.update_color()


class ScoreOptions(QDialog):
    def __init__(self, parent=None, properties=None):
        super().__init__(parent)
        self.setWindowTitle("Score Options")
        self.setModal(True)
        self.resize(700, 600)
        
        # Use provided properties or default template
        self.properties = properties if properties else copy.deepcopy(SCORE_TEMPLATE['properties'])
        
        # Store widgets for later retrieval
        self.widgets = {}
        
        # Main layout
        main_layout = QVBoxLayout()
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        
        # Create tabs
        self.create_layout_tab()
        self.create_elements_tab()
        self.create_line_widths_tab()
        self.create_font_sizes_tab()
        
        main_layout.addWidget(self.tab_widget)
        
        # Add buttons
        button_layout = QHBoxLayout()
        self.ok_button = QPushButton("OK")
        self.cancel_button = QPushButton("Cancel")
        
        self.ok_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)
        self.ok_button.setDefault(True)
        
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)
        main_layout.addLayout(button_layout)
        
        self.setLayout(main_layout)
    
    def create_layout_tab(self):
        """Create the Layout tab"""
        tab = QWidget()
        layout = QGridLayout()
        row = 0
        
        layout_properties = [
            'page_width', 'page_height', 'page_margin_left', 'page_margin_right',
            'page_margin_up', 'page_margin_down', 'draw_scale', 'header_height',
            'footer_height', 'color_right_midinote', 'color_left_midinote',
            'black_note_rule', 'stop_sign_style', 'continuation_dot_style'
        ]
        
        for prop in layout_properties:
            if prop in SCORE_TEMPLATE['properties']:
                self.add_property_widget(layout, prop, row)
                row += 1
        
        tab.setLayout(layout)
        self.tab_widget.addTab(tab, "Layout")
    
    def create_elements_tab(self):
        """Create the Elements On/Off tab"""
        tab = QWidget()
        layout = QGridLayout()
        row = 0
        
        elements_properties = [
            'staff_onoff', 'minipiano_onoff', 'stem_onoff', 'beam_onoff',
            'note_onoff', 'midinote_onoff', 'notestop_onoff', 'page_numbering_onoff',
            'barlines_onoff', 'basegrid_onoff', 'countline_onoff', 'measure_numbering_onoff',
            'accidental_onoff', 'continuationdot_onoff', 'leftdot_onoff', 'timestamp_onoff',
            'text_onoff'
        ]
        
        for prop in elements_properties:
            if prop in SCORE_TEMPLATE['properties']:
                self.add_property_widget(layout, prop, row)
                row += 1
        
        tab.setLayout(layout)
        self.tab_widget.addTab(tab, "Elements On/Off")
    
    def create_line_widths_tab(self):
        """Create the Line Widths tab"""
        tab = QWidget()
        layout = QGridLayout()
        row = 0
        
        line_width_properties = [
            'staff_threeline_width', 'staff_twoline_width', 'barline_width',
            'beam_width', 'stem_width', 'basegrid_width', 'countline_width',
            'slur_width_middle', 'slur_width_sides'
        ]
        
        for prop in line_width_properties:
            if prop in SCORE_TEMPLATE['properties']:
                self.add_property_widget(layout, prop, row)
                row += 1
        
        tab.setLayout(layout)
        self.tab_widget.addTab(tab, "Line Widths")
    
    def create_font_sizes_tab(self):
        """Create the Font Sizes tab"""
        tab = QWidget()
        layout = QGridLayout()
        row = 0
        
        font_size_properties = [
            'text_font_size', 'title_font_size', 'composer_font_size',
            'footer_font_size', 'measure_numbering_font_size', 'time_signature_font_size'
        ]
        
        for prop in font_size_properties:
            if prop in SCORE_TEMPLATE['properties']:
                self.add_property_widget(layout, prop, row)
                row += 1
        
        tab.setLayout(layout)
        self.tab_widget.addTab(tab, "Font Sizes")
    
    def add_property_widget(self, layout, prop_name, row):
        """Add a widget for a property based on its type"""
        # Skip specified properties
        if prop_name in ['staffs', 'editor_zoom', 'threeline_scale']:
            return
        
        # Get template value to determine widget type
        template_value = SCORE_TEMPLATE['properties'][prop_name]
        # Get current value from properties
        current_value = self.properties.get(prop_name, template_value)
        
        # Create label
        label_text = prop_name.replace('_', ' ').title()
        label = QLabel(f"{label_text}:")
        layout.addWidget(label, row, 0)
        
        # Handle specific dropdown cases first
        if prop_name == 'black_note_rule':
            widget = QComboBox()
            widget.addItem('Up')
            widget.addItem('Down')
            # Set current selection - extract from list format ['Up', 'Down'][1]
            if isinstance(current_value, str):
                if current_value in ['Up', 'Down']:
                    widget.setCurrentText(current_value)
                else:
                    widget.setCurrentIndex(1)  # Default to 'Down'
            else:
                # Current value might be ['Up', 'Down'][1] format
                widget.setCurrentIndex(1)  # Default to 'Down'
            self.widgets[prop_name] = widget
            
        elif prop_name == 'stop_sign_style':
            widget = QComboBox()
            widget.addItem('PianoScript')
            widget.addItem('Klavarskribo')
            # Set current selection - extract from list format ['PianoScript', 'Klavarskribo'][0]
            if isinstance(current_value, str):
                if current_value in ['PianoScript', 'Klavarskribo']:
                    widget.setCurrentText(current_value)
                else:
                    widget.setCurrentIndex(0)  # Default to 'PianoScript'
            else:
                widget.setCurrentIndex(0)  # Default to 'PianoScript'
            self.widgets[prop_name] = widget
            
        elif prop_name == 'continuation_dot_style':
            widget = QComboBox()
            widget.addItem('PianoScript')
            widget.addItem('Klavarskribo')
            # Set current selection - extract from list format ['PianoScript', 'Klavarskribo'][1]
            if isinstance(current_value, str):
                if current_value in ['PianoScript', 'Klavarskribo']:
                    widget.setCurrentText(current_value)
                else:
                    widget.setCurrentIndex(1)  # Default to 'Klavarskribo'
            else:
                widget.setCurrentIndex(1)  # Default to 'Klavarskribo'
            self.widgets[prop_name] = widget
            
        # Handle general types
        elif isinstance(template_value, bool):
            # Checkbox for boolean values
            widget = QCheckBox()
            widget.setChecked(bool(current_value))
            self.widgets[prop_name] = widget
            
        elif isinstance(template_value, (int, float)):
            # Double spinbox for numeric values
            widget = QDoubleSpinBox()
            widget.setDecimals(2)
            widget.setSingleStep(0.05)
            widget.setRange(0.01, 9999.99)
            widget.setValue(float(current_value))
            self.widgets[prop_name] = widget
            
        elif isinstance(template_value, str) and template_value.startswith('#'):
            # Color picker for hex color values
            color_value = current_value if isinstance(current_value, str) and current_value.startswith('#') else template_value
            widget = ColorButton(color_value)
            self.widgets[prop_name] = widget
            
        else:
            # Skip unsupported types
            return
        
        layout.addWidget(widget, row, 1)
    
    def get_properties(self):
        """Return the modified properties dictionary"""
        result = copy.deepcopy(self.properties)
        
        for prop_name, widget in self.widgets.items():
            if widget is None:
                continue
                
            if isinstance(widget, QCheckBox):
                result[prop_name] = widget.isChecked()
            elif isinstance(widget, QDoubleSpinBox):
                result[prop_name] = widget.value()
            elif isinstance(widget, ColorButton):
                result[prop_name] = widget.get_color()
            elif isinstance(widget, QComboBox):
                # For combo boxes, return the selected text as string
                result[prop_name] = widget.currentText()
        
        return result
