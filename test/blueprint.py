#! python3.11
# coding: utf-8

""" blueprint class example """

__author__ = 'Philip Bergwerf'  # noqa
__copyright__ = '© Philip Bergwerf 2023-2023 all rights reserved'  # noqa


Score = {
    "events":
    {
        "grid": [],
        "note": []
    }
}

BluePrint = {
  "events": {
    "grid": [
      {
        "amount": 22,
        "numerator": 3,
        "denominator": 4,
        "nr": 1,
        "option": 'option 1',
        "visible": True,
        "grid": [256, 512, 768],
      },
      {
        "amount": 11,
        "numerator": 4,
        "denominator": 4,
        "nr": 2,
        "option": 'option 2',
        "visible": False,
        "grid": [256, 512, 768],
      },
      {
        "amount": 33,
        "numerator": 4,
        "denominator": 4,
        "nr": 3,
        "option": 'option 3',
        "visible": True,
        "grid": [256, 512, 768],
      },
      {
        "amount": 8,
        "numerator": 4,
        "denominator": 4,
        "nr": 4,
        "option": 'option 4',
        "visible": True,
        "grid": [256, 512, 768],
      },
      {
        "amount": 16,
        "numerator": 5,
        "denominator": 8,
        "option": "option 5",
        "nr": 5,
        "visible": True,
        "grid": [256, 512, 768]
      }
    ],
  "note": [
      {
        "id": "note1",
        "time": 0,
        "duration": 128,
        "pitch": 52,
        "hand": "r",
        "x-offset": 0,
        "y-offset": 0,
        "stem-visible": True,
        "accidental": 0,
        "type": "note",
        "staff": 0,
        "notestop": True  # noqa
      },
      {
        "id": "note2",
        "time": 0,
        "duration": 128,
        "pitch": 57,
        "hand": "r",
        "x-offset": 0,
        "y-offset": 0,
        "stem-visible": True,
        "accidental": 0,
        "type": "note",
        "staff": 0,
        "notestop": True  # noqa
      },
      {
        "id": "note3",
        "time": 0,
        "duration": 128,
        "pitch": 61,
        "hand": "r",
        "x-offset": 0,
        "y-offset": 0,
        "stem-visible": True,
        "accidental": 0,
        "type": "note",
        "staff": 0,
        "notestop": True  # noqa
      },
      {
        "id": "note4",
        "time": 0,
        "duration": 128,
        "pitch": 64,
        "hand": "r",
        "x-offset": 0,
        "y-offset": 0,
        "stem-visible": True,
        "accidental": 0,
        "type": "note",
        "staff": 0,
        "notestop": True  # noqa
      }
    ],
    "beam": [
      {
        "id": "beam434",
        "time": 0.0,
        "duration": 256.0,
        "hand": "r",
        "staff": 0,
        "type": "beam"
      },
      {
        "id": "beam652",
        "time": 0.0,
        "duration": 256.0,
        "hand": "l",
        "staff": 0,
        "type": "beam"
      },
    ]
  }
}
