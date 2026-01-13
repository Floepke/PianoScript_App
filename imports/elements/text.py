from imports.utils.savefilestructure import SaveFileStructureSource
from PySide6.QtWidgets import QInputDialog, QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QSpinBox, QPushButton
from imports.utils.constants import *
import copy


class Text:
    def __init__(self):
        self.edit_obj = None
        self.edit_time = None
        self.edit_side = None

    def tool(self, io, event_type: str, x: int, y: int):
        '''handles the mouse handling of the text tool'''

        # left mouse button handling:
        if event_type == 'leftclick':
            detect = io['editor'].detect_item(io, float(x), float(y), event_type='text')
            if detect: # we clicked on an existing text item, edit it
                self.edit_obj = copy.deepcopy(detect)
                self.edit_time = detect['time']
                self.edit_side = detect['side']
            else: # we didn't click on an existing text item, create a new one
                
                # Create and show dialog
                dialog = TextInputDialog(io['root'])
                if dialog.exec() == QDialog.DialogCode.Accepted:
                    text_input, mm_from_side = dialog.get_values()
                    
                    if text_input.strip():  # Check if text is not empty
                        # create new text item:
                        new = SaveFileStructureSource.new_text(
                            tag='text' + str(io['calc'].add_and_return_tag()),
                            time=io['calc'].y2tick_editor(y, snap=True),
                            staff=io['selected_staff'],
                            text=text_input,
                            side='<' if io['calc'].x2pitch_editor(x) <= 40 else '>',
                            mm_from_side=mm_from_side
                        )

                        # draw in the editor:
                        self.draw_editor(io, new)

                        # add to savefile:
                        io['score']['events']['text'].append(new)

        elif event_type == 'leftclick+move':
            if self.edit_obj:
                # move the text item
                self.edit_obj['time'] = io['calc'].y2tick_editor(y, snap=True)
                self.edit_obj['side'] = '<' if io['calc'].x2pitch_editor(x) <= 40 else '>'
                # redraw in the editor:
                self.draw_editor(io, self.edit_obj)
            else:
                ...

        elif event_type == 'leftrelease':
            if self.edit_obj:
                # move the text item
                self.edit_obj['time'] = io['calc'].y2tick_editor(y, snap=True)
                self.edit_obj['side'] = '<' if io['calc'].x2pitch_editor(x) <= 40 else '>'
                # redraw in the editor:
                self.draw_editor(io, self.edit_obj)
                # update in the savefile:
                for t in io['score']['events']['text']:
                    if t['tag'] == self.edit_obj['tag']:
                        t.update(self.edit_obj)
            else:
                ...
            
            # if we didn't move the text item, we open the edit dialog
            if self.edit_obj:
                if self.edit_obj['time'] == self.edit_time and self.edit_obj['side'] == self.edit_side:
                    
                    dialog = TextInputDialog(io['root'], text=self.edit_obj['text'], mm_from_side=self.edit_obj['mm_from_side'])
                    
                    if dialog.exec() == QDialog.DialogCode.Accepted:
                        text_input, mm_from_side = dialog.get_values()
                        
                        if text_input.strip():  # Check if text is not empty
                            
                            # update the text item:
                            self.edit_obj['text'] = text_input
                            self.edit_obj['mm_from_side'] = mm_from_side
                            
                            # redraw in the editor:
                            self.draw_editor(io, self.edit_obj)
                            
                            # update in the savefile:
                            for t in io['score']['events']['text']:
                                if t['tag'] == self.edit_obj['tag']:
                                    t.update(self.edit_obj)

            # reset edit object
            self.edit_obj = None
            self.edit_time = None
            self.edit_side = None

        # middle mouse button handling:
        elif event_type == 'middleclick':
            ...

        elif event_type == 'middleclick+move':
            ...

        elif event_type == 'middlerelease':
            ...

        # right mouse button handling:
        elif event_type == 'rightclick':
            detect = io['editor'].detect_item(
                io, float(x), float(y), event_type='text')
            if detect:
                # delete from savefile:
                io['score']['events']['text'] = [t for t in io['score']['events']['text'] if t['tag'] != detect['tag']]
                # delete from editor:
                self.delete_editor(io, detect)
            else:
                ...

        elif event_type == 'rightclick+move':
            ...

        elif event_type == 'rightrelease':
            ...

    def draw_editor(self, io, text, inselection: bool = False):
        '''draws the text element in the editor'''
        # remove old drawing if existing:
        self.delete_editor(io, text)

        # drawing logic:
        y = io['calc'].tick2y_editor(text['time'])
        if text['side'] == '<':
            x = EDITOR_LEFT + EDITOR_MARGIN - (EDITOR_MARGIN / 3)
            anchor = 'n'  # Top-left of the text
            # Use left rotation function
            io['editor'].new_text_left(x=x, y=y, text=text['text'], font='Courier New', tag=[text['tag']], anchor=anchor, size=16)

            # draw dashed time position line:
            io['editor'].new_line(x1=EDITOR_LEFT + EDITOR_MARGIN, y1=y, x2=x, y2=y,
                                  color='black', width=1, dash=(4, 2), tag=[text['tag']])
        else:
            x = EDITOR_RIGHT - EDITOR_MARGIN + (EDITOR_MARGIN / 3)
            anchor = 'n'  # Top-right of the text
            # Use right rotation function
            io['editor'].new_text_right(x=x, y=y, text=text['text'], font='Courier New', tag=[text['tag']], anchor=anchor, size=16)

            # draw dashed time position line:
            io['editor'].new_line(x1=x, y1=y, x2=EDITOR_RIGHT - EDITOR_MARGIN, y2=y,
                                  color='black', width=1, dash=(4, 2), tag=[text['tag']])

    def delete_editor(self, io, text):
        '''deletes the text element from the editor and the savefile'''
        io['editor'].delete_with_tag([text['tag']])

class TextInputDialog(QDialog):
    def __init__(self, parent=None, text="", mm_from_side=7):
        super().__init__(parent)
        self.setWindowTitle("Text Properties")
        self.setModal(True)
        self.resize(400, 150)
        
        # Create layout
        layout = QVBoxLayout()
        
        # Text input
        text_layout = QHBoxLayout()
        text_layout.addWidget(QLabel("Text:"))
        self.text_edit = QLineEdit(text)
        text_layout.addWidget(self.text_edit)
        layout.addLayout(text_layout)
        
        # mm input
        mm_layout = QHBoxLayout()
        mm_layout.addWidget(QLabel("mm from side:"))
        self.mm_spinbox = QSpinBox()
        self.mm_spinbox.setRange(1, 24)
        self.mm_spinbox.setValue(mm_from_side)
        mm_layout.addWidget(self.mm_spinbox)
        layout.addLayout(mm_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        self.ok_button = QPushButton("OK")
        self.cancel_button = QPushButton("Cancel")
        
        self.ok_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
        # Set focus to text input
        self.text_edit.setFocus()
        
        # Make Enter key accept the dialog
        self.ok_button.setDefault(True)
    
    def get_values(self):
        """Returns (text, semitones) tuple"""
        return self.text_edit.text(), self.mm_spinbox.value()