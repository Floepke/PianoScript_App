#! python3.11
# coding: utf8

""" piano notes translator, key A0 is key 1, key C8 is 88 """

__author__ = 'Sihir'
__copyright__ = '© Sihir 2023-2024 all rights reserved'

from dataclasses import dataclass


@dataclass
class PianoNotes:
    """ conversion from piano key number to name and octave """

    _note_names = [
        'C ', 'C#', 'D ', 'D#',
        'E ', 'F ', 'F#', 'G ',
        'G#', 'A ', 'A#', 'B '
    ]

    _dictionary = {}

    @staticmethod
    def translate_note(piano_note: int) -> tuple:
        """ translate the number to a note name """

        octave, note = divmod(piano_note + 8, 12)
        name = PianoNotes._note_names[note]
        note = f'{name.strip()}{octave}'
        return name, octave, note

    @staticmethod
    def start_notes():
        """ possible start notes for the staff """

        return [
            1,      # A0
            4, 9,   # C1, F1
            16, 21,
            28, 33,
            40, 45,
            52, 57,
            64, 69,
            76, 81]

    @staticmethod
    def finish_notes():
        """ possible start notes for the staff """

        return [
            3, 8,  # B1, E1
            15, 20,
            27, 32,
            39, 44,
            51, 56,
            63, 68,
            75, 80,
            87]

    @staticmethod
    def revert_translation(wanted: str):
        """ translate 'B1' back to 19, etc """

        if not PianoNotes._dictionary:
            for number in PianoNotes.start_notes() + PianoNotes.finish_notes():
                _, _, note = PianoNotes.translate_note(number)
                PianoNotes._dictionary[note] = number

        return PianoNotes._dictionary.get(wanted, '?')
