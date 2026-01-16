from __future__ import annotations
from dataclasses import dataclass

@dataclass
class Beam:
    time: float = 0.0
    duration: float = 100.0
    hand: str = '<'
    id: int = 0
