from __future__ import annotations
from dataclasses import dataclass, field
from typing import Literal

@dataclass
class Layout:
    # Page dimensions and margins
    page_width_mm: float = 210.0
    page_height_mm: float = 297.0
    page_top_margin_mm: float = 10.0
    page_bottom_margin_mm: float = 10.0
    page_left_margin_mm: float = 5.0
    page_right_margin_mm: float = 5.0
    
    # header/footer area settings
    header_height_mm: float = 15.0
    footer_height_mm: float = 8.0

    # Global drawing options
    scale: float = 0.38
    black_note_rule: Literal['above_stem','below_stem'] = 'below_stem'

    # Note appearance
    note_head_visible: bool = True
    note_stem_visible: bool = True
    note_stem_length_semitone: int = 3
    note_stem_thickness_mm: float = 0.5 # Thickness of the stem as well the notehead outline
    note_leftdot_visible: bool = True
    note_midinote_visible: bool = True
    note_midinote_left_color: str = '#cccccc'
    note_midinote_right_color: str = '#cccccc'

    # Beam appearance
    beam_visible: bool = True
    beam_thickness_mm: float = 1.0

    # Grace note appearance
    grace_note_visible: bool = True

    # Pedal appearance
    pedal_lane_enabled: bool = False
    pedal_lane_width_mm: float = 2.5

    # Text appearance
    text_visible: bool = True
    text_font_family: str = 'Courier New'
    text_font_size_pt: float = 10.0

    # Slur appearance
    slur_visible: bool = True
    slur_width_sides_mm: float = 0.1
    slur_width_middle_mm: float = 0.3

    # Repeat markers
    repeat_start_visible: bool = True
    repeat_end_visible: bool = True

    # Count line
    countline_visible: bool = True
    countline_dash_pattern: list[float] = field(default_factory=lambda: [0.0, 1.0])  # Dash pattern for count lines (e.g., [dash_length, gap_length])
    countline_thickness_mm: float = 0.5

    # Grid lines
    grid_barline_thickness_mm: float = 0.8
    grid_gridline_thickness_mm: float = 0.8
    grid_gridline_dash_pattern_mm: list[float] = field(default_factory=lambda: [3.0, 3.0])

    # Time signature indicator type (global)
    time_signature_indicator_type: Literal['classical', 'klavarskribo', 'both'] = 'both'

    # Stave appearence
    stave_two_line_thickness_mm: float = 0.5
    stave_three_line_thickness_mm: float = 0.5
    stave_clef_line_dash_pattern_mm: list[float] = field(default_factory=lambda: [3.0, 3.0])  # Dash pattern for clef lines (e.g., [dash_length, gap_length])


LAYOUT_FLOAT_CONFIG: dict[str, dict[str, float]] = {
    'page_width_mm': {'min': 50.0, 'max': 10000.0, 'step': 0.5},
    'page_height_mm': {'min': 50.0, 'max': 10000.0, 'step': 0.5},
    'page_top_margin_mm': {'min': 0.0, 'max': 100.0, 'step': 0.5},
    'page_bottom_margin_mm': {'min': 0.0, 'max': 100.0, 'step': 0.5},
    'page_left_margin_mm': {'min': 0.0, 'max': 100.0, 'step': 0.5},
    'page_right_margin_mm': {'min': 0.0, 'max': 100.0, 'step': 0.5},
    'header_height_mm': {'min': 0.0, 'max': 100.0, 'step': 0.5},
    'footer_height_mm': {'min': 0.0, 'max': 100.0, 'step': 0.5},
    'scale': {'min': 0.0, 'max': 1.0, 'step': 0.01},
    'note_stem_length_semitone': {'min': 0.0, 'max': 20.0, 'step': 1.0},
    'note_stem_thickness_mm': {'min': 0.0, 'max': 5.0, 'step': 0.1},
    'beam_thickness_mm': {'min': 0.0, 'max': 5.0, 'step': 0.1},
    'pedal_lane_width_mm': {'min': 0.0, 'max': 20.0, 'step': 0.5},
    'text_font_size_pt': {'min': 4.0, 'max': 94.0, 'step': 0.5},
    'slur_width_sides_mm': {'min': 0.0, 'max': 5.0, 'step': 0.1},
    'slur_width_middle_mm': {'min': 0.0, 'max': 5.0, 'step': 0.1},
    'countline_thickness_mm': {'min': 0.0, 'max': 5.0, 'step': 0.1},
    'grid_barline_thickness_mm': {'min': 0.0, 'max': 5.0, 'step': 0.1},
    'grid_gridline_thickness_mm': {'min': 0.0, 'max': 5.0, 'step': 0.1},
    'stave_two_line_thickness_mm': {'min': 0.0, 'max': 5.0, 'step': 0.1},
    'stave_three_line_thickness_mm': {'min': 0.0, 'max': 5.0, 'step': 0.1},
}
    
