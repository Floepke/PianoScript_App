from __future__ import annotations
import os
import threading
import time
from pathlib import Path
from typing import List, Optional, Tuple

import fluidsynth

# Guard against incorrect/empty fluidsynth installs (needs pyfluidsynth)
if not hasattr(fluidsynth, "Synth"):
    raise ImportError(
        "fluidsynth.Synth not found. Install pyfluidsynth (pip install pyfluidsynth) and ensure libfluidsynth is available."
    )

from utils.CONSTANT import QUARTER_NOTE_UNIT


class Player:
    """Playback of `SCORE` using a bundled FluidSynth instance."""

    def __init__(self, soundfont_path: Optional[str] = None) -> None:
        self._fs: Optional[fluidsynth.Synth] = None
        self._sfid: Optional[int] = None
        self._soundfont_path: Optional[str] = soundfont_path or self._autodetect_soundfont()
        self._pitch_offset: int = 20  # App pitch 49 == MIDI 69 (A4); MIDI = app + 20
        self._channel: int = 0
        self._gain: float = 0.35
        self._thread: Optional[threading.Thread] = None
        self._running: bool = False
        self._bpm: float = 120.0
        self._t0: float = 0.0
        self._start_units: float = 0.0
        self._last_event_count: int = 0
        self._off_epsilon_sec: float = 0.003  # ~3 ms safety gap before offs
        self._min_duration_units: float = 4.0
        self._init_synth()

    # ------------------------------------------------------------------
    # FluidSynth setup
    # ------------------------------------------------------------------
    def _autodetect_soundfont(self) -> Optional[str]:
        """Return the first existing SF2 path from common system/user locations."""
        candidates: list[Path] = []
        env_sf = os.environ.get("KEYTAB_SOUNDFONT")
        if env_sf:
            candidates.append(Path(env_sf))
        # System defaults
        candidates.append(Path("/usr/share/sounds/sf2/FluidR3_GM.sf2"))
        candidates.append(Path("/Library/Audio/Sounds/Banks/FluidR3_GM.sf2"))
        candidates.append(Path("/System/Library/Components/CoreAudio.component/Contents/SharedSupport/Resources/gs_instrument.sf2"))
        for p in candidates:
            if p.expanduser().is_file():
                return str(p.expanduser())
        return None

    def _init_synth(self) -> None:
        if self._fs is not None:
            try:
                self._fs.delete()
            except Exception:
                pass
        self._fs = fluidsynth.Synth()
        # Prefer PulseAudio for desktop environments; fall back to FluidSynth default
        started = False
        for drv in ("pulseaudio", None):
            try:
                self._fs.start(driver=drv)
                started = True
                break
            except Exception:
                continue
        if not started:
            # Last-resort fallback avoids raising during init
            try:
                self._fs.start(driver=None)
            except Exception:
                pass
        if self._soundfont_path:
            self._sfid = self._fs.sfload(self._soundfont_path)
            self._fs.program_select(self._channel, self._sfid, 0, 0)
        else:
            raise RuntimeError(
                "No soundfont found. Set KEYTAB_SOUNDFONT or load a .sf2/.sf3 from disk."
            )
        try:
            self.set_gain(self._gain)
        except Exception:
            pass

    def set_soundfont(self, path: str) -> None:
        p = Path(path).expanduser()
        if not p.is_file():
            raise FileNotFoundError(f"Soundfont not found: {p}")
        self._soundfont_path = str(p)
        if self._fs is None:
            self._init_synth()
            return
        self._sfid = self._fs.sfload(self._soundfont_path)
        self._fs.program_select(self._channel, self._sfid, 0, 0)

    def set_gain(self, gain: float) -> None:
        g = float(max(0.0, gain))
        self._gain = g
        if self._fs is not None:
            try:
                self._fs.set_gain(g)
            except Exception:
                pass

    # ------------------------------------------------------------------
    # Playback control
    # ------------------------------------------------------------------
    def _stop_for_restart(self) -> None:
        self._running = False
        try:
            if self._thread is not None and self._thread.is_alive():
                self._thread.join(timeout=0.2)
        except Exception:
            pass
        self._thread = None
        try:
            self._all_notes_off()
        except Exception:
            pass
        try:
            time.sleep(0.02)
        except Exception:
            pass

    def play_score(self, score) -> None:
        if self.is_playing():
            self._stop_for_restart()
        events = self._build_events_full(score)
        self._run_events_with_fluidsynth(events)

    def play_from_time_cursor(self, start_units: float, score) -> None:
        if self.is_playing():
            self._stop_for_restart()
        events = self._build_events_from_time(start_units, score)
        self._run_events_with_fluidsynth(events)

    def stop(self) -> None:
        self._running = False
        try:
            if self._thread is not None and self._thread.is_alive():
                self._thread.join(timeout=0.5)
        except Exception:
            pass
        self._thread = None
        try:
            self._all_notes_off()
        except Exception:
            pass

    def audition_note(self, pitch: int = 40, velocity: int = 80, duration_sec: float = 0.2) -> None:
        if self.is_playing():
            return
        midi_pitch = max(0, min(127, int(pitch) + int(self._pitch_offset)))
        vel = int(max(1, min(127, velocity)))
        dur = float(max(0.02, duration_sec))

        def _run():
            if self._fs is None:
                try:
                    self._init_synth()
                except Exception:
                    return
            try:
                self._fs.noteon(self._channel, midi_pitch, vel)
                time.sleep(dur)
                self._fs.noteoff(self._channel, midi_pitch)
            except Exception:
                pass

        th = threading.Thread(target=_run, daemon=True)
        th.start()

    def is_playing(self) -> bool:
        return bool(self._running)

    # ------------------------------------------------------------------
    # Event scheduling
    # ------------------------------------------------------------------
    def _run_events_with_fluidsynth(self, events: List[Tuple[str, float, int, int]]) -> None:
        if self._fs is None:
            self._init_synth()
        self._running = True

        def _runner() -> None:
            t0 = time.time()
            try:
                self._t0 = float(t0)
            except Exception:
                pass
            for kind, t_rel, midi_note, vel in events:
                if not self._running:
                    break
                now = time.time()
                delay = max(0.0, t0 + float(t_rel) - now)
                if delay > 0:
                    time.sleep(delay)
                if not self._running:
                    break
                try:
                    if kind == 'on':
                        self._fs.noteon(self._channel, int(midi_note), int(vel))
                    else:
                        self._fs.noteoff(self._channel, int(midi_note))
                except Exception:
                    pass
            self._running = False
            try:
                self._all_notes_off()
            except Exception:
                pass

        th = threading.Thread(target=_runner, daemon=True)
        th.start()
        self._thread = th

    def _all_notes_off(self) -> None:
        if self._fs is None:
            return
        try:
            self._fs.all_notes_off(self._channel)
        except Exception:
            pass
        try:
            self._fs.system_reset()
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Event building
    # ------------------------------------------------------------------
    def _build_events_full(self, score) -> List[Tuple[str, float, int, int]]:
        events: List[Tuple[str, float, int, int]] = []
        segs = self._get_tempo_segments(score)
        try:
            self._bpm = float(segs[0][2]) if segs else 120.0
            self._start_units = 0.0
        except Exception:
            pass
        for n in score.events.note:
            dur_units = float(getattr(n, 'duration', 0.0) or 0.0)
            if dur_units < float(self._min_duration_units):
                continue
            start_units = float(getattr(n, 'time', 0.0) or 0.0)
            end_units = float(start_units + dur_units)
            start_sec = self._seconds_between(0.0, start_units, segs)
            dur_sec = self._seconds_between(start_units, end_units, segs)
            vel = int(getattr(n, 'velocity', 64) or 64)
            app_pitch = int(n.pitch)
            midi_pitch = max(0, min(127, app_pitch + self._pitch_offset))
            events.append(('on', start_sec, midi_pitch, vel))
            off_t = max(0.0, start_sec + max(0.0, dur_sec) - float(self._off_epsilon_sec))
            events.append(('off', off_t, midi_pitch, 0))
        events.sort(key=lambda e: (e[1], 0 if e[0] == 'off' else 1))
        try:
            self._last_event_count = int(len([1 for e in events if e[0] == 'on']))
        except Exception:
            pass
        return events

    def _build_events_from_time(self, start_units: float, score) -> List[Tuple[str, float, int, int]]:
        segs = self._get_tempo_segments(score)
        su = float(max(0.0, start_units))
        try:
            self._bpm = float(segs[0][2]) if segs else 120.0
            self._start_units = float(su)
        except Exception:
            pass
        events: List[Tuple[str, float, int, int]] = []
        for n in score.events.note:
            start = float(n.time)
            end = float(n.time + n.duration)
            if float(getattr(n, 'duration', 0.0) or 0.0) < float(self._min_duration_units):
                continue
            app_pitch = int(n.pitch)
            midi_pitch = max(0, min(127, app_pitch + self._pitch_offset))
            vel = int(getattr(n, 'velocity', 64) or 64)
            if end <= su:
                continue
            if start < su < end:
                events.append(('on', 0.0, midi_pitch, vel))
                off_t = self._seconds_between(su, end, segs)
                off_t = max(0.0, float(off_t) - float(self._off_epsilon_sec))
                events.append(('off', float(off_t), midi_pitch, 0))
            elif start >= su:
                on_t = self._seconds_between(su, start, segs)
                dur_t = self._seconds_between(start, float(n.time + n.duration), segs)
                events.append(('on', float(on_t), midi_pitch, vel))
                off_t = float(on_t + max(0.0, dur_t) - float(self._off_epsilon_sec))
                events.append(('off', max(0.0, off_t), midi_pitch, 0))
        events.sort(key=lambda e: (e[1], 0 if e[0] == 'off' else 1))
        try:
            self._last_event_count = int(len([1 for e in events if e[0] == 'on']))
        except Exception:
            pass
        return events

    # ------------------------------------------------------------------
    # Tempo helpers
    # ------------------------------------------------------------------
    def _get_tempo_segments(self, score) -> List[Tuple[float, float, float]]:
        segs: List[Tuple[float, float, float]] = []
        try:
            lst = sorted(list(getattr(score.events, 'tempo', []) or []), key=lambda e: float(getattr(e, 'time', 0.0) or 0.0))
        except Exception:
            lst = []
        if not lst:
            return [(0.0, float('inf'), 60.0 / (120.0 * float(QUARTER_NOTE_UNIT)))]
        for i, ev in enumerate(lst):
            start = float(getattr(ev, 'time', 0.0) or 0.0)
            s_per_unit = self._calculate_tempo(ev)
            if i + 1 < len(lst):
                next_start = float(getattr(lst[i + 1], 'time', 0.0) or 0.0)
                end = max(start, next_start)
            else:
                end = float('inf')
            segs.append((start, end, float(s_per_unit)))
        return segs

    def _seconds_between(self, a_units: float, b_units: float, segs: List[Tuple[float, float, float]]) -> float:
        if b_units <= a_units:
            return 0.0
        total = 0.0
        for s, e, s_per_unit in segs:
            if e <= a_units:
                continue
            if s >= b_units:
                break
            lo = max(a_units, s)
            hi = min(b_units, e)
            if hi > lo:
                total += (hi - lo) * float(s_per_unit)
        if segs and b_units > segs[-1][1]:
            _s_last, e_last, s_per_unit_last = segs[-1]
            lo = max(a_units, e_last)
            hi = b_units
            if hi > lo:
                total += (hi - lo) * float(s_per_unit_last)
        return total

    def _units_from_elapsed(self, elapsed_sec: float, start_units: float, segs: List[Tuple[float, float, float]]) -> float:
        u = float(start_units)
        rem = float(elapsed_sec)
        idx = 0
        for i, (s, e, _s_per_unit) in enumerate(segs):
            if s <= start_units < e:
                idx = i
                break
            if start_units >= e:
                idx = i + 1
        while rem > 0.0 and idx < len(segs):
            s, e, s_per_unit = segs[idx]
            seg_lo = max(s, u)
            seg_hi = e
            if seg_hi > seg_lo:
                seg_sec = (seg_hi - seg_lo) * float(s_per_unit)
                if rem >= seg_sec:
                    u = seg_hi
                    rem -= seg_sec
                    idx += 1
                    continue
                u += rem / float(s_per_unit)
                rem = 0.0
                return u
            idx += 1
        if segs and rem > 0.0:
            _s, _e, s_per_unit_last = segs[-1]
            u += rem / float(s_per_unit_last)
        return u

    def _calculate_tempo(self, tempo_event) -> float:
        try:
            tpm = float(getattr(tempo_event, 'tempo', 60.0) or 60.0)
        except Exception:
            tpm = 60.0
        try:
            dur_units = float(getattr(tempo_event, 'duration', 0.0) or 0.0)
        except Exception:
            dur_units = 0.0
        if dur_units <= 0.0:
            return 60.0 / (120.0 * float(QUARTER_NOTE_UNIT))
        return 60.0 / (float(tpm) * float(dur_units))

    # ------------------------------------------------------------------
    # Status and playhead
    # ------------------------------------------------------------------
    def get_playhead_time(self, score=None) -> Optional[float]:
        if not bool(self._running):
            return None
        try:
            elapsed = max(0.0, time.time() - float(self._t0))
            if score is None:
                s_per_unit = float(self._bpm) if self._bpm > 0 else (60.0 / (120.0 * float(QUARTER_NOTE_UNIT)))
                units = float(self._start_units) + float(elapsed) / float(s_per_unit)
                return units
            segs = self._get_tempo_segments(score)
            u = self._units_from_elapsed(float(elapsed), float(self._start_units), segs)
            return u
        except Exception:
            return None

    def get_debug_status(self) -> dict:
        status = {
            'playback_type': 'fluidsynth',
            'bpm': float(self._bpm),
            'events': int(self._last_event_count),
            'soundfont': str(self._soundfont_path or ''),
            'gain': float(self._gain),
        }
        return status