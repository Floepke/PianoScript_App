from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class Info:
    title: str = "Untitled"
    composer: str = "Composer"
    copyright: str = f"© all rights reserved {datetime.now().year}"
    arranger: str = ""
    lyricist: str = ""
    comment: str = ""
