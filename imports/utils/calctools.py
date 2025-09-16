from imports.utils.constants import *
import os, json

class CalcTools:
    '''
        The CalcTools class contains all the methods that calculate basic things about the score.
        it's a separate class because I don't want to clutter the editor class with these methods.
        It are little solutions to little problems.
        Included methods:
            - get_total_score_ticks(); returns the total number of ticks in the score
            - get_measure_length(grid); returns the length of a measure in pianoticks based on the grid message from the score file
            - tick2y_editor(time); converts pianoticks into y position on the editor
            - pitch2x_editor(pitch); converts pitch into x position on the editor
            - x2pitch_editor(x); converts x position on the editor into pitch
            - y2tick_editor(y); converts y position on the editor into pianoticks
            - add_and_return_tag(); creates a new tag number and returns it
            - renumber_tags(); renumbers the event tags starting from zero again. It's needed if we load a new or existing project.
    '''

    def __init__(self, io):
        self.io = io

    def get_total_score_ticks(self):
        '''returns the total number of ticks from the entire score / position of the endbarline'''

        total_ticks = 0

        for gr in self.io['score']['events']['grid']:

            # calculate the length of one measure based on the numerator and denominator.
            numerator = gr['numerator']
            denominator = gr['denominator']
            measure_length = int(
                numerator * ((QUARTER_PIANOTICK * 4) / denominator))
            amount = gr['amount']

            # add the length of the grid message
            total_ticks += measure_length * amount

        return total_ticks

    @staticmethod
    def get_measure_length(grid):
        '''
            returns the length of a measure in pianoticks
            based on the grid message from the score file
        '''
        return int(grid['numerator'] * (QUARTER_PIANOTICK * (4 / grid['denominator'])))

    def tick2y_editor(self, time):
        '''converts pianoticks into y position on the editor'''
        return time * (self.io['score']['properties']['editor_zoom'] / QUARTER_PIANOTICK) + EDITOR_MARGIN

    def y2tick_editor(self, y, snap=False):
        '''converts y position on the editor into pianoticks'''
        editor_zoom = self.io['score']['properties']['editor_zoom']
        y = (y - EDITOR_MARGIN) * (QUARTER_PIANOTICK / editor_zoom)
        if y < 0:
            y = -FRACTION

        if snap:
            # Snap to grid starting from the top of the editor
            grid_size = self.io['snap_grid']
            y = round((y - (grid_size / 2)) / grid_size) * grid_size

        return y

    @staticmethod
    def pitch2x_editor(pitch):
        '''converts pitch into x position on the editor'''

        # evaluate pitch (between 1 and 88) and create initial x position
        pitch = max(1, min(88, pitch))
        x = EDITOR_LEFT + EDITOR_MARGIN - STAFF_X_UNIT_EDITOR

        # 21 is A0, 109 is C8 (based on midi note numbers); 12 is octave, 0 is C, 5 is F
        for n in range(1, 89):
            x += STAFF_X_UNIT_EDITOR if n % 12 in [4,
                                                   9] else STAFF_X_UNIT_EDITOR / 2
            if pitch == n:
                break

        return x
    
    @staticmethod
    def x2xunits_editor(x, snap=False):
        '''converts the x (mouse)position to the distance from the c4 position on the staff in STAFF_X_UNIT_EDITOR floats'''
        c4_xpos = CalcTools.pitch2x_editor(40) # key 40 = c4
        out = (x - c4_xpos) / STAFF_X_UNIT_EDITOR
        if snap:
            out = round(out * 2) / 2
        return out
    
    @staticmethod
    def units2x_editor(value):
        c4_xpos = CalcTools.pitch2x_editor(40)
        return (c4_xpos + (value * STAFF_X_UNIT_EDITOR))

    @staticmethod
    def x2pitch_editor(x):
        '''converts x position on the editor into pitch'''

        # make a list of all x key center positions
        x_positions = []
        x_pos = EDITOR_LEFT + EDITOR_MARGIN - STAFF_X_UNIT_EDITOR
        for n in range(1, 89):
            x_pos += STAFF_X_UNIT_EDITOR if n % 12 in [
                4, 9] else STAFF_X_UNIT_EDITOR / 2
            x_positions.append(x_pos)

        # find the closest mouse x position based from the x_positions list
        closest_x = min(x_positions, key=lambda y: abs(y-x))
        closest_x_index = x_positions.index(closest_x)
        return closest_x_index + 1

    def add_and_return_tag(self):
        '''creates a new tag number and returns it'''
        tag = self.io['new_tag']
        self.io['new_tag'] += 1
        return tag

    def renumber_tags(self):
        '''
            This function takes the score and
            renumbers the event tags starting
            from zero again. It's needed if we
            load a new or existing project.
        '''
        for k in self.io['score']['events'].keys():  # loop through all event types
            # loop through all objects of one event type
            for obj in self.io['score']['events'][k]:
                if not 'tag' in obj:
                    continue  # to skip any event that doesn't have a tag
                if obj['tag'] == 'lockedlinebreak':
                    continue  # to prevent that only the first linebreak doesn't get deleted later in the program
                obj['tag'] = f"{k}{self.io['new_tag']}"
                if k in self.io['selection']['copy_types']:
                    obj['tag'] = obj['tag']
                self.io['new_tag'] += 1

    @staticmethod
    def update_viewport_ticks(io):
        gui = io['gui']
        editor_view = gui.editor_view
        editor_scene = gui.editor_scene
        editor_zoom = io['score']['properties']['editor_zoom']
        viewport = io['viewport']

        scale_factor = editor_view.transform().m11()
        px_scene_height = editor_scene.sceneRect().height()

        if px_scene_height == 0:
            px_scene_height = 1  # Fix for division by zero

        ticks_scene_height = (
            px_scene_height / (QUARTER_PIANOTICK / editor_zoom)) * scale_factor
        px_view_height = editor_view.height()
        tick_view_height = (
            px_view_height * (QUARTER_PIANOTICK / editor_zoom)) / scale_factor
        tick_editor_margin = io['calc'].y2tick_editor(
            EDITOR_MARGIN + EDITOR_MARGIN)

        # Calculate the toptick and bottomtick
        toptick = editor_view.verticalScrollBar().value() * (px_scene_height /
                                                             ticks_scene_height) - tick_editor_margin
        bottomtick = toptick + tick_view_height

        # Update the viewport toptick and bottomtick
        viewport['toptick'] = toptick - 1
        viewport['bottomtick'] = bottomtick + 1

    # process grid selector
    def process_grid(self):

        # get selected radio button/length
        radio = None
        for i in range(self.io['gui'].radio_layout.count()):
            radio_button = self.io['gui'].radio_layout.itemAt(i).widget()
            if radio_button.isChecked():
                radio = i
                break

        # get selected divide and multiply
        divide = self.io['gui'].divide_spin_box.value()
        multiply = int(self.io['gui'].multiply_spin_box.value())

        # calculate the snap grid
        length_dict = {
            0: 1024,
            1: 512,
            2: 256,
            3: 128,
            4: 64,
            5: 32,
            6: 16,
            7: 8
        }
        self.io['snap_grid'] = length_dict[radio] / divide * multiply

        # update the the label
        self.io['gui'].grid_selector_label.setText(
            f"Tick: {self.io['snap_grid']}")

    # get barline ticks
    def get_barline_ticks(self):
        '''returns a list with all barline ticks'''
        time = 0
        barline_ticks = []
        for grid in self.io['score']['events']['grid']:
            measure_length = grid['numerator'] * (QUARTER_PIANOTICK * (4 / grid['denominator']))
            for i in range(grid['amount']):
                barline_ticks.append(time)
                time += measure_length
            
        return barline_ticks

    def get_measure_number(self, time):
        '''returns the measure number based on the time'''
        barline_ticks = self.get_barline_ticks()
        for i in barline_ticks:
            if time < i:
                return barline_ticks.index(i)

    def get_measure_tick(self, time) -> tuple[int, int, int]:
        ''' returns the measure number and the tick in that measure '''

        grids = self.io['score']['events']['grid']
        pos = 0
        measure = 1
        start = 0
        count = 0

        for gr in grids:
            # calculate the length of one tick for this grid
            numerator = gr['numerator']
            denominator = gr['denominator']
            amount = int(gr['amount'])

            tick_length = int(((QUARTER_PIANOTICK * 4) / denominator))
            for cnt in range(amount):
                count = 0
                start = pos
                for num in range(numerator):
                    pos += tick_length

                    count += 1
                    if time < pos:
                        return measure, time - start, count

                measure += 1

        return measure, time - start, count
    
    def ensure_json(self, json_path, fallback_json):
        '''This function checks: 
            1. if the file_path exists
            2. if not it creates the directory
            3. places the file in the new or already existing directory'''

        json_path = os.path.expanduser(json_path)
        dir = os.path.dirname(json_path)
        if not os.path.exists(dir):
            os.makedirs(dir)
        if not os.path.exists(json_path):
            with open(json_path, 'w') as file:
                json.dump(fallback_json, file, indent=4)
        return json_path
    
    def bezier_curve(self, p0, p1, p2, p3, resolution=10):
        points = []
        for t in range(resolution + 1):
            t = t / resolution
            x = (1 - t) ** 3 * p0[0] + 3 * (1 - t) ** 2 * t * p1[0] + 3 * (1 - t) * t ** 2 * p2[0] + t ** 3 * p3[0]
            y = (1 - t) ** 3 * p0[1] + 3 * (1 - t) ** 2 * t * p1[1] + 3 * (1 - t) * t ** 2 * p2[1] + t ** 3 * p3[1]
            points.append((x, y))
        return points
