from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

@dataclass
class BaseGrid:
    """
    Defines the musical grid across a sequence of measures.

    - numerator: time signature numerator (e.g., 4 in 4/4)
    - denominator: time signature denominator (e.g., 4 in 4/4)

    Denominator defines the smallest possible time step for the base grid in
    this context. A denominator of 1 enforces drawing the barline (beat 1) for
    each measure. Higher denominators subdivide the measure into smaller units
    and `grid_beats_enabled` selects which beats are drawn/enabled.

    For example, in 4/4, `grid_beats_enabled=[1,2,3,4]` draws beats 1–4.

    - grid_beats_enabled: list of beat indices within the measure to draw/enable.
      Beat 1 always corresponds to the barline.
    - measure_amount: number of measures to generate with these settings.
    """
    numerator: int = 4
    denominator: int = 4
    grid_beats_enabled: List[int] = field(default_factory=lambda: [1, 2, 3, 4])
    measure_amount: int = 1