from __future__ import annotations
import threading
import time
from typing import Optional, Set, List, Tuple

import mido
import numpy as np

from utils.CONSTANT import QUARTER_NOTE_UNIT
from appdata_manager import get_appdata_manager

from synth.wavetable_synth import WavetableSynth


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
        # Whether to send MIDI transport (start/stop/clock/Spp)
        self._send_midi_transport: bool = True
        # Whether to persist settings to appdata
        self._persist_settings: bool = True
        # Load preferences from appdata
        try:
            adm = get_appdata_manager()
            self._playback_type = str(adm.get("playback_type", "midi_port") or "midi_port")
            pn = str(adm.get("midi_out_port", "") or "")
            if pn:
                self._port_name = pn
            self._send_midi_transport = bool(adm.get("send_midi_transport", True))
        except Exception:
            pass
        # Playback timing state for UI playhead
        self._bpm: float = 120.0
        self._t0: float = 0.0
        self._start_units: float = 0.0
        self._last_event_count: int = 0
        # Small safety gap for note-off times to avoid exact on/off coincidence clicks and missed retriggers
        self._off_epsilon_sec: float = 0.003  # ~3 ms, inaudible timing shift
        # Ignore very short notes (in app units) to avoid hanging/stuck behavior
        # App duration units: QUARTER_NOTE_UNIT == 100.0, so 4 units ≈ 0.04 quarter notes
        self._min_duration_units: float = 4.0
        # MIDI sync clock thread
        self._clock_thread: Optional[threading.Thread] = None
        self._clock_stop_event = threading.Event()

    def _stop_for_restart(self) -> None:
        # Fast, immediate stop used before restarting playback to avoid overlap/clicks.
        self._running = False
        try:
            self._stop_midi_sync(send_stop=True)
        except Exception:
            pass
        try:
            if self._thread is not None and self._thread.is_alive():
                self._thread.join(timeout=0.2)
        except Exception:
            pass
        self._thread = None
        if self._playback_type == 'internal_synth' and self._synth is not None:
            try:
                self._synth.stop()
            except Exception:
                pass
        else:
            try:
                self._all_notes_off()
            except Exception:
                pass
        try:
            self._active_notes.clear()
        except Exception:
            pass
        try:
            time.sleep(0.02)
        except Exception:
            pass

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

    def set_humanize_detune_cents(self, cents: float) -> None:
        if self._synth is None and WavetableSynth is not None:
            self._synth = WavetableSynth()
        try:
            if self._synth is not None and hasattr(self._synth, 'set_humanize_detune_cents'):
                self._synth.set_humanize_detune_cents(float(max(0.0, cents)))
        except Exception:
            pass

    def set_humanize_interval_s(self, seconds: float) -> None:
        if self._synth is None and WavetableSynth is not None:
            self._synth = WavetableSynth()
        try:
            if self._synth is not None and hasattr(self._synth, 'set_humanize_interval_s'):
                self._synth.set_humanize_interval_s(float(max(0.0, seconds)))
        except Exception:
            pass

    def set_playback_type(self, playback_type: str) -> None:
        self._playback_type = str(playback_type)
        if self._persist_settings:
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
        if self._persist_settings:
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
                # Keep preferred port name so we can retry later
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
                # Port temporarily unavailable; keep name and retry later
                print(f"[MIDI] Preferred port not found: {self._port_name}")
                return
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

    def _send_midi_message(self, msg: mido.Message) -> None:
        if self._out is None:
            return
        try:
            self._out.send(msg)
        except Exception:
            pass

    def _seconds_per_unit_at(self, units: float, segs: List[Tuple[float, float, float]]) -> float:
        if not segs:
            return 60.0 / (120.0 * float(QUARTER_NOTE_UNIT))
        for s, e, s_per_unit in segs:
            if s <= units < e:
                return float(s_per_unit)
        return float(segs[-1][2])

    def _start_midi_sync(self, segs: List[Tuple[float, float, float]], start_units: float) -> None:
        if self._out is None or not bool(self._send_midi_transport):
            return
        # Reset transport, send Song Position Pointer (SPP), then Start/Continue
        try:
            self._send_midi_message(mido.Message('stop'))
        except Exception:
            pass
        try:
            spp = int(max(0.0, (float(start_units) / float(QUARTER_NOTE_UNIT)) * 4.0))
            self._send_midi_message(mido.Message('songpos', pos=int(spp)))
        except Exception:
            pass
        try:
            if float(start_units) > 0.0:
                self._send_midi_message(mido.Message('continue'))
            else:
                self._send_midi_message(mido.Message('start'))
        except Exception:
            pass

        # Start clock thread
        try:
            self._clock_stop_event.clear()
        except Exception:
            pass

        def _clock_runner():
            next_tick = time.time()
            while not self._clock_stop_event.is_set():
                now = time.time()
                if now < next_tick:
                    time.sleep(min(0.001, next_tick - now))
                    continue
                # Send MIDI clock tick
                try:
                    self._send_midi_message(mido.Message('clock'))
                except Exception:
                    pass
                # Compute interval from current tempo segment
                try:
                    elapsed = max(0.0, now - float(self._t0))
                    units = self._units_from_elapsed(float(elapsed), float(start_units), segs)
                    s_per_unit = float(self._seconds_per_unit_at(float(units), segs))
                    sec_per_quarter = float(s_per_unit) * float(QUARTER_NOTE_UNIT)
                    interval = max(0.001, float(sec_per_quarter) / 24.0)
                except Exception:
                    interval = 0.02
                next_tick = now + interval

        th = threading.Thread(target=_clock_runner, daemon=True)
        th.start()
        self._clock_thread = th

    def _stop_midi_sync(self, send_stop: bool = False) -> None:
        try:
            self._clock_stop_event.set()
        except Exception:
            pass
        try:
            if self._clock_thread is not None and self._clock_thread.is_alive():
                self._clock_thread.join(timeout=0.2)
        except Exception:
            pass
        self._clock_thread = None
        if send_stop and bool(self._send_midi_transport):
            try:
                self._send_midi_message(mido.Message('stop'))
            except Exception:
                pass

    def set_send_midi_transport(self, enabled: bool) -> None:
        self._send_midi_transport = bool(enabled)
        if self._persist_settings:
            try:
                adm = get_appdata_manager()
                adm.set("send_midi_transport", bool(self._send_midi_transport))
                adm.save()
            except Exception:
                pass

    def set_persist_settings(self, enabled: bool) -> None:
        self._persist_settings = bool(enabled)

    def _build_events_full(self, score) -> List[Tuple[str, float, int, int]]:
        events: List[Tuple[str, float, int, int]] = []
        # Build tempo segments from SCORE.events.tempo (piecewise constant BPM)
        segs = self._get_tempo_segments(score)
        # Record nominal BPM from first segment and start at zero units
        try:
            self._bpm = float(segs[0][2]) if segs else 120.0
            self._start_units = 0.0
        except Exception:
            pass
        for n in score.events.note:
            # Skip notes shorter than threshold in time units
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
        # Sort by time, then ensure 'off' precedes 'on' at the same timestamp to reduce clicks
        events.sort(key=lambda e: (e[1], 0 if e[0] == 'off' else 1))
        try:
            self._last_event_count = int(len([1 for e in events if e[0] == 'on']))
        except Exception:
            pass
        return events

    def play_score(self, score) -> None:
        # Always restart playback from the beginning on Play.
        # If already playing, fast-stop to prevent double-play and clicks.
        if self.is_playing():
            try:
                self._stop_for_restart()
            except Exception:
                pass
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
        segs = self._get_tempo_segments(score)
        events = self._build_events_full(score)
        try:
            self._start_midi_sync(segs, 0.0)
        except Exception:
            pass
        self._run_events_with_midi(events)

    def play_from_time_cursor(self, start_units: float, score) -> None:
        # If playing, restart from the requested cursor rather than layering playback.
        if self.is_playing():
            try:
                self._stop_for_restart()
            except Exception:
                pass
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
        # Build tempo segments
        segs = self._get_tempo_segments(score)
        su = float(max(0.0, start_units))
        events: list[tuple[str, float, int, int]] = []
        # Start any spanning notes immediately; schedule offs and future notes
        for n in score.events.note:
            start = float(n.time)
            end = float(n.time + n.duration)
            # Skip notes shorter than threshold in time units
            if float(getattr(n, 'duration', 0.0) or 0.0) < float(self._min_duration_units):
                continue
            app_pitch = int(n.pitch)
            midi_pitch = max(0, min(127, app_pitch + self._pitch_offset))
            vel = int(getattr(n, 'velocity', 64) or 64)
            if end <= su:
                continue
            if start < su < end:
                # Start now; schedule off at remaining duration
                self._note_on(int(midi_pitch), int(vel))
                off_t = self._seconds_between(su, end, segs)
                off_t = max(0.0, float(off_t) - float(self._off_epsilon_sec))
                events.append(('off', float(off_t), midi_pitch, 0))
            elif start >= su:
                on_t = self._seconds_between(su, start, segs)
                dur_t = self._seconds_between(start, float(n.time + n.duration), segs)
                events.append(('on', float(on_t), midi_pitch, vel))
                off_t = float(on_t + max(0.0, dur_t) - float(self._off_epsilon_sec))
                events.append(('off', max(0.0, off_t), midi_pitch, 0))
        # Sort by time, with 'off' before 'on' at equal times
        events.sort(key=lambda e: (e[1], 0 if e[0] == 'off' else 1))

        # Record BPM and relative start units for playhead mapping
        try:
            self._start_units = float(su)
            self._bpm = float(segs[0][2]) if segs else 120.0
        except Exception:
            pass
        try:
            self._start_midi_sync(segs, su)
        except Exception:
            pass
        self._run_events_with_midi(events)

    def _build_events_from_time(self, start_units: float, score) -> List[Tuple[str, float, int, int]]:
        segs = self._get_tempo_segments(score)
        su = float(max(0.0, start_units))
        # Record BPM and start units so UI can compute playhead
        try:
            self._bpm = float(segs[0][2]) if segs else 120.0
            self._start_units = float(su)
        except Exception:
            pass
        events: List[Tuple[str, float, int, int]] = []
        for n in score.events.note:
            start = float(n.time)
            end = float(n.time + n.duration)
            # Skip notes shorter than threshold in time units
            if float(getattr(n, 'duration', 0.0) or 0.0) < float(self._min_duration_units):
                continue
            app_pitch = int(n.pitch)
            midi_pitch = max(0, min(127, app_pitch + self._pitch_offset))
            vel = int(getattr(n, 'velocity', 64) or 64)
            if end <= su:
                continue
            if start < su < end:
                # Start now; schedule off at remaining duration
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
            try:
                self._stop_midi_sync(send_stop=True)
            except Exception:
                pass
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
            self._stop_midi_sync(send_stop=True)
        except Exception:
            pass
        try:
            if self._thread is not None and self._thread.is_alive():
                self._thread.join(timeout=0.5)
        except Exception:
            pass
        self._thread = None
        if self._playback_type == 'internal_synth' and self._synth is not None:
            try:
                # Fade out to avoid clicks, then stop
                self._synth.fade_out_and_stop(50)
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

    def audition_note(self, pitch: int = 40, velocity: int = 80, duration_sec: float = 0.2) -> None:
        """Play a short audition note using the current playback backend."""
        if self.is_playing():
            return
        try:
            app_pitch = int(pitch)
        except Exception:
            app_pitch = 40
        midi_pitch = max(0, min(127, int(app_pitch) + int(self._pitch_offset)))
        vel = int(max(1, min(127, velocity)))
        dur = float(max(0.02, duration_sec))

        def _run():
            if self._playback_type == 'internal_synth' and WavetableSynth is not None:
                if self._synth is None:
                    try:
                        self._synth = WavetableSynth()
                    except Exception:
                        return
                try:
                    self._synth.note_on(int(midi_pitch), int(vel))
                    time.sleep(dur)
                    self._synth.note_off(int(midi_pitch))
                except Exception:
                    pass
                return
            # MIDI backend
            try:
                self._ensure_port()
            except Exception:
                return
            if self._out is None:
                return
            try:
                self._note_on(int(midi_pitch), int(vel))
                time.sleep(dur)
                self._note_off(int(midi_pitch))
            except Exception:
                pass

        th = threading.Thread(target=_run, daemon=True)
        th.start()

    def is_playing(self) -> bool:
        return bool(self._running)

    def get_playhead_time(self, score=None) -> Optional[float]:
        """Return current playhead position in app units (ticks) under variable tempo.

        Uses tempo segments to invert elapsed seconds back into units from `self._start_units`.
        """
        if not bool(self._running):
            return None
        try:
            elapsed = max(0.0, time.time() - float(self._t0))
            # Build segments if score provided; else fall back to linear mapping
            if score is None:
                # Fallback when score is unavailable: interpret self._bpm as seconds-per-unit
                s_per_unit = float(self._bpm) if self._bpm > 0 else (60.0 / (120.0 * float(QUARTER_NOTE_UNIT)))
                units = float(self._start_units) + float(elapsed) / float(s_per_unit)
                return units
            segs = self._get_tempo_segments(score)
            u = self._units_from_elapsed(float(elapsed), float(self._start_units), segs)
            return u
        except Exception:
            return None

    # ---- Tempo mapping helpers ----
    def _get_tempo_segments(self, score) -> List[Tuple[float, float, float]]:
        """Return list of tempo segments: (start_units, end_units, seconds_per_unit).

        - Uses SCORE.events.tempo. Each event has `time`, `duration` (units), `tempo` (markers per minute).
        - For each event, seconds per unit = 60 / (tempo * duration_units).
        - Segments last until the next event's start; the last extends indefinitely.
        - If no tempo events, fall back to quarter-note BPM 120: seconds per unit = 60 / (120 * QUARTER_NOTE_UNIT).
        """
        segs: List[Tuple[float, float, float]] = []
        try:
            lst = sorted(list(getattr(score.events, 'tempo', []) or []), key=lambda e: float(getattr(e, 'time', 0.0) or 0.0))
        except Exception:
            lst = []
        if not lst:
            return [(0.0, float('inf'), 60.0 / (120.0 * float(QUARTER_NOTE_UNIT)))]
        for i, ev in enumerate(lst):
            start = float(getattr(ev, 'time', 0.0) or 0.0)
            _dur = float(getattr(ev, 'duration', 0.0) or 0.0)
            s_per_unit = self._calculate_tempo(ev)
            # Tempo stays active until the next tempo event starts
            if i + 1 < len(lst):
                next_start = float(getattr(lst[i + 1], 'time', 0.0) or 0.0)
                end = max(start, next_start)
            else:
                end = float('inf')
            segs.append((start, end, float(s_per_unit)))
        return segs

    def _seconds_between(self, a_units: float, b_units: float, segs: List[Tuple[float, float, float]]) -> float:
        """Integrate seconds from a_units to b_units across tempo segments.
        sec = units * seconds_per_unit, piecewise per tempo segment.
        If b_units exceeds last segment end, carry last segment's seconds_per_unit forward.
        """
        if b_units <= a_units:
            return 0.0
        total = 0.0
        # Iterate segments overlapping [a_units, b_units)
        for i, (s, e, s_per_unit) in enumerate(segs):
            if e <= a_units:
                continue
            if s >= b_units:
                break
            lo = max(a_units, s)
            hi = min(b_units, e)
            if hi > lo:
                total += (hi - lo) * float(s_per_unit)
        # If b_units extends beyond the last segment end, carry last tempo forward
        if segs and b_units > segs[-1][1]:
            _s_last, e_last, s_per_unit_last = segs[-1]
            lo = max(a_units, e_last)
            hi = b_units
            if hi > lo:
                total += (hi - lo) * float(s_per_unit_last)
        return total

    def _units_from_elapsed(self, elapsed_sec: float, start_units: float, segs: List[Tuple[float, float, float]]) -> float:
        """Invert seconds→units from start_units across tempo segments.

        Walk segments from start_units forward subtracting their seconds length until remainder,
        then convert remainder to units within the current segment.
        """
        u = float(start_units)
        rem = float(elapsed_sec)
        # Find the segment index where start_units lies
        idx = 0
        for i, (s, e, _s_per_unit) in enumerate(segs):
            if s <= start_units < e:
                idx = i
                break
            if start_units >= e:
                idx = i + 1
        # Walk segments
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
                # Partial within this segment
                u += rem / float(s_per_unit)
                rem = 0.0
                return u
            idx += 1
        # If beyond last segment, carry last tempo
        if segs and rem > 0.0:
            _s, _e, s_per_unit_last = segs[-1]
            u += rem / float(s_per_unit_last)
        return u

    def _calculate_tempo(self, tempo_event) -> float:
        """Return seconds-per-unit scaling for a `Tempo` event.

        Definition: `tempo` means markers-per-minute for this event, where one marker spans
        `duration` units. Therefore, seconds per unit = 60 / (tempo * duration).
        """
        try:
            tpm = float(getattr(tempo_event, 'tempo', 60.0) or 60.0)
        except Exception:
            tpm = 60.0
        try:
            dur_units = float(getattr(tempo_event, 'duration', 0.0) or 0.0)
        except Exception:
            dur_units = 0.0
        if dur_units <= 0.0:
            # Fallback to quarter-BPM 120 if invalid
            return 60.0 / (120.0 * float(QUARTER_NOTE_UNIT))
        return 60.0 / (float(tpm) * float(dur_units))

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
