from __future__ import annotations
from dataclasses import dataclass

@dataclass
class GraceNote:
    pitch: int = 41
    time: float = 50.0
    id: int = 0
