from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class FontSpec:
    family: str = "Times New Roman"
    size_pt: float = 12.0
    bold: bool = False
    italic: bool = False

    def resolve_family(self) -> str:
        try:
            from fonts import resolve_font_family
            return resolve_font_family(self.family)
        except Exception:
            return self.family


@dataclass
class HeaderText(FontSpec):
    text: str = ""


@dataclass
class Header:
    title: HeaderText = field(default_factory=lambda: HeaderText(
        text="title",
        family="Times New Roman",
        size_pt=12.0,
    ))
    composer: HeaderText = field(default_factory=lambda: HeaderText(
        text="composer",
        family="Times New Roman",
        size_pt=10.0,
    ))
    copyright: HeaderText = field(default_factory=lambda: HeaderText(
        text="copyright",
        family="Times New Roman",
        size_pt=8.0,
    ))
