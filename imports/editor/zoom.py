class Zoom:
    def __init__(self, io):
        self.io = io

        # connect zoom actions
        self.io['gui'].zoom_in_action.triggered.connect(
            lambda: zoom_in(self.io))
        self.io['gui'].zoom_out_action.triggered.connect(
            lambda: zoom_out(self.io))

        # connect zoom shortcuts
        self.io['gui'].zoom_in_action.setShortcut('=')
        self.io['gui'].zoom_out_action.setShortcut('-')


def zoom_in(io):
    '''zooms in the editor'''
    io['score']['properties']['editor_zoom'] += 10
    if io['score']['properties']['editor_zoom'] > 1000:
        io['score']['properties']['editor_zoom'] = 1000
    io['maineditor'].update('zoom')


def zoom_out(io):
    '''zooms out the editor'''
    io['score']['properties']['editor_zoom'] -= 10
    if io['score']['properties']['editor_zoom'] < 10:
        io['score']['properties']['editor_zoom'] = 10
    io['maineditor'].update('zoom')
