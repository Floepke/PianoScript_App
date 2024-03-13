#! python3.11
# coding: utf8

"""  create a dictionary containing the string equivalent of image files """

__author__ = 'Sihir'
__copyright__ = '© Sihir 2024-2024 all rights reserved'

from sys import exit as _exit

from os import curdir
from os import walk

from os.path import join
from os.path import abspath
from os.path import splitext
from os.path import dirname
from os.path import isdir

from base64 import encodebytes as encode_b64

from PySide6.QtGui import QGuiApplication


def has_ext(fullname: str, wanted: str) -> bool:
    """ return True when the fullname has the wanted extension """

    _, ext = splitext(fullname)
    return ext.lower() == wanted.lower()


def b64_encode(value: bytes) -> str:
    """ encode using base64
    :param value: the byte array to be encoded
    """
    return encode_b64(value).decode('utf8')


def pict_as_str(filename: str) -> str:
    """ convert an image to string """

    buffer = open(filename, 'rb').read()
    return b64_encode(buffer)


def create_dict(icons_path: str) -> dict:
    """
    convert all images in the icons folder to string
    and store that in a dictionary
    """
    _ = QGuiApplication()

    image_dict = {}
    for root, folders, files in walk(icons_path):
        for file in files:
            if has_ext(fullname=file, wanted='.png'):
                fullname = join(root, file)
                data = pict_as_str(filename=fullname)
                image_dict[file] = data

    return image_dict


def stringify(image_dict: dict, filename: str):
    """ store the dictionary as python file """

    with open(file=filename, mode='w', encoding='utf8') as stream:

        print('#! python3.11', file=stream)
        print('# coding: utf8', file=stream)
        print(file=stream)
        print('""" the dictionary with images in string format """', file=stream)
        print(file=stream)
        print('# NOTE: this is a generated file, do not change the contents', file=stream)
        print('# see imports/icons/precompile/png2str.py for more info', file=stream)
        print('#', file=stream)
        print('image_dict = {', file=stream)
        for key, value in image_dict.items():
            print(f'        "{key}":"""{value}""", ', file=stream)
        print('}', file=stream)


def to_dict(icons_path: str):
    """ create the file that contains the image dictionary """

    image_dict = create_dict(icons_path)
    target_file = join(icons_path, 'icons_data.py')
    stringify(image_dict=image_dict, filename=target_file)


def find_path(cwd: str, branch: str) -> str:
    """ find the folder somewhere in or above cwd """

    while isdir(cwd):
        for root, folders, _ in walk(cwd):
            for folder in folders:
                if folder in ['.git', 'venv', '.idea']:
                    break
                if folder == 'icons':
                    return join(str(root), folder)
        # try higher
        cwd = dirname(cwd)

    assert False


def main() -> int:
    """ main function """

    cwd = abspath(curdir)
    icons_path = find_path(cwd=cwd, branch='icons')
    to_dict(icons_path=icons_path)
    return 0


if __name__ == '__main__':
    _exit(main())
