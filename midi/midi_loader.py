from __future__ import annotations
from pathlib import Path
from typing import Optional, Dict, List, Tuple

import pretty_midi
try:
    import mido  # fallback parser
except Exception:
    mido = None

from file_model.SCORE import SCORE
from utils.CONSTANT import QUARTER_NOTE_UNIT


def _seconds_to_units(pm: pretty_midi.PrettyMIDI, t_seconds: float) -> float:
    """Convert an absolute time in seconds to app time units (QUARTER_NOTE_UNIT based).

    Uses PrettyMIDI's time->tick mapping to respect tempo changes, then maps
    ticks to quarter notes via pm.resolution.
    """
    try:
        ticks = pm.time_to_tick(float(t_seconds))
        quarters = float(ticks) / float(pm.resolution or 480)
        return quarters * QUARTER_NOTE_UNIT
    except Exception:
        # Fallback: assume constant tempo estimated by PrettyMIDI
        bpm = float(pm.estimate_tempo() or 120.0)
        quarter_sec = 60.0 / bpm
        return (t_seconds / quarter_sec) * QUARTER_NOTE_UNIT


def midi_load(path: str) -> SCORE:
    """Load a MIDI file and convert it into a SCORE model.

    - Notes mapped to SCORE.events.note with pitch/time/duration
    - Time mapping respects tempo changes via PrettyMIDI's tick conversion
    - Inserts a tempo Text at time 0 using first tempo if available
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"MIDI file not found: {path}")

    # Try PrettyMIDI first; if it fails, fallback to mido
    try:
        pm = pretty_midi.PrettyMIDI(str(p))
    except Exception as exc:
        if mido is None:
            raise
        # Fallback: parse with mido
        return _midi_load_with_mido(str(p))

    score = SCORE().new()

    # Tempo: record first tempo change as Text (e.g., "120/4")
    try:
        times, tempi = pm.get_tempo_changes()
        if isinstance(tempi, (list, tuple)) and len(tempi) > 0:
            bpm = int(round(float(tempi[0])))
            score.new_text(text=f"{bpm}/4", time=0.0, side='<', mm_from_side=5.0, rotated=True)
    except Exception:
        # If tempo extraction fails, skip
        pass

    # Map notes from all non-drum instruments (convert MIDI pitch to app pitch)
    for inst in pm.instruments:
        if getattr(inst, 'is_drum', False):
            continue
        for n in inst.notes:
            start_units = _seconds_to_units(pm, float(n.start))
            end_units = _seconds_to_units(pm, float(n.end))
            duration_units = max(0.0, end_units - start_units)
            # MIDI A4 (69) -> app A4 (49): subtract 20
            app_pitch = int(n.pitch) - 20
            # Simple left/right hand heuristic around app middle C (~40)
            hand = '<' if int(app_pitch) < 40 else '>'
            score.new_note(pitch=int(app_pitch), time=float(start_units), duration=float(duration_units), hand=hand)

    return score


def _midi_load_with_mido(path: str) -> SCORE:
    """Fallback MIDI loader using mido; pairs note on/off and computes seconds across tempo changes."""
    mid = mido.MidiFile(filename=path)
    tpq = int(getattr(mid, 'ticks_per_beat', 480) or 480)
    # Default tempo in microseconds per beat (500k = 120 BPM)
    default_tempo = 500000

    # Collect tempo changes from track 0 or meta across all tracks
    tempo_events: List[Tuple[int, int]] = []  # (abs_ticks, tempo)
    for i, track in enumerate(mid.tracks):
        abs_ticks = 0
        for msg in track:
            abs_ticks += int(getattr(msg, 'time', 0) or 0)
            if msg.type == 'set_tempo':
                tempo_events.append((abs_ticks, int(msg.tempo)))
    tempo_events.sort(key=lambda x: x[0])

    # Build function to convert delta ticks at a given segment tempo to seconds
    def ticks_to_seconds(delta_ticks: int, tempo_us: int) -> float:
        # seconds = delta_ticks * (tempo_us / 1e6) / tpq
        return (float(delta_ticks) * (float(tempo_us) / 1_000_000.0)) / float(tpq)

    # Iterate messages to build absolute seconds timeline per track and pair notes
    score = SCORE().new()

    # First tempo for Text
    bpm0 = 60.0 / ((tempo_events[0][1] if tempo_events else default_tempo) / 1_000_000.0)
    try:
        score.new_text(text=f"{int(round(bpm0))}/4", time=0.0, side='<', mm_from_side=5.0, rotated=True)
    except Exception:
        pass

    # Helper: get current tempo at given absolute ticks
    def tempo_at_ticks(abs_ticks: int) -> int:
        cur = default_tempo
        for t, tempo in tempo_events:
            if abs_ticks >= t:
                cur = tempo
            else:
                break
        return cur

    # For each track, track note stacks by (channel, pitch)
    for track in mid.tracks:
        abs_ticks = 0
        note_stack: Dict[Tuple[int, int], List[Tuple[int, float]]] = {}
        abs_seconds = 0.0
        for msg in track:
            dt_ticks = int(getattr(msg, 'time', 0) or 0)
            if dt_ticks:
                # Advance absolute seconds using tempo at start of segment
                tempo_us = tempo_at_ticks(abs_ticks)
                abs_seconds += ticks_to_seconds(dt_ticks, tempo_us)
                abs_ticks += dt_ticks
            if msg.type == 'note_on' and msg.velocity > 0:
                key = (getattr(msg, 'channel', 0), msg.note)
                note_stack.setdefault(key, []).append((msg.note, abs_seconds))
            elif msg.type in ('note_off', 'note_on'):
                # Treat note_on with velocity 0 as off
                if msg.type == 'note_on' and msg.velocity > 0:
                    continue
                key = (getattr(msg, 'channel', 0), msg.note)
                lst = note_stack.get(key)
                if lst:
                    _, start_sec = lst.pop()  # last started
                    end_sec = abs_seconds
                    start_units = (start_sec / (60.0 / bpm0)) * QUARTER_NOTE_UNIT
                    end_units = (end_sec / (60.0 / bpm0)) * QUARTER_NOTE_UNIT
                    duration_units = max(0.0, end_units - start_units)
                    app_pitch = int(msg.note) - 20
                    hand = '<' if int(app_pitch) < 40 else '>'
                    score.new_note(pitch=int(app_pitch), time=float(start_units), duration=float(duration_units), hand=hand)
        # For any unmatched note_on left, close them with short duration
        for (ch, pitch), lst in note_stack.items():
            for _, start_sec in lst:
                end_sec = start_sec + 0.05
                start_units = (start_sec / (60.0 / bpm0)) * QUARTER_NOTE_UNIT
                end_units = (end_sec / (60.0 / bpm0)) * QUARTER_NOTE_UNIT
                duration_units = max(0.0, end_units - start_units)
                app_pitch2 = int(pitch) - 20
                hand = '<' if int(app_pitch2) < 40 else '>'
                score.new_note(pitch=int(app_pitch2), time=float(start_units), duration=float(duration_units), hand=hand)

    return score
