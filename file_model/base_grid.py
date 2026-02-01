from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Literal

@dataclass
class BaseGrid:
    """
    Defines the musical grid across a sequence of measures.

    - numerator: time signature numerator (e.g., 4 in 4/4)
    - denominator: time signature denominator (e.g., 4 in 4/4)

    Denominator defines the smallest possible time step for the base grid in
    this context. A denominator of 1 enforces drawing the barline (beat 1) for
    each measure. Higher denominators subdivide the measure into smaller units
    and `beat_grouping` selects which beats are drawn/enabled.

    For example, in 4/4, `beat_grouping=[1,2,3,4]` means a single group of 4.
    In 7/8 with 3+4 grouping, `beat_grouping=[1,2,3,1,2,3,4]`.

    - beat_grouping: per-beat sequence describing grouping. The sequence length
      must equal the numerator. It must start at 1 and can only count up or
      reset to 1 (e.g., 1231234).
    - measure_amount: number of measures to generate with these settings.
    """
    numerator: int = 4
    denominator: int = 4
    beat_grouping: List[int] = field(default_factory=lambda: [1, 2, 3, 4])
    measure_amount: int = 1
    indicator_enabled: bool = True