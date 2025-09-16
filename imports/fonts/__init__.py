#! python3.11
# coding: utf8

""" Fonts package - Load embedded fonts from base64 data """

from .fonts import (
    load_font,
    get_font_families,
    create_font,
    get_available_fonts,
    load_all_fonts,
    get_edwin_roman_font
)

__all__ = [
    'load_font',
    'get_font_families', 
    'create_font',
    'get_available_fonts',
    'load_all_fonts',
    'get_edwin_roman_font'
]