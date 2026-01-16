from __future__ import annotations
from typing import Optional, List
import copy

class UndoManager:
    """
    Simple undo/redo manager for SCORE snapshots with drag-coalescing.

    - Stores deep-copied SCORE instances
    - begin_group()/commit_group() coalesce noisy intermediate states (e.g., drags)
    - capture() records a new snapshot when model differs from last
    - capture_coalesced() replaces the tail snapshot within an active group
    """

    def __init__(self, limit: int = 200) -> None:
        self._history: List[object] = []  # SCORE instances
        self._index: int = -1
        self._redo: List[object] = []
        self._group_open: bool = False
        self._limit = max(10, int(limit))

    def reset_initial(self, score) -> None:
        self._history = [copy.deepcopy(score)]
        self._index = 0
        self._redo = []
        self._group_open = False

    def begin_group(self, label: str = "") -> None:
        self._group_open = True

    def commit_group(self) -> None:
        self._group_open = False

    def _current(self) -> Optional[object]:
        if 0 <= self._index < len(self._history):
            return self._history[self._index]
        return None

    def _is_different(self, score) -> bool:
        cur = self._current()
        if cur is None:
            return True
        # Compare by identity; SCORE lacks equality, so approximate by json dict
        try:
            # If both objects are the same instance, skip
            if cur is score:
                return False
        except Exception:
            pass
        # Fallback: always treat as different and rely on coalescing to limit noise
        return True

    def _push(self, score) -> None:
        snap = copy.deepcopy(score)
        # Drop redo branch on new edit
        self._redo.clear()
        # If we have extra entries beyond index, truncate forward history
        self._history = self._history[: self._index + 1]
        self._history.append(snap)
        self._index = len(self._history) - 1
        # Enforce limit (drop oldest)
        if len(self._history) > self._limit:
            drop = len(self._history) - self._limit
            self._history = self._history[drop:]
            self._index = max(0, self._index - drop)

    def capture(self, score, label: str = "") -> None:
        if self._is_different(score):
            self._push(score)

    def capture_coalesced(self, score, label: str = "") -> None:
        if not self._group_open:
            # Fallback to normal capture
            return self.capture(score, label)
        if self._is_different(score):
            snap = copy.deepcopy(score)
            # Replace tail if we're already at the end, else append
            if self._index == len(self._history) - 1 and self._index >= 0:
                self._history[self._index] = snap
            else:
                self._push(score)

    def can_undo(self) -> bool:
        return self._index > 0

    def can_redo(self) -> bool:
        return self._index < (len(self._history) - 1)

    def undo(self) -> Optional[object]:
        if not self.can_undo():
            return None
        self._redo.append(self._history[self._index])
        self._index -= 1
        return self._current()

    def redo(self) -> Optional[object]:
        if not self.can_redo():
            return None
        self._index += 1
        return self._current()
