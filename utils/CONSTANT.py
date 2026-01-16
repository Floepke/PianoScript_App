'''
    Here all constants used in the application are stored.
'''

import os
from pathlib import Path

# Directory in the user's home used for autosaves and error backups
# Expanded once and reused across the app for any non-user-initiated saves.
UTILS_SAVE_DIR: Path = Path(os.path.expanduser("~/.pianoscript"))

# the meaning of time is defined in this constant.
QUARTER_NOTE_UNIT: float = 256.0
