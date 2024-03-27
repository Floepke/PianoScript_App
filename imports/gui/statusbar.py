

class StatusBar:

    def __init__(self, io):

        self.io = io

    def set_message(self, message='', duration=0):
        '''
            This function takes care of directly showing the given text in the statusbar
            as well displaying usefull default information.
            - AutoSave on/off
            - AutoEngrave on/off
        '''
        if self.io['auto_save']:
            asave_mode = '(Auto_save) | '
        else:
            asave_mode = ''

        if self.io['auto_engrave']:
            aengrave_mode = '(Auto_engrave) | '
        else:
            aengrave_mode = ''
        
        message = asave_mode + aengrave_mode + message

        self.io['gui'].main.statusBar().showMessage(message, 0)
        self.io['app'].processEvents()
