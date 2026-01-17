from __future__ import annotations
from typing import List, Dict
from utils.CONSTANT import EDITOR_DRAWING_ORDER

# Import drawer classes
from .grid_drawer import GridDrawer
from .stave_drawer import StaveDrawer
from .note_drawer import NoteDrawer
from .grace_note_drawer import GraceNoteDrawer
from .beam_drawer import BeamDrawer
from .pedal_drawer import PedalDrawer
from .text_drawer import TextDrawer
from .slur_drawer import SlurDrawer
from .start_repeat_drawer import StartRepeatDrawer
from .end_repeat_drawer import EndRepeatDrawer
from .count_line_drawer import CountLineDrawer
from .line_break_drawer import LineBreakDrawer


_DRAWER_CLASSES: Dict[str, type] = {
    "grid": GridDrawer,
    "stave": StaveDrawer,
    "note": NoteDrawer,
    "grace_note": GraceNoteDrawer,
    "beam": BeamDrawer,
    "pedal": PedalDrawer,
    "text": TextDrawer,
    "slur": SlurDrawer,
    "start_repeat": StartRepeatDrawer,
    "end_repeat": EndRepeatDrawer,
    "count_line": CountLineDrawer,
    "line_break": LineBreakDrawer,
}


def get_all_drawers() -> List[object]:
    """Return all element drawers ordered by EDITOR_DRAWING_ORDER."""
    out: List[object] = []
    for name in EDITOR_DRAWING_ORDER:
        cls = _DRAWER_CLASSES.get(name)
        if cls is not None:
            try:
                out.append(cls())
            except Exception:
                pass
    return out
