from __future__ import annotations
from dataclasses import dataclass
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

    # Global drawing options
    scale: float = 1.0
    color_right_midinote: str = '#cccccc'
    color_left_midinote: str = '#cccccc'
    black_note_rule: Literal['above_stem','below_stem'] = 'below_stem'

    # Note appearance
    note_head_visible: bool = True
    note_stem_visible: bool = True
    note_stem_length_mm: float = 7.5
    note_stem_width_mm: float = 0.5 # Thickness of the stem as well the notehead outline
    note_leftdot_visible: bool = True

    # Beam appearance
    beam_visible: bool = True
    beam_thickness_mm: float = 0.5

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
    countline_thickness_mm: float = 0.4
