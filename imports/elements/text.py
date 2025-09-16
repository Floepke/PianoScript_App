from imports.utils.savefilestructure import SaveFileStructureSource
from PySide6.QtWidgets import QInputDialog
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
                # ask for text input
                text_input, ok = QInputDialog.getText(io['root'], 'Enter your text', 'Enter your text or dynamic direction for the music:')

                if ok and text_input != '':
                    # create new text item:
                    new = SaveFileStructureSource.new_text(
                        tag='text' + str(io['calc'].add_and_return_tag()),
                        time=io['calc'].y2tick_editor(y, snap=True),
                        staff=io['selected_staff'],
                        text=text_input, # ask_string
                        side='<' if io['calc'].x2pitch_editor(x) <= 40 else '>'
                    )

                    # draw in the editor:
                    self.draw_editor(io, new)

                    # add to savefile:
                    io['score']['events']['text'].append(new)
                else:
                    ...

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
                    text_input, ok = QInputDialog.getText(io['root'], 'Edit your text', 'Edit your text or dynamic direction for the music:', text=self.edit_obj['text'])

                    if ok and text_input != '':
                        self.edit_obj['text'] = text_input
                        # redraw in the editor:
                        self.draw_editor(io, self.edit_obj)
                        # update in the savefile:
                        for t in io['score']['events']['text']:
                            if t['tag'] == self.edit_obj['tag']:
                                t.update(self.edit_obj)
                    else:
                        ...

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
