from ctypes import cast
from file_model import SCORE
from ui.widgets.draw_util import DrawUtil


class GridEditorMixin:
    def draw_grid_editor_buttons(self, du: DrawUtil) -> None:
        self = cast("Editor", self)
        score: SCORE = self.current_score()

        # TODO: implement grid editor buttons drawing
        pass