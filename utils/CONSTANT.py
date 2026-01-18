'''
    Here all constants used in the application are stored.
'''

import os
from pathlib import Path

from utils.tiny_tool import key_class_filter

# Directory in the user's home used for autosaves and error backups
# Expanded once and reused across the app for any non-user-initiated saves.
UTILS_SAVE_DIR: Path = Path(os.path.expanduser('~/.pianoscript'))

# the meaning of time is defined in this constant.
QUARTER_NOTE_UNIT: float = 256.0

# Drawing orders (single sources of truth)
# Each string corresponds to a drawer name registered in editor/drawers/__init__.py
# Update these lists to control layer stacking in the Editor and Engraver.
EDITOR_LAYERING = [
    # midi_note in background of the notation.
    'cursor_grid',
    'midi_note', 
    
    # stave elements
    'chord_guide',
    'grid_line',
    'stave_three_line',
    'stave_two_line',
    'stave_clef_line',
    'barline',
    'stem_white_space',
    
    # note elements
    'stop_sign',
    'accidental',
    'notehead_white',
    'notehead_black',
    'left_dot',
    'stem',
    'chord_connect',

    # grace_note
    'grace_note',

    # beam elements
    'beam',
    'beam_stem',

    # other notation elements
    'measure_number',
    'slur',
    'text',
    'tempo',
    'line_break',
    'count_line',
    
    # UI elements (top layers)
    'selection_rect',  # Selection rectangle
    'keyboard_overlay_bg',     # Piano keyboard overlay background
    'keyboard_overlay_keys',   # Piano keyboard overlay keys
    'cursor',            # Always on top
]

ENGRAVER_LAYERING = [
    # to be entered later
    ...
]

# Keyboard constants
PIANO_KEY_AMOUNT: int = 88

# key collections
BLACK_KEYS: list[int] = key_class_filter('CDFGA')
BE_KEYS: list[int] = key_class_filter('be')

