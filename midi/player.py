from __future__ import annotations
import os
import sys
import threading
import time
import ctypes
from pathlib import Path
from typing import List, Optional, Tuple

import mido


def _ensure_fluidsynth_lib() -> None:
    candidates = [
        Path("/usr/lib/x86_64-linux-gnu/libfluidsynth.so.3"),
        Path("/usr/lib/libfluidsynth.so.3"),
        Path("/lib/x86_64-linux-gnu/libfluidsynth.so.3"),
        Path("/usr/local/lib/libfluidsynth.so.3"),
        Path("/usr/lib/libfluidsynth.so"),
        Path("/usr/local/lib/libfluidsynth.so"),
    ]
    for path in candidates:
        if not path.exists():
            continue
        try:
            ctypes.CDLL(str(path))
            # Hint pyfluidsynth to use this exact file so ctypes.find_library is bypassed.
            os.environ.setdefault("PYFLUIDSYNTH_LIB", str(path))
            return
        except Exception:
            continue
    raise ImportError(
        "FluidSynth native library not available. Install it with 'sudo apt-get install fluidsynth libfluidsynth3' (or equivalent) and ensure the library is present at /usr/lib*/libfluidsynth.so.3."
    )


if sys.platform.startswith("linux"):
    _ensure_fluidsynth_lib()
    try:
        import fluidsynth  # type: ignore
    except Exception as exc:  # pragma: no cover - environment specific
        raise ImportError(
            "FluidSynth native library not available. Install it with 'sudo apt-get install fluidsynth libfluidsynth3' (or the equivalent for your distro) and ensure pyfluidsynth is installed."
        ) from exc

from utils.CONSTANT import QUARTER_NOTE_UNIT


class _Backend:
    def program_select(self) -> None:  # pragma: no cover - runtime side effects
        raise NotImplementedError

    def set_gain(self, gain: float) -> None:  # pragma: no cover - runtime side effects
        raise NotImplementedError

    def note_on(self, midi_note: int, velocity: int) -> None:  # pragma: no cover - runtime side effects
        raise NotImplementedError

    def note_off(self, midi_note: int) -> None:  # pragma: no cover - runtime side effects
        raise NotImplementedError

    def all_notes_off(self) -> None:  # pragma: no cover - runtime side effects
        raise NotImplementedError

    def shutdown(self) -> None:  # pragma: no cover - runtime side effects
        pass


class _FluidsynthBackend(_Backend):
    def __init__(self, soundfont_path: Optional[str]) -> None:
        if not hasattr(sys.modules.get('fluidsynth'), "Synth"):
            raise ImportError(
                "FluidSynth not available. Install it with 'sudo apt-get install fluidsynth libfluidsynth3' and ensure pyfluidsynth is installed."
            )
        self._fs: Optional[fluidsynth.Synth] = None
        self._sfid: Optional[int] = None
        self._channel: int = 0
        self._gain: float = 0.35
        self._soundfont_path = soundfont_path or self._autodetect_soundfont()
        if self._soundfont_path is None:
            raise RuntimeError(
                "No soundfont found. Install a GM soundfont (e.g. FluidR3_GM.sf2) or set KEYTAB_SOUNDFONT."
            )
        self._init_synth()

    def _autodetect_soundfont(self) -> Optional[str]:
        candidates: list[Path] = []
        env_sf = os.environ.get("KEYTAB_SOUNDFONT")
        if env_sf:
            candidates.append(Path(env_sf))
        candidates.append(Path("/usr/share/sounds/sf2/FluidR3_GM.sf2"))
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
        started = False
        for drv in ("pulseaudio", None):
            try:
                self._fs.start(driver=drv)
                started = True
                break
            except Exception:
                continue
        if not started:
            try:
                self._fs.start(driver=None)
            except Exception:
                pass
        self._sfid = self._fs.sfload(self._soundfont_path)
        self._fs.program_select(self._channel, self._sfid, 0, 0)
        try:
            self._fs.set_gain(self._gain)
        except Exception:
            pass

    def program_select(self) -> None:
        if self._fs is not None and self._sfid is not None:
            try:
                self._fs.program_select(self._channel, self._sfid, 0, 0)
            except Exception:
                pass

    def set_gain(self, gain: float) -> None:
        self._gain = max(0.0, float(gain))
        if self._fs is not None:
            try:
                self._fs.set_gain(self._gain)
            except Exception:
                pass

    def note_on(self, midi_note: int, velocity: int) -> None:
        if self._fs is not None:
            try:
                self._fs.noteon(self._channel, midi_note, velocity)
            except Exception:
                pass

    def note_off(self, midi_note: int) -> None:
        if self._fs is not None:
            try:
                self._fs.noteoff(self._channel, midi_note)
            except Exception:
                pass

    def all_notes_off(self) -> None:
        if self._fs is not None:
            try:
                self._fs.all_notes_off(self._channel)
            except Exception:
                pass
        try:
            if self._fs is not None:
                self._fs.system_reset()
        except Exception:
            pass

    def shutdown(self) -> None:
        self.all_notes_off()
        if self._fs is not None:
            try:
                self._fs.delete()
            except Exception:
                pass
        self._fs = None


