from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

@dataclass
class LineBreak:
    time: float = 0.0
    margin_mm: List[float] = field(default_factory=lambda: [0.0, 0.0]) # [left, right]
    # [lowest_key, highest_key] (None means the engraver uses automatic detection)
    stave_range: List[int] | None = field(default_factory=lambda: [0, 0]) 
    # Whether this line break indicates a page break or a line break
    page_break: bool = False
    _id: int = 0
