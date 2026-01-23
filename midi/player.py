from __future__ import annotations
import threading
import time
from typing import Optional, Set, List, Tuple

import mido
import numpy as np

from utils.CONSTANT import QUARTER_NOTE_UNIT
from appdata_manager import get_appdata_manager

try:
    from synth.wavetable_synth import WavetableSynth
except Exception:
    WavetableSynth = None  # type: ignore


class Player:
    """Playback of `SCORE` via either external MIDI port or internal synth."""

    def __init__(self) -> None:
        self._out: Optional[mido.ports.BaseOutput] = None
        self._port_name: Optional[str] = None
        self._thread: Optional[threading.Thread] = None
        self._running: bool = False
        self._active_notes: Set[int] = set()
        # App pitch mapping: app 49 == MIDI 69 (A4). MIDI = app + 20
        self._pitch_offset: int = 20
        # Default channel (for MIDI backend)
        self._channel: int = 0
        # Backend selection: 'midi_port' or 'internal_synth'
        self._playback_type: str = 'midi_port'
        # Internal synth instance
        self._synth = None  # internal synth instance when using 'internal_synth'
        # Load preferences from appdata
        try:
            adm = get_appdata_manager()
            self._playback_type = str(adm.get("playback_type", "midi_port") or "midi_port")
            pn = str(adm.get("midi_out_port", "") or "")
            if pn:
                self._port_name = pn
        except Exception:
            pass
        # Playback timing state for UI playhead
        self._bpm: float = 120.0
        self._t0: float = 0.0
        self._start_units: float = 0.0
        self._last_event_count: int = 0

    # Synth API passthroughs
    def set_wavetables(self, left, right) -> None:
        if self._synth is None and WavetableSynth is not None:
            self._synth = WavetableSynth()
        try:
            if self._synth is not None:
                self._synth.set_wavetables(np.asarray(left, dtype=np.float32), np.asarray(right, dtype=np.float32))
        except Exception:
            pass

    def set_adsr(self, attack_seconds: float, decay_seconds: float, sustain_level: float, release_seconds: float) -> None:
        if self._synth is None and WavetableSynth is not None:
            self._synth = WavetableSynth()
        try:
            if self._synth is not None:
                self._synth.set_adsr(float(attack_seconds), float(decay_seconds), float(sustain_level), float(release_seconds))
        except Exception:
            pass

    def set_audio_output_device(self, device_name: str) -> None:
        if self._synth is None and WavetableSynth is not None:
            self._synth = WavetableSynth()
        try:
            if self._synth is not None:
                self._synth.set_output_device(str(device_name) if device_name else None)
        except Exception:
            pass

    def set_gain(self, gain: float) -> None:
        if self._synth is None and WavetableSynth is not None:
            self._synth = WavetableSynth()
        try:
            if self._synth is not None:
                self._synth.gain = float(max(0.0, gain))
        except Exception:
            pass

    def set_playback_type(self, playback_type: str) -> None:
        self._playback_type = str(playback_type)
        try:
            adm = get_appdata_manager()
            adm.set("playback_type", self._playback_type)
            adm.save()
        except Exception:
            pass

    def list_output_ports(self) -> list[str]:
        try:
            return list(mido.get_output_names() or [])
        except Exception:
            return []

    def set_output_port(self, name: str) -> None:
        # Close existing port and open the requested one
        try:
            if self._out is not None:
                # All notes off on current port before switching
                try:
                    self._all_notes_off()
                except Exception:
                    pass
                try:
                    self._out.close()
                except Exception:
                    pass
            self._out = None
        except Exception:
            pass
        self._port_name = str(name) if name else None
        # Persist selection
        try:
            adm = get_appdata_manager()
            adm.set("midi_out_port", self._port_name or "")
            adm.save()
        except Exception:
            pass
        # Attempt to open immediately
        if self._port_name:
            try:
                self._out = mido.open_output(self._port_name)
                print(f"[MIDI] Using output port: {self._port_name}")
            except Exception as exc:
                print(f"[MIDI] Failed to open '{self._port_name}': {exc}")
                self._out = None

    def _ensure_port(self) -> None:
        if self._out is not None:
            return
        names = self.list_output_ports()
        # If a preferred name is set, try to use it
        if self._port_name:
            if self._port_name in names:
                try:
                    self._out = mido.open_output(self._port_name)
                    print(f"[MIDI] Using output port: {self._port_name}")
                    return
                except Exception as exc:
                    print(f"[MIDI] Failed to open '{self._port_name}': {exc}")
            else:
                print(f"[MIDI] Preferred port not found: {self._port_name}")
                raise RuntimeError(f"Preferred MIDI port not found: {self._port_name}")
        # Prefer first non-"Through" port
        non_through = [n for n in names if 'through' not in str(n).lower()]
        if not non_through:
            # Only "Through" ports available — treat as no usable ports
            raise RuntimeError("No usable MIDI output ports (only 'Through' found)")
        name = non_through[0]
        try:
            self._out = mido.open_output(name)
            print(f"[MIDI] Using output port: {name}")
            self._port_name = name
        except Exception as exc:
            raise RuntimeError(f"Failed to open MIDI output port '{name}': {exc}")

    def _note_on(self, midi_note: int, velocity: int) -> None:
        if self._out is None:
            return
        msg = mido.Message('note_on', note=int(midi_note), velocity=int(max(0, min(127, velocity))), channel=int(self._channel))
        try:
            self._out.send(msg)
            self._active_notes.add(int(midi_note))
        except Exception:
            pass

    def _note_off(self, midi_note: int) -> None:
        if self._out is None:
            return
        msg = mido.Message('note_off', note=int(midi_note), velocity=0, channel=int(self._channel))
        try:
            self._out.send(msg)
            self._active_notes.discard(int(midi_note))
        except Exception:
            pass

    def _all_notes_off(self) -> None:
        if self._out is None:
            return
        try:
            # Send CC123 All Notes Off
            cc = mido.Message('control_change', control=123, value=0, channel=int(self._channel))
            self._out.send(cc)
        except Exception:
            pass
        # Also send note-off for any tracked active notes
        try:
            for n in list(self._active_notes):
                self._note_off(int(n))
        except Exception:
            pass

    def _build_events_full(self, score) -> List[Tuple[str, float, int, int]]:
        events: List[Tuple[str, float, int, int]] = []
        bpm = 120.0
        try:
            for t in score.events.text:
                s = str(getattr(t, 'text', ''))
                if s and '/' in s:
                    bpm = float(s.split('/')[0])
                    break
        except Exception:
            pass
        # Record BPM and start at zero units for full-play runs
        try:
            self._bpm = float(bpm)
            self._start_units = 0.0
        except Exception:
            pass
        for n in score.events.note:
            start_sec = (float(n.time) / QUARTER_NOTE_UNIT) * (60.0 / bpm)
            dur_sec = (float(n.duration) / QUARTER_NOTE_UNIT) * (60.0 / bpm)
            vel = int(getattr(n, 'velocity', 64) or 64)
            app_pitch = int(n.pitch)
            midi_pitch = app_pitch + self._pitch_offset
            events.append(('on', start_sec, midi_pitch, vel))
            events.append(('off', start_sec + max(0.0, dur_sec), midi_pitch, 0))
        events.sort(key=lambda e: e[1])
        try:
            self._last_event_count = int(len([1 for e in events if e[0] == 'on']))
        except Exception:
            pass
        return events

    def play_score(self, score) -> None:
        if self._playback_type == 'internal_synth' and WavetableSynth is not None:
            if self._synth is None:
                self._synth = WavetableSynth()
            events = self._build_events_full(score)
            self._run_events_with_synth(events)
            return
        # MIDI port backend
        self._ensure_port()
        if self._out is None:
            return
        events = self._build_events_full(score)
        self._run_events_with_midi(events)

    def play_from_time_cursor(self, start_units: float, score) -> None:
        if self._playback_type == 'internal_synth' and WavetableSynth is not None:
            events = self._build_events_from_time(start_units, score)
            if self._synth is None:
                self._synth = WavetableSynth()
            self._run_events_with_synth(events)
            return
        # MIDI backend
        self._ensure_port()
        if self._out is None:
            return
        bpm = 120.0
        try:
            for t in score.events.text:
                s = str(getattr(t, 'text', ''))
                if s and '/' in s:
                    bpm = float(s.split('/')[0])
                    break
        except Exception:
            pass
        su = float(max(0.0, start_units))
        events: list[tuple[str, float, int, int]] = []
        # Start any spanning notes immediately; schedule offs and future notes
        for n in score.events.note:
            start = float(n.time)
            end = float(n.time + n.duration)
            app_pitch = int(n.pitch)
            midi_pitch = app_pitch + self._pitch_offset
            vel = int(getattr(n, 'velocity', 64) or 64)
            if end <= su:
                continue
            if start < su < end:
                # Start now; schedule off at remaining duration
                self._note_on(int(midi_pitch), int(vel))
                off_t = ((end - su) / QUARTER_NOTE_UNIT) * (60.0 / bpm)
                events.append(('off', float(off_t), midi_pitch, 0))
            elif start >= su:
                on_t = ((start - su) / QUARTER_NOTE_UNIT) * (60.0 / bpm)
                dur_t = (float(n.duration) / QUARTER_NOTE_UNIT) * (60.0 / bpm)
                events.append(('on', float(on_t), midi_pitch, vel))
                events.append(('off', float(on_t + max(0.0, dur_t)), midi_pitch, 0))
        events.sort(key=lambda e: e[1])

        # Record BPM and relative start units for playhead mapping
        try:
            self._start_units = float(su)
            self._bpm = float(bpm)
        except Exception:
            pass
        self._run_events_with_midi(events)

    def _build_events_from_time(self, start_units: float, score) -> List[Tuple[str, float, int, int]]:
        bpm = 120.0
        try:
            for t in score.events.text:
                s = str(getattr(t, 'text', ''))
                if s and '/' in s:
                    bpm = float(s.split('/')[0])
                    break
        except Exception:
            pass
        su = float(max(0.0, start_units))
        # Record BPM and start units so UI can compute playhead
        try:
            self._bpm = float(bpm)
            self._start_units = float(su)
        except Exception:
            pass
        events: List[Tuple[str, float, int, int]] = []
        for n in score.events.note:
            start = float(n.time)
            end = float(n.time + n.duration)
            app_pitch = int(n.pitch)
            midi_pitch = app_pitch + self._pitch_offset
            vel = int(getattr(n, 'velocity', 64) or 64)
            if end <= su:
                continue
            if start < su < end:
                # Start now; schedule off at remaining duration
                events.append(('on', 0.0, midi_pitch, vel))
                off_t = ((end - su) / QUARTER_NOTE_UNIT) * (60.0 / bpm)
                events.append(('off', float(off_t), midi_pitch, 0))
            elif start >= su:
                on_t = ((start - su) / QUARTER_NOTE_UNIT) * (60.0 / bpm)
                dur_t = (float(n.duration) / QUARTER_NOTE_UNIT) * (60.0 / bpm)
                events.append(('on', float(on_t), midi_pitch, vel))
                events.append(('off', float(on_t + max(0.0, dur_t)), midi_pitch, 0))
        events.sort(key=lambda e: e[1])
        try:
            self._last_event_count = int(len([1 for e in events if e[0] == 'on']))
        except Exception:
            pass
        return events

    def _run_events_with_midi(self, events: List[Tuple[str, float, int, int]]) -> None:
        self._running = True
        def _runner():
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
                if kind == 'on':
                    self._note_on(int(midi_note), int(vel))
                else:
                    self._note_off(int(midi_note))
            # Playback finished naturally
            self._running = False
        th = threading.Thread(target=_runner, daemon=True)
        th.start()
        self._thread = th

    def _run_events_with_synth(self, events: List[Tuple[str, float, int, int]]) -> None:
        if self._synth is None:
            return
        self._running = True
        def _runner():
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
                        self._synth.note_on(int(midi_note), int(vel))
                    else:
                        self._synth.note_off(int(midi_note))
                except Exception:
                    pass
            # Playback finished naturally
            self._running = False
        th = threading.Thread(target=_runner, daemon=True)
        th.start()
        self._thread = th

    def stop(self) -> None:
        self._running = False
        try:
            if self._thread is not None and self._thread.is_alive():
                self._thread.join(timeout=0.5)
        except Exception:
            pass
        self._thread = None
        if self._playback_type == 'internal_synth' and self._synth is not None:
            try:
                # Fade out to avoid clicks, then stop
                self._synth.fade_out_and_stop(200)
            except Exception:
                # Fallback to immediate stop
                try:
                    self._synth.stop()
                except Exception:
                    pass
        else:
            try:
                self._all_notes_off()
            except Exception:
                pass

    def is_playing(self) -> bool:
        return bool(self._running)

    def get_playhead_units(self) -> Optional[float]:
        """Return current playhead position in app time units (ticks), or None if idle.

        Mapping: units = start_units + elapsed_sec * QUARTER_NOTE_UNIT * bpm / 60.
        """
        if not bool(self._running):
            return None
        try:
            elapsed = max(0.0, time.time() - float(self._t0))
            units = float(self._start_units) + float(elapsed) * float(QUARTER_NOTE_UNIT) * float(self._bpm) / 60.0
            return units
        except Exception:
            return None

    def get_debug_status(self) -> dict:
        """Return current playback debug info for UI/status messages."""
        status = {
            'playback_type': self._playback_type,
            'bpm': float(self._bpm),
            'events': int(self._last_event_count),
        }
        try:
            if self._playback_type == 'internal_synth' and self._synth is not None:
                status['gain'] = float(getattr(self._synth, 'gain', 0.0))
                status['device'] = str(getattr(self._synth, '_device_name', '') or '')
        except Exception:
            pass
        try:
            if self._playback_type == 'midi_port':
                status['midi_port'] = str(self._port_name or '')
            else:
                status['midi_port'] = ''
        except Exception:
            pass
        return status
