#! python3.11
# coding: utf8

""" get a QIcon or QPixmap from the dictionary with images """

"""  image from example """

from base64 import decodebytes as decode_b64

from PySide6.QtGui import QPixmap
from PySide6.QtGui import QIcon

from imports.icons.icons_data import image_dict


def b64_decode(value: str) -> bytes:
    """ decode using base64
    :param value: the string to be decoded
    """
    return decode_b64(value.encode('utf8'))


def get_pixmap(key: str) -> QPixmap:
    """ get the string representation and convert that to QPixmap """

    value = image_dict.get(key, '')
    pixmap = QPixmap()
    pixmap.loadFromData(b64_decode(value))
    return pixmap


def get_icon(key: str) -> QIcon:
    """ get the string representation and convert that to QIcon """

    pixmap = get_pixmap(key)
    assert pixmap
    icon = QIcon(pixmap)
    assert icon
    return icon
