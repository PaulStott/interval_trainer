# detect_pitch.py

import numpy as np
import sounddevice as sd
import threading
import time
from math import log2

NOTE_NAMES = ['C', 'C#/Db', 'D', 'D#/Eb', 'E', 'F', 'F#/Gb', 'G', 'G#/Ab', 'A', 'A#/Bb', 'B']
SAMPLE_RATE = 44100
FRAME_DURATION = 0.03

devices = sd.query_devices()
internal_mic = [i for i, d in enumerate(devices) if "Microphone" in d['name']]
if internal_mic:
    sd.default.device = (internal_mic[0], 1)

def yin_pitch(signal, fs, w_len=None, threshold=0.15, min_freq=50, max_freq=1000):
    if w_len is None:
        w_len = len(signal)

    signal = signal[:w_len]
    # Step 1: Difference function
    d = np.zeros(w_len // 2)
    for tau in range(1, len(d)):
        diff = signal[:-tau] - signal[tau:]
        d[tau] = np.sum(diff ** 2)

    # Step 2: Cumulative mean normalized difference function
    d[0] = 1  # prevent division by zero
    cumulative_sum = np.cumsum(d[1:])  # cumulative sum excluding d[0]
    d_prime = np.empty_like(d)
    d_prime[0] = 1
    for tau in range(1, len(d)):
        d_prime[tau] = d[tau] * tau / cumulative_sum[tau - 1] if cumulative_sum[tau - 1] != 0 else 1

    # Step 3: Absolute threshold
    candidates = np.where(d_prime < threshold)[0]
    if len(candidates) == 0:
        return None  # no pitch found below threshold

    tau = candidates[0]

    # Step 4: Parabolic interpolation for better precision
    if tau + 1 < len(d_prime) and tau - 1 >= 0:
        y0, y1, y2 = d_prime[tau - 1], d_prime[tau], d_prime[tau + 1]
        denom = 2 * (2 * y1 - y2 - y0)
        if denom != 0:
            tau_adjusted = tau + (y2 - y0) / denom
        else:
            tau_adjusted = tau
    else:
        tau_adjusted = tau

    # Step 5: Convert lag to frequency
    frequency = fs / tau_adjusted

    # Filter frequencies outside the allowed range
    if frequency < min_freq or frequency > max_freq:
        return None

    return frequency

def freq_to_midi(freq):
    return 69 + 12 * np.log2(freq / 440.0)

def midi_to_note_name(midi_num):
    midi_num = int(round(midi_num))
    octave = (midi_num // 12) - 1
    note = NOTE_NAMES[midi_num % 12]
    return f"{note}{octave}"

def pitch_class_difference(m_detected, m_target):
    """
    Computes the shortest distance in semitones between two pitch classes,
    disregarding octave. Returns a signed difference in cents (±600 max).
    """
    pc_detected = int(round(m_detected)) % 12
    pc_target = int(round(m_target)) % 12
    semitone_diff = (pc_detected - pc_target) % 12
    if semitone_diff > 6:
        semitone_diff -= 12
    return semitone_diff * 100  # Convert to cents

class PitchDetector:
    def __init__(self, tonic_freq, target_interval_semitones, tolerance_cents=50):
        self.tonic_freq = tonic_freq
        self.target_interval_semitones = target_interval_semitones
        self.tolerance_cents = tolerance_cents
        self.stop_event = threading.Event()
        self.correct_detected = False
        self.last_detected_note = None
        self._lock = threading.Lock()

        # Compute the pitch class of the target note
        tonic_midi = int(round(freq_to_midi(self.tonic_freq)))
        target_midi = tonic_midi + self.target_interval_semitones
        self.target_pc = target_midi % 12

    def _audio_callback(self, indata, frames, time_info, status):
        if status:
            print(f"Audio input status: {status}")
        with self._lock:
            if self.correct_detected:
                return

        audio = indata[:, 0]
        pitch = yin_pitch(audio, SAMPLE_RATE)
        if pitch is None:
            return

        m_detected = freq_to_midi(pitch)
        tonic_midi = freq_to_midi(self.tonic_freq)
        m_target = tonic_midi + self.target_interval_semitones

        cents_diff = pitch_class_difference(m_detected, m_target)

        detected_note = midi_to_note_name(m_detected)
        target_note = midi_to_note_name(m_target)

        print(f"Detected pitch: {pitch:.2f} Hz → {detected_note}, "
            f"Target: {target_note}, Pitch class diff: {cents_diff:.1f} cents")

        with self._lock:
            self.last_detected_note = detected_note
            self.correct_detected = abs(cents_diff) <= self.tolerance_cents

    def start_listening(self, duration_sec=5):
        with self._lock:
            self.correct_detected = False
            self.last_detected_note = None
            self.stop_event.clear()

        with sd.InputStream(device=sd.default.device,
                            channels=1,
                            samplerate=SAMPLE_RATE,
                            blocksize=int(FRAME_DURATION * SAMPLE_RATE),
                            callback=self._audio_callback):
            time.sleep(duration_sec)
        self.stop_event.set()

    def wait_for_detection(self, timeout=None):
        self.stop_event.wait(timeout)
        with self._lock:
            return self.correct_detected, self.last_detected_note

    def detect_pitch_within_bar(self, duration_sec=3, timeout=5):
        self.start_listening(duration_sec=duration_sec)
        return self.wait_for_detection(timeout=timeout)

    def stop(self):
        self.stop_event.set()