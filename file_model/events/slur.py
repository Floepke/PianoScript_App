from __future__ import annotations
from dataclasses import dataclass

@dataclass
class Slur:
    """
    Slur defined by 4 cubic Bezier control points.
    x coordinates use the relative amount of semitone distances from c4.
    y coordinates use time units (e.g., quarter note = 256.0).
    """
    x1_rpitch: int = 0
    y1_time: float = 0.0
    x2_rpitch: int = 0
    y2_time: float = 25.0
    x3_rpitch: int = 0
    y3_time: float = 75.0
    x4_rpitch: int = 0
    y4_time: float = 100.0
    _id: int = 0
