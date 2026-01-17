'''
    Here all constants used in the application are stored.
'''

import os
from pathlib import Path

# Directory in the user's home used for autosaves and error backups
# Expanded once and reused across the app for any non-user-initiated saves.
UTILS_SAVE_DIR: Path = Path(os.path.expanduser('~/.pianoscript'))

# the meaning of time is defined in this constant.
QUARTER_NOTE_UNIT: float = 256.0

# Drawing orders (single sources of truth)
# Each string corresponds to a drawer name registered in editor/drawers/__init__.py
# Update these lists to control layer stacking in the Editor and Engraver.
EDITOR_DRAWING_ORDER = [
    'grid',
    'stave',
    'note',
    'grace_note',
    'beam',
    'pedal',
    'text',
    'slur',
    'start_repeat',
    'end_repeat',
    'count_line',
    'line_break',
]

ENGRAVER_DRAWING_ORDER = [
    # Default engraver order; customize independently if needed
    'grid',
    'stave',
    'note',
    'beam',
    'slur',
    'grace_note',
    'text',
    'start_repeat',
    'end_repeat',
    'count_line',
    'line_break',
    'pedal',
]

# Keyboard constants
PIANO_KEY_AMOUNT: int = 88

# Black keys in 1..88 (1 = A0, 88 = C8)
# Pattern: A#, C#, D#, F#, G# per 12-semitone group starting at A0
BLACK: list[int] = [
    k for k in range(1, PIANO_KEY_AMOUNT + 1)
    if ((k - 1) % 12) in (1, 4, 6, 9, 11)
]