class _MidiOutBackend(_Backend):
    """Use OS-provided wavetable synth via RtMidi (CoreMIDI/WinMM)."""

    def __init__(self) -> None:
        try:
            self._port = mido.open_output()
        except Exception as exc:  # pragma: no cover - environment dependent
            raise RuntimeError(
                "No MIDI output device available. Configure a default CoreMIDI/WinMM output to enable playback."
            ) from exc

    def program_select(self) -> None:
        try:
            self._port.send(mido.Message("program_change", program=0))
        except Exception:
            pass

    def set_gain(self, gain: float) -> None:
        # Not supported on OS synth; ignore.
        pass

    def note_on(self, midi_note: int, velocity: int) -> None:
        try:
            self._port.send(mido.Message("note_on", note=int(midi_note), velocity=int(velocity)))
        except Exception:
            pass

    def note_off(self, midi_note: int) -> None:
        try:
            self._port.send(mido.Message("note_off", note=int(midi_note), velocity=0))
        except Exception:
            pass

    def all_notes_off(self) -> None:
        try:
            for n in range(128):
                self._port.send(mido.Message("note_off", note=n, velocity=0))
        except Exception:
            pass

    def shutdown(self) -> None:
        try:
            self.all_notes_off()
            self._port.close()
        except Exception:
            pass


class Player:
    """Playback of `SCORE` using FluidSynth on Linux; OS MIDI synth elsewhere."""

    def __init__(self, soundfont_path: Optional[str] = None) -> None:
        self._backend: Optional[_Backend] = None
        self._backend_kind: str = "rtmidi"
        if sys.platform.startswith("linux"):
            self._backend = _FluidsynthBackend(soundfont_path)
            self._backend_kind = "fluidsynth"
        else:
            self._backend = _MidiOutBackend()
            self._backend_kind = "rtmidi"

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
        try:
            if self._backend is not None:
                self._backend.program_select()
        except Exception:
            pass

    def set_soundfont(self, path: str) -> None:
        if self._backend_kind != "fluidsynth":
            return
        backend = self._backend
        if not isinstance(backend, _FluidsynthBackend):
            return
        p = Path(path).expanduser()
        if not p.is_file():
            raise FileNotFoundError(f"Soundfont not found: {p}")
        backend._soundfont_path = str(p)
        backend._init_synth()

    def set_gain(self, gain: float) -> None:
        g = float(max(0.0, gain))
        self._gain = g
        if self._backend is not None:
            try:
                self._backend.set_gain(g)
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
        self._run_events(events)

    def play_from_time_cursor(self, start_units: float, score) -> None:
        if self.is_playing():
            self._stop_for_restart()
        events = self._build_events_from_time(start_units, score)
        self._run_events(events)

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
        if self._backend is None:
            raise RuntimeError("Audio backend not initialized.")
        midi_pitch = max(0, min(127, int(pitch) + int(self._pitch_offset)))
        vel = int(max(1, min(127, velocity)))
        dur = float(max(0.02, duration_sec))

        def _run():
            try:
                self._backend.note_on(midi_pitch, vel)
                time.sleep(dur)
                self._backend.note_off(midi_pitch)
            except Exception:
                pass

        th = threading.Thread(target=_run, daemon=True)
        th.start()

    def is_playing(self) -> bool:
        return bool(self._running)

    # ------------------------------------------------------------------
    # Event scheduling
    # ------------------------------------------------------------------
    def _run_events(self, events: List[Tuple[str, float, int, int]]) -> None:
        if self._backend is None:
            raise RuntimeError("Audio backend not initialized.")
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
                        self._backend.note_on(int(midi_note), int(vel))
                    else:
                        self._backend.note_off(int(midi_note))
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
        if self._backend is None:
            return
        try:
            self._backend.all_notes_off()
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
        sf = None
        if isinstance(self._backend, _FluidsynthBackend):
            sf = getattr(self._backend, "_soundfont_path", None)
        return {
            'playback_type': self._backend_kind,
            'bpm': float(self._bpm),
            'events': int(self._last_event_count),
            'soundfont': str(sf or ''),
            'gain': float(self._gain),
        }