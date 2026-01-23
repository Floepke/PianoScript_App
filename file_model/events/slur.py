from __future__ import annotations
from dataclasses import dataclass

@dataclass
class Slur:
    """
    Slur defined by 4 cubic Bezier control points.
    x coordinates use semitone offsets relative to C4 (central C) on a vertical stave.
    y coordinates use time units (e.g., quarter note = 256.0).
    """
    x1_semitones_c4: int = 0
    y1_time: float = 0.0
    x2_semitones_c4: int = 0
    y2_time: float = 25.0
    x3_semitones_c4: int = 0
    y3_time: float = 75.0
    x4_semitones_c4: int = 0
    y4_time: float = 100.0
    id: int = 0
