#! python3.12

""" the StringBuilder class using StringIO """

__author__ = 'Sihir'  # noqa
__copyright__ = '© Sihir 2024-2024 all rights reserved'  # noqa

from time import struct_time
from time import localtime
from time import time as _time


def to_dhms(value: int) -> str:  # noqa
    """ convert seconds to days:hours:mins:secs """  # noqa

    if value is None:
        return '0:00:00:00'

    minutes = int(value / 60)
    seconds = int(value % 60)
    hours = int(minutes / 60)
    minutes = int(minutes % 60)
    days = int(hours / 24)
    hours = int(hours % 24)

    if days > 0:
        return f'{days}.{hours:0>2}:{minutes:0>2}:{seconds:0>2}'
    else:
        return f'{hours:0>2}:{minutes:0>2}:{seconds:0>2}'


def from_dhms(duration: str) -> int:  # noqa
    """ calc number of seconds of the track """

    parts = duration.split(':')
    seconds = int(parts[3])
    minutes = int(parts[2])
    hours = int(parts[1])
    days = int(parts[0])
    value = ((24 * days + hours) * 60 + minutes) * 60 + seconds
    return value


def now() -> struct_time:
    """ current date and time """
    return localtime(_time())


def timestamp(when: struct_time) -> str:
    """ create a timestamp string """

    return f'{when.tm_year}' \
           f'{when.tm_mon:0>2}' \
           f'{when.tm_mday:0>2}_' \
           f'{when.tm_hour:0>2}'\
           f'{when.tm_min:0>2}' \
           f'{when.tm_sec:0>2}'
