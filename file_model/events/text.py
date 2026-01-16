from __future__ import annotations
from dataclasses import dataclass

@dataclass
class Text:
    text: str = '120/4'
    time: float = 0.0
    side: str = '<'
    mm_from_side: float = 5.0
    rotated: bool = True
    id: int = 0
