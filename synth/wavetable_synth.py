from __future__ import annotations
import threading
import time
from typing import Optional, Dict

import numpy as np
import sounddevice as sd

from utils.CONSTANT import QUARTER_NOTE_UNIT
from file_model.SCORE import SCORE


class WavetableSynth:
    """A simple stereo wavetable synth with per-note envelopes.

    - Drawn wavetables for left/right channels (single-cycle, -1..+1)
    - ADSR-like envelope: attack fixed short, sustain as exponential fade over `sustain_fade_seconds`,
      release on note-off over `release_seconds`.
    - Polyphonic mixing (basic) with per-voice state.
    """

    def __init__(self, samplerate: int = 44100) -> None:
        self.samplerate = int(samplerate)
        self._wt_left = np.sin(2*np.pi*np.linspace(0, 1, 512, endpoint=False)).astype(np.float32)
        self._wt_right = self._wt_left.copy()
        self._voices: Dict[int, dict] = {}
        self._lock = threading.RLock()
        self._stream: Optional[sd.OutputStream] = None
        self._running = False
        # Envelope (ADSR) settings
        self.attack_seconds: float = 0.01
        self.decay_seconds: float = 0.10
        self.sustain_level: float = 0.7
        self.release_seconds: float = 0.2
        self._bpm: float = 120.0
        self._audio_thread: Optional[threading.Thread] = None
        # Pitch mapping: app pitch 49 == A4 (440 Hz)
        self._a4_pitch_index: int = 49
        # Master gain (0.5 makes output half as loud)
        self.master_gain: float = 0.25

    # ---- Config ----
    def set_wavetables(self, left: np.ndarray, right: np.ndarray) -> None:
        left = np.asarray(left, dtype=np.float32)
        right = np.asarray(right, dtype=np.float32)
        if left.ndim != 1 or right.ndim != 1 or len(left) < 8 or len(right) < 8:
            raise ValueError("Wavetable arrays must be 1-D with length >= 8")
        self._wt_left = left
        self._wt_right = right

    def set_adsr(self, attack_seconds: float, decay_seconds: float, sustain_level: float, release_seconds: float) -> None:
        self.attack_seconds = max(0.0, float(attack_seconds))
        self.decay_seconds = max(0.0, float(decay_seconds))
        self.sustain_level = float(np.clip(sustain_level, 0.0, 1.0))
        self.release_seconds = max(0.0, float(release_seconds))

    # ---- Playback ----
    def start(self) -> None:
        if self._stream is not None:
            return
        self._running = True
        self._stream = sd.OutputStream(samplerate=self.samplerate, channels=2, dtype='float32', callback=self._callback)
        self._stream.start()

    def stop(self) -> None:
        self._running = False
        try:
            if self._stream is not None:
                self._stream.stop()
                self._stream.close()
        except Exception:
            pass
        self._stream = None
        with self._lock:
            self._voices.clear()

    def set_a4_pitch_index(self, pitch_index: int) -> None:
        self._a4_pitch_index = int(pitch_index)

    def _pitch_to_freq(self, pitch: int) -> float:
        # Anchor: app pitch `self._a4_pitch_index` corresponds to 440 Hz
        return 440.0 * (2.0 ** ((int(pitch) - int(self._a4_pitch_index)) / 12.0))

    def note_on(self, midi_pitch: int, velocity: int = 100) -> None:
        freq = self._pitch_to_freq(int(midi_pitch))
        amp = max(0.0, min(1.0, velocity / 127.0))
        with self._lock:
            self._voices[midi_pitch] = {
                'freq': float(freq),
                'amp': float(amp),
                'phase_l': 0.0,
                'phase_r': 0.0,
                'state': 'attack',  # 'attack','decay','sustain','release'
                'env': 0.0,
                'started': time.time(),
                'released': None,
            }

    def note_off(self, midi_pitch: int) -> None:
        with self._lock:
            v = self._voices.get(midi_pitch)
            if v:
                v['state'] = 'release'
                v['released'] = time.time()

    # ---- SCORE scheduling ----
    def play_score(self, score: SCORE) -> None:
        # Extract tempo from first text like "120/4", else 120
        bpm = 120.0
        try:
            for t in score.events.text:
                s = str(getattr(t, 'text', ''))
                if s and '/' in s:
                    b = float(s.split('/')[0])
                    bpm = b
                    break
        except Exception:
            pass
        self._bpm = float(bpm)

        # Start audio
        self.start()

        # Build schedule
        events = []
        for n in score.events.note:
            start_sec = (float(n.time) / QUARTER_NOTE_UNIT) * (60.0 / self._bpm)
            dur_sec = (float(n.duration) / QUARTER_NOTE_UNIT) * (60.0 / self._bpm)
            events.append(('on', start_sec, int(n.pitch), 100))
            events.append(('off', start_sec + max(0.0, dur_sec), int(n.pitch), 0))
        events.sort(key=lambda e: e[1])

        # Schedule in a background thread
        def _runner():
            t0 = time.time()
            for kind, t_rel, pitch, vel in events:
                if not self._running:
                    break
                now = time.time()
                delay = max(0.0, t0 + t_rel - now)
                if delay > 0:
                    time.sleep(delay)
                if kind == 'on':
                    self.note_on(pitch, vel)
                else:
                    self.note_off(pitch)
        th = threading.Thread(target=_runner, daemon=True)
        th.start()
        self._audio_thread = th

    # ---- audio callback ----
    def _callback(self, outdata, frames, time_info, status):
        if not self._running:
            outdata[:] = 0.0
            return
        # Prepare buffers
        l = np.zeros(frames, dtype=np.float32)
        r = np.zeros(frames, dtype=np.float32)
        dt = 1.0 / self.samplerate
        # Precompute per-sample increments for ADSR; handle zero durations
        atk_step = 1.0 / max(1e-9, self.attack_seconds * self.samplerate) if self.attack_seconds > 0 else 1.0
        dcy_total = max(1e-9, self.decay_seconds * self.samplerate)
        rel_step = 1.0 / max(1e-9, self.release_seconds * self.samplerate) if self.release_seconds > 0 else 1.0
        wtL = self._wt_left
        wtR = self._wt_right
        lenL = len(wtL)
        lenR = len(wtR)
        with self._lock:
            remove = []
            for key, v in list(self._voices.items()):
                freq = v['freq']
                amp = v['amp']
                phase_l = v['phase_l']
                phase_r = v['phase_r']
                env = v['env']
                state = v['state']
                inc = freq / self.samplerate
                for i in range(frames):
                    # ADSR envelope progression
                    if state == 'attack':
                        if self.attack_seconds <= 0:
                            env = 1.0
                            state = 'decay'
                        else:
                            env += atk_step
                            if env >= 1.0:
                                env = 1.0
                                state = 'decay'
                    elif state == 'decay':
                        if self.decay_seconds <= 0:
                            env = self.sustain_level
                            state = 'sustain'
                        else:
                            # Linear decay from 1.0 to sustain_level over decay_seconds
                            target = self.sustain_level
                            if env > target:
                                env -= (1.0 - target) / dcy_total
                                if env <= target:
                                    env = target
                                    state = 'sustain'
                            else:
                                env = target
                                state = 'sustain'
                    elif state == 'sustain':
                        env = self.sustain_level
                    elif state == 'release':
                        if self.release_seconds <= 0:
                            env = 0.0
                        else:
                            env -= rel_step
                            if env <= 0.0:
                                env = 0.0
                    # skip accumulation if silent during release
                    if env <= 1e-6 and state == 'release':
                        phase_l += inc
                        phase_r += inc
                        continue
                    # wavetable sampling
                    idx_l = int((phase_l % 1.0) * lenL)
                    idx_r = int((phase_r % 1.0) * lenR)
                    l[i] += wtL[idx_l] * amp * env
                    r[i] += wtR[idx_r] * amp * env
                    phase_l += inc
                    phase_r += inc
                v['phase_l'] = phase_l
                v['phase_r'] = phase_r
                v['env'] = env
                v['state'] = state
                if env < 1e-5 and state == 'release':
                    remove.append(key)
            for k in remove:
                self._voices.pop(k, None)
        # Simple limiter
        out = np.stack([l, r], axis=1)
        # Apply master gain before limiting
        out *= float(self.master_gain)
        out = np.clip(out, -1.0, 1.0)
        outdata[:frames, :] = out


def seconds_from_units(units: float, bpm: float) -> float:
    return (units / QUARTER_NOTE_UNIT) * (60.0 / bpm)
