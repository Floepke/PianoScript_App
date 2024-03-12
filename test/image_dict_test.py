"""  image from example """

from sys import exit as _exit
from sys import argv

from os import mkdir
from os import walk
from os import remove
from os import rmdir

from os.path import join
from os.path import abspath
from os.path import splitext
from os.path import isdir
from os.path import isfile

from base64 import encodebytes as encode_b64
from base64 import decodebytes as decode_b64

from PySide6.QtGui import QPixmap
from PySide6.QtGui import QIcon
from PySide6.QtGui import QGuiApplication

try:
    # it is no error that this file does not exist
    # it is created by running this script without an argument
    #
    # when the dictionary is created it can be tested by
    # running the script with the argument -t
    #
    # remove the file test_dictionary.py running
    # the script with the argument -c
    #
    # see what is possible with the image dictionary
    # with the function test_dict.
    # to execute that function, run the script with the
    # argument -d
    #
    from image_dictionary import image_dict2
except:
    pass


def has_ext(fullname: str, wanted: str) -> bool:
    """ ... """

    _, ext = splitext(fullname)

    return ext.lower() == wanted.lower()


def b64_encode(value: bytes) -> str:
    """ encode using base64
    :param value: the byte array to be encoded
    """
    return encode_b64(value).decode('utf8')


def b64_decode(value: str) -> bytes:
    """ decode using base64
    :param value: the string to be decoded
    """
    return decode_b64(value.encode('utf8'))


def pict_as_str(filename: str) -> str:
    """ convert an image to string """

    buffer = open(filename, 'rb').read()
    return b64_encode(buffer)


def create_dict() -> dict:
    """ - """

    image_dict = {}
    image_path = abspath('imports/icons')

    for root, folders, files in walk(image_path):
        for file in files:
            if has_ext(file, '.png'):
                fullname = join(root, file)
                data = pict_as_str(filename=fullname)
                image_dict[file] = data

    return image_dict


def clean(work_folder: str):
    """ clean all files in directory dir """

    for root, _, files in walk(work_folder):
        for file in files:
            fullname = join(root, file)
            remove(fullname)


def get_pixmap(image_dict: dict, key: str) -> QPixmap:
    """ ... """

    value = image_dict.get(key, '')
    pixmap = QPixmap()
    pixmap.loadFromData(b64_decode(value))
    return pixmap


def get_icon(image_dict: dict, key: str) -> QIcon:
    """ ... """

    pixmap = get_pixmap(image_dict, key)
    assert pixmap
    icon = QIcon(pixmap)
    assert icon
    return icon


def test_dict(work_path):
    """ test the conversion """
    _ = QGuiApplication()

    image_dict = create_dict()
    for key in image_dict.keys():

        pixmap = get_pixmap(image_dict, key)
        pixmap.save(join(work_path, key), 'PNG')

        icon = QIcon(pixmap)
        assert icon


def stringify(image_dict: dict, filename: str):
    """ store the dictionary as python file """

    with open(file=filename, mode='w', encoding='utf8') as stream:
        print('image_dict2 = {', file=stream)
        for key, value in image_dict.items():
            print(f'        "{key}":"""{value}""", ', file=stream)
        print('}', file=stream)


def to_dict():
    """ create the file that contains the image dictionary """

    image_dict = create_dict()
    stringify(image_dict, 'test/image_dictionary.py')


def from_dict(work_path: str):
    """ read a file from the image dictionary """

    _ = QGuiApplication()

    key = 'note.png'
    target = join(work_path, key)

    pixmap = get_pixmap(image_dict2, key)
    pixmap.save(target, 'PNG')

    icon = QIcon(pixmap)
    assert icon

    print(f'written {target}')


def main() -> int:
    """ main function """

    work_path = abspath('test/work')

    if '-t' in argv:

        if not isdir(work_path):
            mkdir(work_path)

        clean(work_path)
        from_dict(work_path)

    elif '-c' in argv:

        if isdir(work_path):
            clean(work_path)
            rmdir(work_path)

        dict_file = abspath('test/image_dictionary.py')
        if isfile(dict_file):
            remove(dict_file)

    elif '-d' in argv:

        if not isdir(work_path):
            mkdir(work_path)

        clean(work_path)

        test_dict(work_path)

    else:
        to_dict()

    return 0


if __name__ == '__main__':
    _exit(main())
