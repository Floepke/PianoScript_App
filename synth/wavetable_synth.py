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
        # Optional per-pitch gain map (MIDI note -> gain multiplier)
        self._pitch_gain: Dict[int, float] = {}
        # Velocity companding curve (exponent < 1.0 raises low velocities)
        self._vel_curve_pow: float = 0.6
        # Minimum effective velocity gain floor (after companding)
        self._min_vel_gain: float = 0.06
        # Humanize detune range (± cents)
        self.detune_cents: float = 3.0
        # Humanize interval (seconds between new detune goals)
        self.detune_interval_s: float = 1.0

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

    def set_velocity_curve(self, exponent: float, min_gain: float = 0.06) -> None:
        """Configure velocity companding: output_gain = max(min_gain, (vel/127)**exponent).

        Use exponent < 1.0 to boost low velocities; exponent=1.0 is linear.
        """
        with self._lock:
            self._vel_curve_pow = float(max(0.1, min(4.0, exponent)))
            self._min_vel_gain = float(max(0.0, min(1.0, min_gain)))

    def set_pitch_gain(self, midi_note: int, gain: float) -> None:
        """Set an optional per-pitch gain multiplier (1.0 = neutral)."""
        with self._lock:
            self._pitch_gain[int(midi_note)] = float(max(0.0, gain))

    def set_humanize_detune_cents(self, cents: float) -> None:
        """Set per-note random detune range in cents (0 disables detune)."""
        with self._lock:
            self.detune_cents = float(max(0.0, min(50.0, cents)))

    def set_humanize_interval_s(self, seconds: float) -> None:
        with self._lock:
            self.detune_interval_s = float(max(0.0, seconds))

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
                phase_l = float(v['phase_l'])
                phase_r = float(v['phase_r'])
                inc_base = float(v['inc_base'])
                wt_l = v['wt_l']
                wt_r = v['wt_r']
                wt_len = float(wt_l.shape[0])
                # Envelope state
                env_state = v['env_state']
                env_level = float(v['env_level'])
                held = bool(v['held'])
                vel = float(v['vel'])
                # Humanize detune state (in cents)
                det_cur = float(v.get('detune_current_c', 0.0))
                det_goal = float(v.get('detune_goal_c', 0.0))
                det_steps_left = int(v.get('detune_steps_left', 0))
                # Precompute interval in samples
                interval_samples = max(1, int(round(float(self.detune_interval_s) * float(self.sample_rate))))
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
                    l_idx[i] = int(phase_l) % wt_l.shape[0]
                    r_idx[i] = int(phase_r) % wt_r.shape[0]
                    # Humanize: update detune goal if needed
                    if det_steps_left <= 0:
                        # Choose a new random target within ±detune_cents
                        dc = float(self.detune_cents)
                        if dc > 0.0:
                            try:
                                det_goal = float(np.random.uniform(-dc, dc))
                            except Exception:
                                det_goal = 0.0
                        else:
                            det_goal = 0.0
                        det_steps_left = int(interval_samples)
                    # Slew current detune toward goal linearly
                    step_c = (det_goal - det_cur) / float(max(1, det_steps_left))
                    det_cur += step_c
                    det_steps_left -= 1
                    # Effective increment with current detune
                    det_ratio = 2.0 ** (float(det_cur) / 1200.0)
                    inc_eff = inc_base * float(det_ratio)
                    phase_l += inc_eff
                    phase_r += inc_eff
                    if phase_l >= wt_len:
                        phase_l -= wt_len
                    if phase_r >= wt_len:
                        phase_r -= wt_len

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
                        # Linear release to zero over release time regardless of sustain level.
                        env_level -= (1.0 / r_s)
                        if env_level <= 0.0:
                            env_level = 0.0
                            env_state = 'off'
                    env[i] = env_level

                # Apply voice to output
                # Per-pitch gain multiplier (default 1.0)
                pitch_gain = float(self._pitch_gain.get(int(k), 1.0))
                out[:, 0] += (wt_l[l_idx] * env * vel * pitch_gain)
                out[:, 1] += (wt_r[r_idx] * env * vel * pitch_gain)
                # Update voice state
                v['phase_l'] = float(phase_l)
                v['phase_r'] = float(phase_r)
                v['env_level'] = float(env_level)
                v['env_state'] = env_state
                v['detune_current_c'] = float(det_cur)
                v['detune_goal_c'] = float(det_goal)
                v['detune_steps_left'] = int(det_steps_left)
                if env_state == 'off':
                    # Remove finished voice
                    self._voices.pop(k, None)

        # Apply master gain and clip
        out *= float(self.gain)
        np.clip(out, -1.0, 1.0, out=out)
        outdata[:] = out

    def note_on(self, midi_note: int, velocity: int) -> None:
        """Start or retrigger a voice for the given MIDI note.

        If a voice for this note already exists (e.g., previous note ending
        exactly when the next starts), retrigger its envelope from the current
        level without resetting phase to avoid clicks.
        """
        self._ensure_stream()
        # Base frequency
        freq = self._midi_to_freq(int(midi_note))
        # Apply a small random pitch detune per note (±3 cents)
        dc = float(self.detune_cents)
        if dc > 0.0:
            try:
                detune_cents = float(np.random.uniform(-dc, dc))
            except Exception:
                detune_cents = 0.0
        else:
            detune_cents = 0.0
        detune_ratio = 2.0 ** (float(detune_cents) / 1200.0)
        freq *= float(detune_ratio)
        inc_base = (float(self._wt_left.shape[0]) * freq) / float(self.sample_rate)
        # Velocity companding with floor to ensure audibility of quiet notes
        vel_norm = float(np.clip(velocity, 0, 127)) / 127.0
        vel_f = max(self._min_vel_gain, vel_norm ** float(self._vel_curve_pow))
        with self._lock:
            existing = self._voices.get(int(midi_note))
            if existing is not None and existing.get('env_state') != 'off':
                # Smooth retrigger: continue phase, re-enter attack from current level
                existing['held'] = True
                existing['env_state'] = 'attack'
                # Keep current env_level to avoid discontinuity
                existing['vel'] = vel_f
                # Update base increment in case sample rate or table length changed
                existing['inc_base'] = float(inc_base)
                existing['wt_l'] = self._wt_left
                existing['wt_r'] = self._wt_right
            else:
                # New voice
                # Start at independent random phases for stereo width
                try:
                    start_phase_l = float(np.random.uniform(0.0, float(self._wt_left.shape[0])))
                except Exception:
                    start_phase_l = 0.0
                try:
                    start_phase_r = float(np.random.uniform(0.0, float(self._wt_right.shape[0])))
                except Exception:
                    start_phase_r = 0.0
                # Initialize detune state
                dc = float(self.detune_cents)
                try:
                    det_cur = float(np.random.uniform(-dc, dc)) if dc > 0.0 else 0.0
                    det_goal = float(np.random.uniform(-dc, dc)) if dc > 0.0 else 0.0
                except Exception:
                    det_cur, det_goal = 0.0, 0.0
                steps_left = max(1, int(round(float(self.detune_interval_s) * float(self.sample_rate))))
                self._voices[int(midi_note)] = {
                    'phase_l': float(start_phase_l),
                    'phase_r': float(start_phase_r),
                    'inc_base': float(inc_base),
                    'wt_l': self._wt_left,
                    'wt_r': self._wt_right,
                    'env_state': 'attack',
                    'env_level': 0.0,
                    'held': True,
                    'vel': vel_f,
                    'detune_current_c': float(det_cur),
                    'detune_goal_c': float(det_goal),
                    'detune_steps_left': int(steps_left),
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
