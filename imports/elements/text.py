from PySide6.QtWidgets import QFontDialog


class Text:

    @staticmethod
    def tool(io, event_type: str, x: int, y: int):
        '''handles the mouse handling of the text tool'''

        # left mouse button handling:
        if event_type == 'leftclick':
            detect = io['editor'].detect_item(
                io, float(x), float(y), event_type='text')
            if detect:
                print(detect)
            else:
                ok, font = QFontDialog.getFont()

        elif event_type == 'leftclick+move':
            ...

        elif event_type == 'leftrelease':
            ...

        # middle mouse button handling:
        elif event_type == 'middleclick':
            ...

        elif event_type == 'middleclick+move':
            ...

        elif event_type == 'middlerelease':
            ...

        # right mouse button handling:
        elif event_type == 'rightclick':
            ...

        elif event_type == 'rightclick+move':
            ...

        elif event_type == 'rightrelease':
            ...

    @staticmethod
    def draw_editor(io, text):

        ...

    @staticmethod
    def delete_editor(io, text):
        io['editor'].delete_with_tag([text['tag']])
