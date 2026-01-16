from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

@dataclass
class BaseGrid:
    """
    Defines the musical grid in measures without specifying literal time positions.
    Attributes:
        numerator (int): The numerator of the time signature.
        denominator (int): The denominator of the time signature.
        grid_step (int): The subdivision of the measure for the grid.
            grid_step defines in how many steps we divide the measure.
        grid_positions (List[int]): The positions within the measure that define the grid.
            1 is the barline. So if 1 misses the app will not print the barline.
            2, 3, 4 are the grid lines.
            so we can hide any of them if needed.
        measure_amount (int): The number of measures with these settings we create.

        So grid_step and grid_positions together define the actual time positions of the grid.
    """
    numerator: int = 4
    denominator: int = 4
    grid_step: int = 4
    grid_positions: List[int] = field(default_factory=lambda: [1, 2, 3, 4])
    measure_amount: int = 1