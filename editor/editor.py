from __future__ import annotations
from typing import Optional, Tuple, Dict, Type
from PySide6 import QtCore

from editor.tool.base_tool import BaseTool
from editor.tool_manager import ToolManager
# Import tool templates
from editor.tool.beam_tool import BeamTool
from editor.tool.count_line_tool import CountLineTool
from editor.tool.end_repeat_tool import EndRepeatTool
from editor.tool.grace_note_tool import GraceNoteTool
from editor.tool.line_break_tool import LineBreakTool
from editor.tool.note_tool import NoteTool
from editor.tool.pedal_tool import PedalTool
from editor.tool.slur_tool import SlurTool
from editor.tool.start_repeat_tool import StartRepeatTool
from editor.tool.text_tool import TextTool
from editor.tool.base_grid_tool import BaseGridTool
from editor.undo_manager import UndoManager
from file_model.SCORE import SCORE
from utils.CONSTANT import EDITOR_LAYERING, QUARTER_NOTE_UNIT
from editor.drawers.stave_drawer import StaveDrawerMixin
from editor.drawers.snap_drawer import SnapDrawerMixin
from editor.drawers.grid_drawer import GridDrawerMixin
from editor.drawers.note_drawer import NoteDrawerMixin
from editor.drawers.grace_note_drawer import GraceNoteDrawerMixin
from editor.drawers.beam_drawer import BeamDrawerMixin
from editor.drawers.pedal_drawer import PedalDrawerMixin
from editor.drawers.text_drawer import TextDrawerMixin
from editor.drawers.slur_drawer import SlurDrawerMixin
from editor.drawers.start_repeat_drawer import StartRepeatDrawerMixin
from editor.drawers.end_repeat_drawer import EndRepeatDrawerMixin
from editor.drawers.count_line_drawer import CountLineDrawerMixin
from editor.drawers.line_break_drawer import LineBreakDrawerMixin


