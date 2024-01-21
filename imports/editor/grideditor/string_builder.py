#! python3.11

""" the StringBuilder class using StringIO """

__author__ = 'Sihir'  # noqa
__copyright__ = '© Sihir 2021-2022 all rights reserved'  # noqa

from io import StringIO


class StringBuilder:
    """ the implementation of StringBuilder """
    _file_str = None

    def __init__(self, value: str = '') -> None:
        """ initialize the buffer
        :param value: the optional string to initialize the buffer with
        :return: None
        """
        self._file_str = StringIO()
        if len(value) > 0:
            self.append_line(value)

    def clear(self) -> str:
        """ save the buffer, clean it and return what was saved """
        result = str(self)
        self._file_str.truncate(0)
        self._file_str.seek(0)
        return result

    def append(self, value: str, separator=None) -> None:
        """ add a value to the buffer, no newline
        :param value: the string to append, without line feed
        :param separator: the optional separator, prepended when the buffer is not empty
        :return: None
        """
        if not value:
            return

        if separator and self._file_str.tell() > 0:
            self._file_str.write(separator)
        self._file_str.write(value)

    def append_line(self, value=None) -> None:
        """ add a value to the buffer, with newline
        :param value: the string to append, with line feed
        :return: None
        """
        if not value:
            value = ''
        self._file_str.write(f'{value}\n')

    def insert(self, pos: int, value: str) -> None:
        """ insert a string on position 'pos'
        :param pos: location to start insert
        :param value: the string to insert
        :return: None
        """
        string = self._file_str
        # save the last part, which will come after the insertion
        last = string.getvalue()[pos:]
        # first remains in the buffer
        string.truncate(pos)
        # truncate does not implicitly do a seek
        string.seek(pos)
        # append the value
        string.write(value)
        # append the last part
        string.write(last)

    def delete(self, pos: int, num: int) -> None:
        """ Delete 'num' characters from position 'pos'
        :param pos: location to start delete
        :param num: number of characters to delete
        :return: None
        """
        orig = self._file_str.getvalue()
        self._file_str = StringIO(orig[:pos] + orig[pos + num:])
        # tell from end is seek(a, 2)
        self._file_str.seek(0, 2)

    def truncate(self, pos: int = 0) -> None:
        """
        Truncate the length of the buffer, by default clear the buffer
        :param pos:
        :return:
        """
        self._file_str.truncate(pos)
        self._file_str.seek(pos)

    def seek(self, pos: int, whence: int = 0):
        """ seek to position 'pos' """
        if whence in [0, 2]:
            self._file_str.seek(pos, whence)
        elif whence == 1:
            self._file_str.seek(self._file_str.tell() + pos)
        else:
            raise NotImplementedError(f'string_builder.seek(..., {whence}')

    def tell(self) -> int:
        """ tell the current position """
        return self._file_str.tell()

    def read(self) -> str:
        """ read the characters from the current tell() position """
        return self._file_str.read()

    def read_line(self) -> str:
        """
        read a line inclusive the line-end character
        starting at the tell() position
        :return: the string that was read as line
        """
        pos = loc = self._file_str.tell()
        data = self._file_str.getvalue()
        size = len(data)
        while pos < size and data[pos] != '\n':
            pos += 1
        # return the characters read
        result = data[loc:pos + 1]
        # seek beyond the end of the string that was read
        self._file_str.seek(pos + 1)
        return result

    def find(self, sub_string: str, location: int = 0) -> int:
        """
        find 'sub_string' in the buffer
        :param sub_string: the string to find
        :param location: the location where to start finding the sub_string
        :return: the location (if >= 0) or -1 when not found
        """
        data = self._file_str.getvalue()
        pos = data.find(sub_string, location)
        if pos >= 0:
            # seek to that location, so a 'read()' or 'read_line()' can be done
            self._file_str.seek(pos)
            return pos

        # not found:
        return -1

    def to_string(self) -> str:
        """ convert to str
        :return: string contents of the buffer
        """
        return str(self)

    def __str__(self) -> str:
        """ the str implementation
        :return: string contents of the buffer
        """
        return self._file_str.getvalue()

    def __len__(self) -> int:
        """ the len implementation
        :return: length of the buffer
        """
        return self._file_str.tell()

    def count_lines(self):
        """ count the number of lines """
        return self._file_str.getvalue().count('\n')
