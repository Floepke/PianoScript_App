from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


@dataclass
class AppState:
    """Per-project UI/app state persisted in .piano files."""
    editor_scroll_pos: int = 0
    snap_base: int = 8
    snap_divide: int = 1
    selected_tool: str = "note"
    center_playhead_enabled: bool = True
    playback_type: str = "midi_port"
    send_midi_transport: bool = True
    midi_out_port: str = ""
    audio_output_device: str = ""
    synth_left_wavetable: List[float] = field(default_factory=list)
    synth_right_wavetable: List[float] = field(default_factory=list)
    synth_attack: float = 0.005
    synth_decay: float = 0.05
    synth_sustain: float = 0.6
    synth_release: float = 0.1
    synth_gain: float = 0.35
    synth_humanize_cents: float = 3.0
    synth_humanize_interval_s: float = 1.0
