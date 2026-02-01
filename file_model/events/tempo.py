from __future__ import annotations
from dataclasses import dataclass


@dataclass
class Tempo:
    time: float = 0.0       # start time in ticks
    duration: float = 0.0   # duration in ticks
    tempo: int = 60         # units per minute
    _id: int = 0
