from __future__ import annotations
import threading
import time
from typing import Dict, Optional

import numpy as np
import sounddevice as sd


class WavetableSynth:
    def __init__(self, sample_rate: int = 48000, blocksize: int = 256, device: Optional[str] = None) -> None:
        self.sample_rate = int(sample_rate)
        self.blocksize = int(blocksize)
        self._stream: Optional[sd.OutputStream] = None
        self._lock = threading.RLock()
        self._voices: Dict[int, dict] = {}
        # Default wavetables (mono: use left only)
        self._wt_left = self._make_sine_table(1024)
        self._wt_right = self._make_sine_table(1024)
        # ADSR in seconds and sustain level 0..1
        self.attack = 0.005
        self.decay = 0.05
        self.sustain = 0.6
        self.release = 0.1
        # Preferred output device name (None = default)
        self._device_name: Optional[str] = device
        self.gain = 0.35
        # Pitch reference (A4 = MIDI 69)
        self._a4_midi = 69
        # Fade-out state
        self._fading: bool = False

    def _make_sine_table(self, n: int) -> np.ndarray:
        t = np.arange(n, dtype=np.float32)
        return np.sin(2 * np.pi * t / float(n)).astype(np.float32)

    def set_wavetables(self, left: np.ndarray, right: Optional[np.ndarray] = None) -> None:
        with self._lock:
            self._wt_left = np.asarray(left, dtype=np.float32).copy()
            if right is None:
                self._wt_right = self._wt_left
            else:
                self._wt_right = np.asarray(right, dtype=np.float32).copy()

    def set_adsr(self, attack_seconds: float, decay_seconds: float, sustain_level: float, release_seconds: float) -> None:
        with self._lock:
            self.attack = max(0.0, float(attack_seconds))
            self.decay = max(0.0, float(decay_seconds))
            self.sustain = float(min(1.0, max(0.0, sustain_level)))
            self.release = max(0.0, float(release_seconds))

    def _midi_to_freq(self, midi_note: int) -> float:
        return 440.0 * (2.0 ** ((float(midi_note) - float(self._a4_midi)) / 12.0))

    def _ensure_stream(self) -> None:
        if self._stream is not None:
            return
        self._stream = sd.OutputStream(
            samplerate=self.sample_rate,
            blocksize=self.blocksize,
            channels=2,
            dtype='float32',
            callback=self._callback,
            device=self._device_name if self._device_name else None,
        )
        self._stream.start()

    def _callback(self, outdata, frames: int, time_info, status):
        # Prepare output buffer
        out = np.zeros((frames, 2), dtype=np.float32)
        with self._lock:
            if not self._voices:
                outdata[:] = out
                return
            # Render each active voice
            for k, v in list(self._voices.items()):
                phase = float(v['phase'])
                inc = float(v['inc'])
                wt_l = v['wt_l']
                wt_r = v['wt_r']
                wt_len = float(wt_l.shape[0])
                # Envelope state
                env_state = v['env_state']
                env_level = float(v['env_level'])
                held = bool(v['held'])
                vel = float(v['vel'])
                # ADSR in samples
                a_s = max(1, int(round(self.attack * self.sample_rate)))
                d_s = max(1, int(round(self.decay * self.sample_rate)))
                r_s = max(1, int(round(self.release * self.sample_rate)))
                sus = float(self.sustain)

                l_idx = np.empty(frames, dtype=np.int32)
                r_idx = np.empty(frames, dtype=np.int32)
                env = np.empty(frames, dtype=np.float32)
                for i in range(frames):
                    # Table lookup
                    idx = int(phase) % wt_l.shape[0]
                    l_idx[i] = idx
                    r_idx[i] = idx
                    phase += inc
                    if phase >= wt_len:
                        phase -= wt_len

                    # Envelope step
                    if env_state == 'attack':
                        env_level += 1.0 / a_s
                        if env_level >= 1.0:
                            env_level = 1.0
                            env_state = 'decay'
                    elif env_state == 'decay':
                        if env_level > sus:
                            env_level -= max(0.0, (1.0 - sus) / d_s)
                            if env_level <= sus:
                                env_level = sus
                                env_state = 'sustain'
                        else:
                            env_state = 'sustain'
                    elif env_state == 'sustain':
                        if not held:
                            env_state = 'release'
                    elif env_state == 'release':
                        env_level -= max(0.0, sus / r_s)
                        if env_level <= 0.0:
                            env_level = 0.0
                            env_state = 'off'
                    env[i] = env_level

                # Apply voice to output
                out[:, 0] += (wt_l[l_idx] * env * vel)
                out[:, 1] += (wt_r[r_idx] * env * vel)
                # Update voice state
                v['phase'] = phase
                v['env_level'] = float(env_level)
                v['env_state'] = env_state
                if env_state == 'off':
                    # Remove finished voice
                    self._voices.pop(k, None)

        # Apply master gain and clip
        out *= float(self.gain)
        np.clip(out, -1.0, 1.0, out=out)
        outdata[:] = out

    def note_on(self, midi_note: int, velocity: int) -> None:
        self._ensure_stream()
        freq = self._midi_to_freq(int(midi_note))
        inc = (float(self._wt_left.shape[0]) * freq) / float(self.sample_rate)
        with self._lock:
            self._voices[int(midi_note)] = {
                'phase': 0.0,
                'inc': float(inc),
                'wt_l': self._wt_left,
                'wt_r': self._wt_right,
                'env_state': 'attack',
                'env_level': 0.0,
                'held': True,
                'vel': float(np.clip(velocity, 0, 127)) / 127.0,
            }

    def note_off(self, midi_note: int) -> None:
        with self._lock:
            v = self._voices.get(int(midi_note))
            if v is not None:
                v['held'] = False
                if v['env_state'] in ('attack', 'decay', 'sustain'):
                    v['env_state'] = 'release'

    def all_notes_off(self) -> None:
        with self._lock:
            for v in self._voices.values():
                v['held'] = False
                if v['env_state'] in ('attack', 'decay', 'sustain'):
                    v['env_state'] = 'release'

    def stop(self) -> None:
        with self._lock:
            self._voices.clear()
        if self._stream is not None:
            try:
                self._stream.stop()
                self._stream.close()
            except Exception:
                pass
            self._stream = None

    def is_running(self) -> bool:
        return self._stream is not None

    def set_output_device(self, device_name: Optional[str]) -> None:
        # Change output device; restart stream if currently running
        with self._lock:
            self._device_name = str(device_name) if device_name else None
            if self._stream is not None:
                try:
                    self._stream.stop()
                    self._stream.close()
                except Exception:
                    pass
                self._stream = None

    def fade_out_and_stop(self, duration_ms: int = 150) -> None:
        # Gracefully ramp down gain and stop the stream to avoid clicks
        if self._stream is None:
            # Nothing to fade
            self.stop()
            return
        try:
            if self._fading:
                return
            self._fading = True
        except Exception:
            pass

        def _do_fade():
            try:
                steps = max(1, int(duration_ms / 10))
                step_s = max(0.001, float(duration_ms) / float(steps) / 1000.0)
                with self._lock:
                    start_gain = float(self.gain)
                for i in range(steps):
                    g = max(0.0, start_gain * (1.0 - float(i + 1) / float(steps)))
                    with self._lock:
                        self.gain = float(g)
                    time.sleep(step_s)
                try:
                    self.all_notes_off()
                except Exception:
                    pass
                self.stop()
                # Restore gain to the previous value for subsequent playback
                with self._lock:
                    self.gain = float(start_gain)
            finally:
                try:
                    self._fading = False
                except Exception:
                    pass

        th = threading.Thread(target=_do_fade, daemon=True)
        th.start()
