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
    x_offset_mm: float = 0.0
    y_offset_mm: float = 0.0


@dataclass
class Header:
    title: HeaderText = field(default_factory=lambda: HeaderText(
        text="title",
        family="C059",
        size_pt=25.0,
    ))
    composer: HeaderText = field(default_factory=lambda: HeaderText(
        text="composer",
        family="C059",
        size_pt=15.0,
    ))
    copyright: HeaderText = field(default_factory=lambda: HeaderText(
        text="copyright",
        family="C059",
        size_pt=10.0,
    ))
