# imports   
import copy

class CtlZ:
    def __init__(self, io):
        self.io = io

        self.buffer = [copy.deepcopy(self.io['score'])]
        self.index = 0
        self.max_ctlz_num = 32

    def reset_ctlz(self):
        # use this if we load a new or existing project
        self.buffer = [copy.deepcopy(self.io['score'])]
        self.index = 0

    def add_ctlz(self):

        # check if there is a change in the score
        if self.io['score'] == self.buffer[self.index]:
            # no change, do nothing
            return
        
        # if we are in the past(undo/redo):
        if not self.index == len(self.buffer) - 1:    
            self.buffer = self.buffer[:self.index + 1]

        # Add a new version of the score to the buffer
        self.buffer.append(copy.deepcopy(self.io['score']))

        # undo limit
        if len(self.buffer) > self.max_ctlz_num:
            self.buffer.pop(0)
        
        self.index = len(self.buffer) - 1

    def undo(self): 
        print('undo')
        
        # load undo version
        self.index -= 1
        if self.index < 0:
            self.index = 0
        self.io['score'] = copy.deepcopy(self.buffer[self.index])

        # update editor and engraver
        self.io['maineditor'].update('ctlz')
        #self.io['engraver'].trigger_render()

    def redo(self):
        print('redo')

        # load redo version
        self.index += 1
        if self.index > len(self.buffer) - 1:
            self.index = len(self.buffer) - 1
        self.io['score'] = copy.deepcopy(self.buffer[self.index])

        # update editor and engraver
        self.io['maineditor'].update('ctlz')
        #self.io['engraver'].trigger_render()