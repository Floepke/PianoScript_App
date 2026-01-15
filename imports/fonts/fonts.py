#! python3.11
# coding: utf8

""" Load fonts from base64 encoded data and create QFont objects """

from base64 import decodebytes as decode_b64
from typing import Optional, List
from PySide6.QtGui import QFontDatabase, QFont
from PySide6.QtCore import QByteArray

try:
    from .fonts_data import font_dict
except ImportError:
    # Fallback for direct execution
    from fonts_data import font_dict


def b64_decode(value: str) -> bytes:
    """ Decode using base64
    :param value: the string to be decoded
    :return: decoded bytes
    """
    return decode_b64(value.encode('utf8'))


def load_font(key: str) -> int:
    """ Load font from base64 data and register it with QFontDatabase
    :param key: font key in font_dict
    :return: font ID from QFontDatabase, -1 if failed
    """
    value = font_dict.get(key, '')
    if not value:
        print(f"Warning: Font key '{key}' not found in font_dict")
        return -1
    
    try:
        # Decode the base64 font data
        font_bytes = b64_decode(value)
        font_data = QByteArray(font_bytes)
        
        # Add the font to the application's font database
        font_id = QFontDatabase.addApplicationFontFromData(font_data)
        
        if font_id == -1:
            print(f"Warning: Failed to load font '{key}' into QFontDatabase")
        else:
            families = QFontDatabase.applicationFontFamilies(font_id)
            #print(f"Successfully loaded font '{key}' with families: {families}")
        
        return font_id
        
    except Exception as e:
        print(f"Error loading font '{key}': {e}")
        return -1


def get_font_families(key: str) -> List[str]:
    """ Get font family names after loading a font
    :param key: font key in font_dict
    :return: list of font family names, empty if failed
    """
    font_id = load_font(key)
    if font_id == -1:
        return []
    
    return QFontDatabase.applicationFontFamilies(font_id)


def create_font(key: str, size: int = 12, weight: QFont.Weight = QFont.Weight.Normal) -> Optional[QFont]:
    """ Create a QFont object from embedded font data
    :param key: font key in font_dict
    :param size: font size in points
    :param weight: font weight
    :return: QFont object or None if failed
    """
    families = get_font_families(key)
    if not families:
        print(f"Warning: Could not create font for key '{key}'")
        return None
    
    # Use the first available family
    font_family = families[0]
    font = QFont(font_family)
    font.setPointSize(size)
    font.setWeight(weight)
    
    return font


def get_available_fonts() -> List[str]:
    """ Get list of available font keys
    :return: list of font keys available in font_dict
    """
    return list(font_dict.keys())


def load_all_fonts() -> dict:
    """ Load all available fonts and return their families
    :return: dictionary mapping font keys to their family names
    """
    result = {}
    for key in font_dict.keys():
        families = get_font_families(key)
        if families:
            result[key] = families
        else:
            print(f"Warning: Failed to load font '{key}'")
    
    return result


# Convenience function to get the Edwin Roman font specifically
def get_edwin_roman_font(size: int = 12, weight: QFont.Weight = QFont.Weight.Normal) -> Optional[QFont]:
    """ Get the Edwin Roman font as QFont object
    :param size: font size in points
    :param weight: font weight
    :return: QFont object or None if failed
    """
    return create_font('edwin_roman', size, weight)