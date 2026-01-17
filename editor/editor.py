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
from utils.CONSTANT import EDITOR_DRAWING_ORDER
from editor.drawers.stave_drawer import StaveDrawerMixin
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
        self.margin: float = 10.0
        self.stave_width: float = 100.0
        self.semitone_width: float = 1.0

    # ---- Drawing via mixins ----
    def draw_background_gray(self, du) -> None:
        """Fill the current page with print-view grey (#7a7a7a)."""
        w_mm, h_mm = du.current_page_size_mm()
        grey = (122/255.0, 122/255.0, 122/255.0, 1.0)
        du.add_rectangle(0.0, 0.0, w_mm, h_mm, stroke_color=None, fill_color=grey, id=0, tags=["background"])

    def draw_all(self, du) -> None:
        """Invoke drawer mixin methods in EDITOR_DRAWING_ORDER."""
        for name in EDITOR_DRAWING_ORDER:
            method = {
                'stave': self.draw_stave,
                'grid': self.draw_grid,
                'note': self.draw_note,
                'grace_note': self.draw_grace_note,
                'beam': self.draw_beam,
                'pedal': self.draw_pedal,
                'text': self.draw_text,
                'slur': self.draw_slur,
                'start_repeat': self.draw_start_repeat,
                'end_repeat': self.draw_end_repeat,
                'count_line': self.draw_count_line,
                'line_break': self.draw_line_break,
            }.get(name)
            if method is not None:
                method(du)

    def _calculate_layout(self, view_width_mm: float) -> None:
        """Compute editor-specific layout based on the current view width.

        - margin: 1/10 of the width
        - stave width: width - 2*margin
        - semitone spacing: stave width / (PIANO_KEY_AMOUNT - 1)
        """
        from utils.CONSTANT import PIANO_KEY_AMOUNT
        w = max(1.0, float(view_width_mm))
        margin = w / 10.0
        self.margin = margin
        self.stave_width = max(1.0, w - 2.0 * margin)
        self.semitone_width = self.stave_width / float(max(1, PIANO_KEY_AMOUNT - 1))

    def set_tool_by_name(self, name: str) -> None:
        cls = self._tool_classes.get(name)
        if cls is None:
            return
        self._tool = cls()
        self._tm.set_tool(self._tool)

    # Model provider for undo snapshots
    def set_file_manager(self, fm) -> None:
        """Provide FileManager so we can snapshot/restore SCORE for undo/redo."""
        self._file_manager = fm
        # Initialize undo with the initial model state
        if self._file_manager is not None:
            self._undo.reset_initial(self._file_manager.current())

    def current_score(self):
        """Return the current SCORE from FileManager if available."""
        if self._file_manager is not None:
            return self._file_manager.current()
        return None

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

    # UI event forwarding APIs for the view
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
