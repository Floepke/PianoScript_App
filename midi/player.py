from __future__ import annotations
from typing import Optional

from utils.CONSTANT import QUARTER_NOTE_UNIT

try:
    from synth.wavetable_synth import WavetableSynth
except Exception:
    WavetableSynth = None


class Player:
    """Playback of `SCORE` using the custom wavetable synth only."""

    def __init__(self) -> None:
        self._wt: Optional[WavetableSynth] = WavetableSynth() if WavetableSynth is not None else None

    def set_wavetables(self, left, right) -> None:
        if self._wt is None:
            return
        self._wt.set_wavetables(left, right)

    def set_adsr(self, attack_seconds: float, decay_seconds: float, sustain_level: float, release_seconds: float) -> None:
        if self._wt is None:
            return
        self._wt.set_adsr(attack_seconds, decay_seconds, sustain_level, release_seconds)

    def play_score(self, score) -> None:
        if self._wt is None:
            return
        self._wt.play_score(score)

    def stop(self) -> None:
        if self._wt is not None:
            self._wt.stop()
