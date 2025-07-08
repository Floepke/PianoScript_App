#! python3.12
#  Copyright (c) 2020 - 2020. Sihir Veenendaal

""" merge exception information from two sources into one class"""

__author__ = 'Sihir'
__copyright__ = "© Sihir 2020-2021 all rights reserved"


import os

from os.path import join

import sys

from functools import wraps

from typing import Any


# pylint: enable=too-many-instance-attributes
class MyException(BaseException):
    """ extract all useful information from the exception and the inspection """

    def __init__(self, extra: Any = None):
        exc = sys.exc_info()
        self.exception_type = exc[0].__name__
        self.message = str(exc[1])
        self.extra = extra if extra else ''

        # find the highest level of the stack
        exx = exc[2]
        while exx.tb_next:
            exx = exx.tb_next

        self.line_number = exx.tb_lineno
        self.function_name = exx.tb_frame.f_code.co_name
        fullname = exx.tb_frame.f_code.co_filename
        self.file_name = os.path.basename(fullname)
        self.path = os.path.dirname(fullname)
        super().__init__(self.message)

    def __str__(self):
        """ convert to string """
        return '\n'.join([
            f"exception: {self.exception_type}",
            f"message  : {self.message}",
            f"function : {self.function_name}",
            f"line nr  : {self.line_number}",
            f"filename : {self.file_name}",
            f"path     : {self.path}",
            f"source   : {self.source}"
            f"extra    : {self.extra}"])

    @property
    def source(self) -> str:
        """ the line of source where the exception occurred """

        return self._get_source(join(self.path, self.file_name), self.line_number)

    def _get_source(self, fullname: str, line_number: int) -> str:
        """ get the line of source from the file """
        assert self
        with open(fullname, mode='r', encoding='utf8') as stream:
            line = ''
            for _ in range(line_number):
                line = stream.readline()
            return f'"{line_number}: {line.strip()}"\n'


def try_wrap(to_stderr: bool = False):
    """ use '@try_wrap()' before 'def func(...)' to wrap try/except for exceptions inside 'func' """

    def wrap_outer(func):
        @wraps(func)
        def wrap_inner(*args, **kwargs):
            wrap_inner.__doc__ = func.__doc__

            try:

                return func(*args, **kwargs)

            # pylint: disable=broad-except
            except Exception as ex1:
                ex2 = MyException()
                print(ex2, file=sys.stderr if to_stderr else sys.stdout)
                raise ex2 from ex1

        return wrap_inner
    return wrap_outer
