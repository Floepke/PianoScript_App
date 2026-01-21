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
    and `grid_positions` selects which beats are drawn/enabled.

    For example, in 4/4, `grid_positions=[1,2,3,4]` draws beats 1–4.

    - grid_positions: list of beat indices within the measure to draw/enable.
      Beat 1 always corresponds to the barline.
    - measure_amount: number of measures to generate with these settings.
    """
    numerator: int = 4
    denominator: int = 4
    grid_positions: List[int] = field(default_factory=lambda: [1, 2, 3, 4])
    measure_amount: int = 1
    indicator_enabled: bool = True
    indicator_type: Literal["classical", "klavarskribo", "both"] = "classical"