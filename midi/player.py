from __future__ import annotations
import threading
import time
from typing import Optional, Set

import mido

from utils.CONSTANT import QUARTER_NOTE_UNIT


class Player:
    """Playback of `SCORE` via external MIDI output port (no internal synth)."""

    def __init__(self) -> None:
        self._out: Optional[mido.ports.BaseOutput] = None
        self._port_name: Optional[str] = None
        self._thread: Optional[threading.Thread] = None
        self._running: bool = False
        self._active_notes: Set[int] = set()
        # App pitch mapping: app 49 == MIDI 69 (A4). MIDI = app + 20
        self._pitch_offset: int = 20
        # Default channel
        self._channel: int = 0

    # Legacy no-ops for previous synth API
    def set_wavetables(self, left, right) -> None:
        pass

    def set_adsr(self, attack_seconds: float, decay_seconds: float, sustain_level: float, release_seconds: float) -> None:
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
        # Prefer first non-"Through" port
        name = None
        for n in names:
            if 'through' in str(n).lower():
                continue
            name = n
            break
        # Fallback to first available, if any
        if name is None and names:
            name = names[0]
        if name is None:
            raise RuntimeError("No MIDI output ports available")
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

    def play_score(self, score) -> None:
        self._ensure_port()
        if self._out is None:
            return
        # Build event list
        events = []
        bpm = 120.0
        try:
            for t in score.events.text:
                s = str(getattr(t, 'text', ''))
                if s and '/' in s:
                    bpm = float(s.split('/')[0])
                    break
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

        self._running = True
        def _runner():
            t0 = time.time()
            for kind, t_rel, midi_note, vel in events:
                if not self._running:
                    break
                now = time.time()
                delay = max(0.0, t0 + t_rel - now)
                if delay > 0:
                    time.sleep(delay)
                if not self._running:
                    break
                if kind == 'on':
                    self._note_on(int(midi_note), int(vel))
                else:
                    self._note_off(int(midi_note))
        th = threading.Thread(target=_runner, daemon=True)
        th.start()
        self._thread = th

    def play_from_time_cursor(self, start_units: float, score) -> None:
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

        self._running = True
        def _runner():
            t0 = time.time()
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
        try:
            self._all_notes_off()
        except Exception:
            pass

    def is_playing(self) -> bool:
        return bool(self._running)
