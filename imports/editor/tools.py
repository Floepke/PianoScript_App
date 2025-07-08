from PySide6.QtWidgets import QInputDialog, QMessageBox

from imports.utils.constants import QUARTER_PIANOTICK
from imports.utils.savefilestructure import SaveFileStructureSource
from imports.elements.linebreak import LineBreak

'''In quick tools, we provide quick access to various tools that can be used in the editor.'''

class Tools:
    ''' Quick tools for the editor '''
    def __init__(self, io):
        self.io = io

    def add_quick_linebreaks(self):
        ''' Add quick linebreaks to the editor '''

        def evaluate(text):
            '''Returns True if text contains only one or more integers separated by spaces, otherwise False.'''
            text = text.strip()
            if not text:
                return False
            if any(not (char.isdigit() or char.isspace()) for char in text):
                return False
            parts = text.split()
            return bool(parts) and all(part.isdigit() for part in parts)

        prompt = (
            '"4" will insert a line-break every 4 measures till the end of the score.\n'
            '"4 8" will group 4 measures in the first line, then 8 measures in the second line.\n'
            'The latest number is applied till the end of the score. Existing linebreaks will be removed.\n'
            'Please enter only numbers separated by <space> for example "5 3 4":'
        )
        text, ok = QInputDialog.getText(None, 'Add Quick LineBreaks', prompt)

        if not ok:
            return
        if not evaluate(text):
            QMessageBox.information(None, "Invalid Input", "Please enter only numbers separated by spaces.")
            self.add_quick_linebreaks()
            return

        measure_grouping = [int(x) for x in text.split() if x.isdigit()]

        # Remove all linebreaks except the first
        for lb in self.io['score']['events']['linebreak'][1:]:
            LineBreak.delete_editor(self.io, lb)

        barline_ticks = self.io['calc'].get_barline_ticks()
        linebreak_times = []
        idx = 0
        group_idx = 0

        while idx < len(barline_ticks):
            group_size = measure_grouping[group_idx] if group_idx < len(measure_grouping) else measure_grouping[-1]
            idx += group_size
            if idx < len(barline_ticks):
                linebreak_times.append(barline_ticks[idx])
            group_idx += 1

        for lb in linebreak_times:
            new_linebreak = SaveFileStructureSource.new_linebreak(
                tag='linebreak' + str(self.io['calc'].add_and_return_tag()),
                time=lb
            )
            self.io['score']['events']['linebreak'].append(new_linebreak)

        # update the editor
        self.io['maineditor'].update('grid_editor')
