from __future__ import annotations
from dataclasses import dataclass

@dataclass
class Pedal:
    type: str = 'v'  # 'v' = down, '^' = up
    time: float = 0.0
    _id: int = 0