class Editor(QtCore.QObject,
             StaveDrawerMixin,
             SnapDrawerMixin,
             GridDrawerMixin,
             NoteDrawerMixin,
             GraceNoteDrawerMixin,
             BeamDrawerMixin,
             SlurDrawerMixin,
             TextDrawerMixin,
             PedalDrawerMixin,
             StartRepeatDrawerMixin,
             EndRepeatDrawerMixin,
             CountLineDrawerMixin,
             LineBreakDrawerMixin):
    """Main editor class: routes UI events to the current tool.

    Handles click vs drag classification using a 3px threshold.
    """

    DRAG_THRESHOLD: int = 3

    def __init__(self, tool_manager: ToolManager):
        super().__init__()
        self._tm = tool_manager
        self._tool: BaseTool = BaseGridTool()  # default tool
        self._undo = UndoManager()
        self._file_manager = None
        self._score = None
        self._tool_classes: Dict[str, Type[BaseTool]] = {
            'beam': BeamTool,
            'count_line': CountLineTool,
            'end_repeat': EndRepeatTool,
            'grace_note': GraceNoteTool,
            'line_break': LineBreakTool,
            'note': NoteTool,
            'pedal': PedalTool,
            'slur': SlurTool,
            'start_repeat': StartRepeatTool,
            'text': TextTool,
            'base_grid': BaseGridTool,
        }
        self._tm.set_tool(self._tool)

        # Press/drag state
        self._left_pressed: bool = False
        self._right_pressed: bool = False
        self._press_pos: Tuple[float, float] = (0.0, 0.0)
        self._dragging_left: bool = False
        self._dragging_right: bool = False

        # layout metrics (mm)
        self.margin: float = None
        self.editor_height: float = None
        self.stave_width: float = None
        self.semitone_width: float = None

        # colors
        self.notation_color: Tuple[float, float, float, float] = (0.0, 0.0, 0.05, 1.0)

        # 
        # snap size in time units (default matches SnapSizeSelector: base=8, divide=1 -> 128)
        self.snap_size_units: float = (QUARTER_NOTE_UNIT * 4.0) / 8.0

    # ---- Drawing via mixins ----
    def draw_background_gray(self, du) -> None:
        """Fill the current page with print-view grey (#7a7a7a)."""
        w_mm, h_mm = du.current_page_size_mm()
        grey = (200, 240, 240, 1.0)
        du.add_rectangle(0.0, 0.0, w_mm, h_mm, stroke_color=None, fill_color=grey, id=0, tags=["background"])

    def draw_all(self, du) -> None:
        """Invoke drawer mixin methods; layer order is enforced by DrawUtil tags.

        We simply call all drawer methods; DrawUtil sorts items by tag layering.
        """
        methods = [
            getattr(self, 'draw_snap', None),
            getattr(self, 'draw_grid', None),
            getattr(self, 'draw_stave', None),
            getattr(self, 'draw_note', None),
            getattr(self, 'draw_grace_note', None),
            getattr(self, 'draw_beam', None),
            getattr(self, 'draw_pedal', None),
            getattr(self, 'draw_text', None),
            getattr(self, 'draw_slur', None),
            getattr(self, 'draw_start_repeat', None),
            getattr(self, 'draw_end_repeat', None),
            getattr(self, 'draw_count_line', None),
            getattr(self, 'draw_line_break', None),
        ]
        for fn in methods:
            if callable(fn):
                fn(du)

    def _calculate_layout(self, view_width_mm: float) -> None:
        """Compute editor-specific layout based on the current view width.

        - margin: 1/10 of the width
        - stave width: width - 2*margin
        - semitone spacing: stave width / (PIANO_KEY_AMOUNT - 1)
        """
        from utils.CONSTANT import PIANO_KEY_AMOUNT
        w = max(1.0, float(view_width_mm))
        margin = w / 6
        self.margin = margin
        self.stave_width = w - 2.0 * margin
        self.semitone_width = self.stave_width / float(max(1, PIANO_KEY_AMOUNT - 1))
        # Ensure editor_height reflects the current SCORE content height in mm
        self.editor_height = self._calc_editor_height()

    def set_tool_by_name(self, name: str) -> None:
        cls = self._tool_classes.get(name)
        if cls is None:
            return
        self._tool = cls()
        self._tm.set_tool(self._tool)

    def set_score(self, score):
        # Set an explicit score model when not using FileManager
        self._score = score

    # Model provider for undo snapshots
    def set_file_manager(self, fm) -> None:
        """Provide FileManager so we can snapshot/restore SCORE for undo/redo."""
        self._file_manager = fm
        # Initialize undo with the initial model state
        if self._file_manager is not None:
            self._undo.reset_initial(self._file_manager.current())

    def current_score(self):
        """Return the current SCORE: prefer FileManager; fall back to explicit _score."""
        if self._file_manager is not None:
            return self._file_manager.current()
        return getattr(self, "_score", None)

    def _snapshot_if_changed(self, coalesce: bool = False, label: str = "") -> None:
        if self._file_manager is None:
            return
        score = self._file_manager.current()
        if coalesce:
            self._undo.capture_coalesced(score, label)
        else:
            self._undo.capture(score, label)
        # Autosave after every captured snapshot/change of model
        self._file_manager.autosave_current()

    # Public undo/redo (optional consumers can bind Ctrl+Z / Ctrl+Shift+Z)
    def undo(self) -> None:
        if self._file_manager is None:
            return
        snap = self._undo.undo()
        if snap is not None:
            self._file_manager.replace_current(snap)

    def redo(self) -> None:
        if self._file_manager is None:
            return
        snap = self._undo.redo()
        if snap is not None:
            self._file_manager.replace_current(snap)

    '''
        ---- Mouse event routing ----
    '''
    def mouse_press(self, button: int, x: float, y: float) -> None:
        if button == 1:
            self._left_pressed = True
            self._dragging_left = False
            self._press_pos = (x, y)
            self._tool.on_left_press(x, y)
            # Begin potential grouped action (e.g., drag)
            self._undo.begin_group("left")
        elif button == 2:
            self._right_pressed = True
            self._dragging_right = False
            self._press_pos = (x, y)
            self._tool.on_right_press(x, y)
            self._undo.begin_group("right")

    def mouse_move(self, x: float, y: float, dx: float, dy: float) -> None:
        if self._left_pressed:
            if not self._dragging_left and (abs(dx) > self.DRAG_THRESHOLD or abs(dy) > self.DRAG_THRESHOLD):
                self._dragging_left = True
                self._tool.on_left_drag_start(x, y)
            if self._dragging_left:
                self._tool.on_left_drag(x, y, dx, dy)
                # Do not capture multiple intermediate drag snapshots
        elif self._right_pressed:
            if not self._dragging_right and (abs(dx) > self.DRAG_THRESHOLD or abs(dy) > self.DRAG_THRESHOLD):
                self._dragging_right = True
                self._tool.on_right_drag_start(x, y)
            if self._dragging_right:
                self._tool.on_right_drag(x, y, dx, dy)
                # Skip intermediate drag snapshots
        else:
            self._tool.on_mouse_move(x, y)

    def mouse_release(self, button: int, x: float, y: float) -> None:
        if button == 1:
            if self._dragging_left:
                self._tool.on_left_drag_end(x, y)
                # Capture a single coalesced snapshot for the whole drag
                self._snapshot_if_changed(coalesce=True, label="left_drag")
                self._undo.commit_group()
            else:
                # Click if moved <= threshold
                px, py = self._press_pos
                if (abs(x - px) <= self.DRAG_THRESHOLD and abs(y - py) <= self.DRAG_THRESHOLD):
                    self._tool.on_left_click(x, y)
                # Capture click changes (non-coalesced)
                self._snapshot_if_changed(coalesce=False, label="left_click")
            self._tool.on_left_unpress(x, y)
            self._left_pressed = False
            self._dragging_left = False
        elif button == 2:
            if self._dragging_right:
                self._tool.on_right_drag_end(x, y)
                self._snapshot_if_changed(coalesce=True, label="right_drag")
                self._undo.commit_group()
            else:
                px, py = self._press_pos
                if (abs(x - px) <= self.DRAG_THRESHOLD and abs(y - py) <= self.DRAG_THRESHOLD):
                    self._tool.on_right_click(x, y)
                self._snapshot_if_changed(coalesce=False, label="right_click")
            self._tool.on_right_unpress(x, y)
            self._right_pressed = False
            self._dragging_right = False

    def mouse_double_click(self, button: int, x: float, y: float) -> None:
        if button == 1:
            self._tool.on_left_double_click(x, y)
        elif button == 2:
            self._tool.on_right_double_click(x, y)

    '''
        ---- Editor drawer mixin helper methods ----
    '''
    def _calc_score_time(self) -> int:
        """Return the total length of the current SCORE in ticks."""
        score: SCORE = self.current_score()
        
        length_ticks = 0
        for bg in score.base_grid:
            measure_length = bg.numerator * (4.0 / bg.denominator) * bg.measure_amount * QUARTER_NOTE_UNIT
            length_ticks += measure_length
        return length_ticks
    
    def _calc_editor_height(self) -> float:
        """Calculate the total height of the editor content in mm.

        Height is based on the total score time scaled by the editor zoom, plus
        top/bottom spacing using the editor's margin value. This ensures drawers
        can rely on `self.editor_height` for vertical layout and that DrawUtil
        uses a matching page height for scrolling.
        """
        total_time_ticks = float(self._calc_score_time())
        score: SCORE | None = self.current_score()
        zoom_mm_per_quarter: float = score.editor.zoom_mm_per_quarter
        stave_length_mm = (total_time_ticks / float(QUARTER_NOTE_UNIT)) * zoom_mm_per_quarter
        top_bottom_mm = float(self.margin or 0.0) * 2.0
        height_mm = max(10.0, stave_length_mm + top_bottom_mm)
        return height_mm

    # ---- External controls ----
    def set_snap_size_units(self, units: float) -> None:
        try:
            self.snap_size_units = max(0.0, float(units))
        except Exception:
            pass
