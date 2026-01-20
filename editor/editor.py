from __future__ import annotations
from typing import Optional, Tuple, Dict, Type, TYPE_CHECKING
import math, bisect
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
from utils.CONSTANT import BE_KEYS, QUARTER_NOTE_UNIT
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
from utils.CONSTANT import PIANO_KEY_AMOUNT
from utils.operator import Operator

if TYPE_CHECKING:
    from editor.tool.base_tool import BaseTool
    from ui.widgets.draw_util import DrawUtil


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
        self.semitone_dist: float = None

        # colors
        self.notation_color: Tuple[float, float, float, float] = (0.0, 0.0, 0.05, 1.0)
        self.accent_color: Tuple[float, float, float, float] = (0.8, 0.2, 0.2, 1.0)
        self.selection_color: Tuple[float, float, float, float] = (0.2, 0.6, 1.0, 0.3)

        # snap size in time units (default matches SnapSizeSelector: base=8, divide=1 -> 128)
        self.snap_size_units: float = (QUARTER_NOTE_UNIT * 4.0) / 8.0

        # Cache for key x-positions (index by piano key number 1..88)
        self._x_positions: Optional[list[float]] = None

        # View metrics for fast pixel↔mm conversions
        self._px_per_mm: float = 1.0            # device px per mm
        self._widget_px_per_mm: float = 1.0     # logical (Qt) px per mm
        self._dpr: float = 1.0                  # device pixel ratio
        # View offset in mm (top of visible clip)
        self._view_y_mm_offset: float = 0.0
        # Viewport height (mm) of the visible clip
        self._viewport_h_mm: float = 0.0

        # cursor
        self.time_cursor: Optional[float] = None
        self.mm_cursor: Optional[float] = None

        # Per-frame shared render cache (built at draw_all)
        self._draw_cache: dict | None = None

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
        # Build shared render cache for this draw pass
        self._build_render_cache()
        
        # Call drawer mixin methods in order
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

        # Clear cache after draw pass to avoid stale state
        self._draw_cache = None

    def _calculate_layout(self, view_width_mm: float) -> None:
        """Compute editor-specific layout based on the current view width.

        - margin: 1/6 of the width
        - stave width: width - 2 * margin
        - semitone spacing: stave width / (PIANO_KEY_AMOUNT - 1)
        """
        # Calculate margin
        self.margin = view_width_mm / 6
        
        # Calculate stave units
        visual_semitone_spaces = 101
        self.stave_width = view_width_mm - (2 * self.margin)
        self.semitone_dist = self.stave_width / visual_semitone_spaces
        
        # Ensure editor_height reflects the current SCORE content height in mm
        self.editor_height = self._calc_editor_height()

        # Rebuild cached x positions
        self._rebuild_x_positions()

    def _rebuild_x_positions(self) -> None:
        """Precompute x positions for keys 1..PIANO_KEY_AMOUNT with BE gap after B/E."""
        be_set = set(BE_KEYS)
        x_pos = self.margin - self.semitone_dist
        xs = [x_pos]

        for n in range(1, PIANO_KEY_AMOUNT + 1):
            # Apply extra gap AFTER B/E, i.e., when stepping from (n-1) -> n
            if (n - 1) in be_set:
                x_pos += self.semitone_dist
            # Normal semitone step
            x_pos += self.semitone_dist
            xs.append(x_pos)

        self._x_positions = xs

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
            # Update shared cursor state for guide rendering (time + mm), with snapping
            try:
                t = self.y_to_time(y)
                t = self.snap_time(t)
                self.time_cursor = t
                # Store cursor mm relative to viewport (local mm)
                abs_mm = self.time_to_mm(float(t))
                self.mm_cursor = abs_mm - float(self._view_y_mm_offset or 0.0)
            except Exception:
                pass
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
        zpq: float = score.editor.zoom_mm_per_quarter
        stave_length_mm = (total_time_ticks / float(QUARTER_NOTE_UNIT)) * zpq
        top_bottom_mm = float(self.margin or 0.0) * 2.0
        height_mm = max(10.0, stave_length_mm + top_bottom_mm)
        return height_mm

    # ---- Shared render cache ----
    def _build_render_cache(self) -> None:
        """Build per-frame cached, time-sorted viewport data for drawers.

        Cache includes:
        - viewport times (begin/end)
        - Operator(7) comparator
        - notes sorted, starts, ends
        - candidate indices ensuring notes with visible ends or spanning viewport are included
        - notes_view slice and notes grouped by hand
        - beam markers by hand (if available) and grid helpers (for future beam grouping)
        """
        score: SCORE | None = self.current_score()
        if score is None:
            self._draw_cache = None
            return

        # Compute viewport times (ticks) from mm offset and height
        try:
            top_mm = float(getattr(self, '_view_y_mm_offset', 0.0) or 0.0)
            vp_h_mm = float(getattr(self, '_viewport_h_mm', 0.0) or 0.0)
            bottom_mm = top_mm + vp_h_mm
        except Exception:
            top_mm = 0.0
            bottom_mm = 0.0
        # Small bleed similar to prior behavior
        zpq = float(score.editor.zoom_mm_per_quarter)
        bleed_mm = max(2.0, zpq * 0.25)
        time_begin = float(self.mm_to_time(top_mm - bleed_mm))
        time_end = float(self.mm_to_time(bottom_mm + bleed_mm))

        # Comparator with threshold of 7 ticks
        op = Operator(7)

        # Notes sorted by (time, pitch)
        notes = list(getattr(score.events, 'note', []) or [])
        notes_sorted = sorted(notes, key=lambda n: (float(n.time), int(n.pitch)))
        starts = [float(n.time) for n in notes_sorted]
        ends = [float(n.time + n.duration) for n in notes_sorted]

        # Candidate indices: union of ranges by start and end, plus back expansion over one viewport length
        lo_start = bisect.bisect_left(starts, time_begin)
        hi_start = bisect.bisect_right(starts, time_end)
        lo_end = bisect.bisect_left(ends, time_begin)
        hi_end = bisect.bisect_right(ends, time_end)
        viewport_len = float(max(0.0, time_end - time_begin))
        slack = float(op.threshold)
        back_lo = bisect.bisect_left(starts, float(time_begin - viewport_len - slack))
        candidate_idx_set = set(range(back_lo, hi_start)) | set(range(lo_end, hi_end))
        candidate_indices = sorted(candidate_idx_set)

        # Filtered view: will be further intersection-tested by drawers
        notes_view = [notes_sorted[i] for i in candidate_indices] if candidate_indices else []

        # Group by hand for convenience
        notes_by_hand: dict[str, list] = {}
        for m in notes_view:
            h = str(getattr(m, 'hand', '<'))
            notes_by_hand.setdefault(h, []).append(m)

        # Beam markers (optional; future use)
        beam_markers = list(getattr(score.events, 'beam', []) or [])
        beam_by_hand: dict[str, list] = {}
        for b in beam_markers:
            h = str(getattr(b, 'hand', '<'))
            beam_by_hand.setdefault(h, []).append(b)
        for h in beam_by_hand:
            beam_by_hand[h] = sorted(beam_by_hand[h], key=lambda b: float(getattr(b, 'time', 0.0)))

        # Grid helpers: absolute times (ticks) of drawn grid lines across the score
        grid_den_times: list[float] = []
        cur_t = 0.0
        for bg in getattr(score, 'base_grid', []) or []:
            # Total measure length in ticks
            measure_len_ticks = float(bg.numerator) * (4.0 / float(bg.denominator)) * float(QUARTER_NOTE_UNIT)
            # Beat length inside this measure (ticks)
            beat_len_ticks = measure_len_ticks / max(1, int(bg.numerator))
            # For each measure in this segment
            for _ in range(int(bg.measure_amount)):
                # Append grid line times for configured grid positions
                for grid in list(getattr(bg, 'grid_positions', []) or []):
                    # grid == 1 marks the barline (measure start); positions are 1-based
                    t_line = cur_t + (int(grid) - 1) * beat_len_ticks
                    grid_den_times.append(float(t_line))
                # Advance to next measure start
                cur_t += measure_len_ticks
        # Append final end barline time for completeness
        grid_den_times.append(float(cur_t))

        self._draw_cache = {
            'time_begin': time_begin,
            'time_end': time_end,
            'op': op,
            'notes_sorted': notes_sorted,
            'starts': starts,
            'ends': ends,
            'candidate_indices': candidate_indices,
            'notes_view': notes_view,
            'notes_by_hand': notes_by_hand,
            'beam_by_hand': beam_by_hand,
            'grid_den_times': grid_den_times,
        }

    # ---- External controls ----
    def set_snap_size_units(self, units: float) -> None:
        try:
            self.snap_size_units = max(0.0, float(units))
        except Exception:
            pass

    # ---- coordinate calculations ----
    def time_to_mm(self, time: float) -> float:
        """Convert time in ticks to mm position."""
        score: SCORE = self.current_score()

        # Layout metrics
        zpq = float(score.editor.zoom_mm_per_quarter)
        return self.margin + (float(time) / float(QUARTER_NOTE_UNIT)) * zpq
    
    def pitch_to_x(self, key_number: int) -> float:
        '''Convert piano key number (1-88) to X position using specific Klavarskribo spacing.'''
        # Validate key number
        if key_number < 1 or key_number > PIANO_KEY_AMOUNT:
            return 0.0
        
        # Ensure x-positions cache is built
        if self._x_positions is None:
            self._rebuild_x_positions()
        
        # Return cached x position
        return self._x_positions[key_number]

    # ---- Mouse-friendly wrappers (pixels) ----
    def time_to_y(self, ticks: float) -> float:
        """Convert time in ticks to Y position in logical (Qt) pixels."""
        mm = self.time_to_mm(ticks)
        return float(mm) * float(getattr(self, '_widget_px_per_mm', 1.0))

    def y_to_time(self, y_px: float) -> float:
        """Convert Y position in logical (Qt) pixels to time in ticks."""
        return self.px_to_time(y_px)

    def x_to_pitch(self, x_px: float) -> int:
        """Convert X position in logical (Qt) pixels to piano key number (1..88)."""
        return self.x_to_pitch_px(x_px)

    def x_to_pitch_mm(self, x_mm: float) -> int:
        """Inverse of pitch_to_x: map X in mm to nearest piano key number (1..88)."""
        import bisect
        if self._x_positions is None:
            self._rebuild_x_positions()
        xs = self._x_positions
        if x_mm <= xs[1]:
            return 1
        if x_mm >= xs[PIANO_KEY_AMOUNT]:
            return PIANO_KEY_AMOUNT
        i = bisect.bisect_left(xs, x_mm, 1, PIANO_KEY_AMOUNT + 1)
        prev_i = max(1, i - 1)
        if i > PIANO_KEY_AMOUNT:
            return prev_i
        prev_x = xs[prev_i]
        curr_x = xs[i]
        return prev_i if abs(x_mm - prev_x) <= abs(x_mm - curr_x) else i

    def x_to_pitch_px(self, x_px: float) -> int:
        """Map X in logical (Qt) pixels to piano key number using cached widget px/mm."""
        x_mm = float(x_px) / max(1e-6, self._widget_px_per_mm)
        return self.x_to_pitch_mm(x_mm)

    def mm_to_time(self, y_mm: float) -> float:
        """Convert Y in mm to time ticks (inverse of time_to_mm)."""
        score: SCORE = self.current_score()
        zpq = float(score.editor.zoom_mm_per_quarter)
        ticks = (float(y_mm) - float(self.margin)) / max(1e-6, zpq) * float(QUARTER_NOTE_UNIT)
        return max(0.0, ticks)

    def px_to_time(self, y_px: float) -> float:
        """Convert Y in logical (Qt) pixels to time ticks efficiently using cached px/mm."""
        # Convert local widget px to mm, then add current viewport clip offset
        y_mm_local = float(y_px) / max(1e-6, self._widget_px_per_mm)
        y_mm = y_mm_local + float(self._view_y_mm_offset or 0.0)
        return self.mm_to_time(y_mm)

    def set_view_metrics(self, px_per_mm: float, widget_px_per_mm: float, dpr: float) -> None:
        """Provide current view scale for fast pixel↔mm conversions."""
        self._px_per_mm = float(px_per_mm)
        self._widget_px_per_mm = float(widget_px_per_mm)
        self._dpr = float(dpr)

    def set_view_offset_mm(self, y_mm_offset: float) -> None:
        """Set the current viewport origin offset (top of clip) in mm."""
        self._view_y_mm_offset = float(y_mm_offset)
        # Recompute local mm cursor on scroll so overlays stay aligned
        if self.time_cursor is not None:
            abs_mm = self.time_to_mm(float(self.time_cursor))
            self.mm_cursor = abs_mm - float(self._view_y_mm_offset or 0.0)

    def set_viewport_height_mm(self, h_mm: float) -> None:
        """Provide the current viewport height in mm for drawer culling."""
        self._viewport_h_mm = max(0.0, float(h_mm))

    def snap_time(self, ticks: float) -> float:
        """Snap time ticks to the start of the previous snap band.

        Example: with snap size S, values in [k*S, (k+1)*S) snap to k*S.
        """
        units = max(1e-6, float(self.snap_size_units))
        ratio = float(ticks) / units
        k = math.floor(ratio + 1e-9)  # tiny epsilon to counter floating error
        return k * units

    # ---- Editor guides (tool-agnostic overlays) ----
    def draw_guides(self, du: DrawUtil) -> None:
        """Draw shared editor guides such as the horizontal time cursor.

        This runs independently of the active tool so overrides don't suppress it.
        """
        # get cursor mm position: convert local (viewport) mm -> absolute mm
        if self.mm_cursor is None:
            return
        y_mm = float(self.mm_cursor) + float(self._view_y_mm_offset or 0.0)
        
        margin = float(self.margin or 0.0)
        stave_width = float(self.stave_width or 0.0)

        # Remove previous cursor guides by tag
        du.delete_with_tag("cursor")

        # Left side of stave
        du.add_line(
            2.0,
            y_mm,
            margin,
            y_mm,
            color=(0, 0, 0, 1),
            width_mm=.75,
            dash_pattern=[0, 2],
            id=0,
            tags=["cursor"],
        )

        # Right side of stave
        du.add_line(
            margin + stave_width,
            y_mm,
            margin * 2.0 + stave_width - 2,
            y_mm,
            color=(0, 0, 0, 1),
            width_mm=.75,
            dash_pattern=[0, 2],
            id=0,
            tags=["cursor"],
        )
