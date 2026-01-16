from __future__ import annotations
from typing import List

# Import drawer stubs
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


def get_all_drawers() -> List[object]:
    """Return all element drawers to be invoked by the editor view."""
    return [
        NoteDrawer(),
        GraceNoteDrawer(),
        BeamDrawer(),
        PedalDrawer(),
        TextDrawer(),
        SlurDrawer(),
        StartRepeatDrawer(),
        EndRepeatDrawer(),
        CountLineDrawer(),
        LineBreakDrawer(),
    ]
