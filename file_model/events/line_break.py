from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

@dataclass
class LineBreak:
    time: float = 0.0
    margin_mm: List[float] = field(default_factory=lambda: [0.0, 0.0]) # [left, right]
    stave_range: List[int] = field(default_factory=lambda: [0, 0]) # [lowest_key, highest_key] (zero means automatic mode)
    id: int = 0
