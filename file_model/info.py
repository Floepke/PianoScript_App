from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Info:
    title: str = "title"
    composer: str = "composer"
    copyright: str = "copyright"
    arranger: str = ""
    lyricist: str = ""
    comment: str = ""
