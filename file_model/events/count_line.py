from __future__ import annotations
from dataclasses import dataclass

@dataclass
class CountLine:
    time: float = 0.0
    pitch1: int = 40
    pitch2: int = 44
    _id: int = 0
