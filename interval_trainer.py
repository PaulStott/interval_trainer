#interval_trainer.py

import tkinter as tk
import random
import threading
import time
import pygame
import io
import wave
import numpy as np
import queue

from metronome import Metronome
from detect_pitch import PitchDetector

# Constants
ALL_INTERVALS = [
    ("Minor Second", 1), ("Major Second", 2), ("Minor Third", 3), ("Major Third", 4),
    ("Perfect Fourth", 5), ("Tritone", 6), ("Perfect Fifth", 7),
    ("Minor Sixth", 8), ("Major Sixth", 9), ("Minor Seventh", 10),
    ("Major Seventh", 11), ("Octave", 12)
]

BEATS_PER_BAR = 4
DEFAULT_BPM = 60
SAMPLE_RATE = 44100


def generate_sine_wave_wav(frequency, duration_ms, volume=0.1):
    duration = duration_ms / 1000.0
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration), False)
    wave_data = (np.sin(2 * np.pi * frequency * t) * (volume * 32767)).astype(np.int16)

    buffer = io.BytesIO()
    with wave.open(buffer, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(wave_data.tobytes())
    buffer.seek(0)
    return pygame.mixer.Sound(buffer)


def note_frequency(tonic_freq, semitones):
    return tonic_freq * (2 ** (semitones / 12))


class IntervalTrainer:
    def __init__(self, bpm, tonic_freq, repeats, status_label, start_button, stop_button,
                 feedback_mode="SLOW", intervals=None):
        self.bpm = bpm
        self.tonic_freq = tonic_freq
        self.repeats = repeats
        self.status_label = status_label
        self.start_button = start_button
        self.stop_button = stop_button
        self.feedback_mode = feedback_mode.upper()
        self.intervals = intervals if intervals else ALL_INTERVALS

        self.metronome = Metronome(bpm=bpm, beats_per_bar=BEATS_PER_BAR)
        self.current_beat = {'beat': 0, 'bar': 0}
        self.beat_condition = threading.Condition()
        self.stop_event = threading.Event()

        self.metronome.register_callback(self.on_beat)

        self.interval_channel = pygame.mixer.Channel(1)
        self.feedback_channel = pygame.mixer.Channel(2)
        self.name_channel = pygame.mixer.Channel(3)

        self.feedback_sounds = {
            "correct": pygame.mixer.Sound("sounds/correct.wav"),
            "incorrect": pygame.mixer.Sound("sounds/incorrect.wav")
        }

        self.sound_cache = {
            semitone: generate_sine_wave_wav(note_frequency(self.tonic_freq, semitone), duration_ms=600)
            for _, semitone in self.intervals
        }
        self.tonic_sound = generate_sine_wave_wav(self.tonic_freq, duration_ms=600)

        self.name_sounds = {
            "Minor Second": pygame.mixer.Sound("sounds/minor_second.wav"),
            "Major Second": pygame.mixer.Sound("sounds/major_second.wav"),
            "Minor Third": pygame.mixer.Sound("sounds/minor_third.wav"),
            "Major Third": pygame.mixer.Sound("sounds/major_third.wav"),
            "Perfect Fourth": pygame.mixer.Sound("sounds/perfect_fourth.wav"),
            "Tritone": pygame.mixer.Sound("sounds/tritone.wav"),
            "Perfect Fifth": pygame.mixer.Sound("sounds/perfect_fifth.wav"),
            "Minor Sixth": pygame.mixer.Sound("sounds/minor_sixth.wav"),
            "Major Sixth": pygame.mixer.Sound("sounds/major_sixth.wav"),
            "Minor Seventh": pygame.mixer.Sound("sounds/minor_seventh.wav"),
            "Major Seventh": pygame.mixer.Sound("sounds/major_seventh.wav"),
            "Octave": pygame.mixer.Sound("sounds/octave.wav")
        }

    def on_beat(self, beat_num):
        with self.beat_condition:
            if beat_num == 1:
                self.current_beat['bar'] += 1
            self.current_beat['beat'] = beat_num
            self.beat_condition.notify_all()

    def wait_for_bar(self, target_bar):
        with self.beat_condition:
            while self.current_beat['bar'] < target_bar and not self.stop_event.is_set():
                self.beat_condition.wait()

    def bar_duration_sec(self):
        return (60 / self.bpm) * BEATS_PER_BAR

    def wait_for_beat(self, target_beat, target_bar, timeout=None):
        with self.beat_condition:
            start_time = time.time()
            while not (self.current_beat['bar'] == target_bar and self.current_beat['beat'] == target_beat):
                if self.stop_event.is_set():
                    break
                remaining = None
                if timeout is not None:
                    elapsed = time.time() - start_time
                    remaining = max(0, timeout - elapsed)
                    if remaining == 0:
                        break
                self.beat_condition.wait(timeout=remaining)

    def play_feedback(self, correct):
        def feedback_worker():
            sound_key = "correct" if correct else "incorrect"
            self.feedback_channel.play(self.feedback_sounds[sound_key])
            while self.feedback_channel.get_busy() and not self.stop_event.is_set():
                time.sleep(0.01)

        threading.Thread(target=feedback_worker, daemon=True).start()

    def play_interval_sounds(self, semitone_interval):
        current_bar = self.current_beat['bar']
        current_beat = self.current_beat['beat']

        self.interval_channel.play(self.tonic_sound)

        def play_after_next_beat():
            next_beat = (current_beat % BEATS_PER_BAR) + 1
            next_bar = current_bar + (1 if next_beat == 1 else 0)
            self.wait_for_beat(next_beat, next_bar)

            while self.interval_channel.get_busy() and not self.stop_event.is_set():
                time.sleep(0.005)

            self.interval_channel.play(self.sound_cache[semitone_interval])

        threading.Thread(target=play_after_next_beat, daemon=True).start()

    def start(self):
        self.stop_event.clear()
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        threading.Thread(target=self.training_loop, daemon=True).start()

    def stop(self):
        self.stop_event.set()
        self.metronome.stop()

    def detect_pitch_async(self, tonic_freq, semitones, duration_sec, timeout):
        result_queue = queue.Queue()

        def detection_task():
            detector = PitchDetector(tonic_freq=tonic_freq, target_interval_semitones=semitones)
            correct, note = detector.detect_pitch_within_bar(duration_sec=duration_sec, timeout=timeout)
            detector.stop()
            result_queue.put((correct, note))

        threading.Thread(target=detection_task, daemon=True).start()
        return result_queue

    def training_loop(self):
        self.metronome.start()
        try:
            all_trials = []
            for _ in range(self.repeats):
                all_trials += random.sample(self.intervals, len(self.intervals))

            for name, semitones in all_trials:
                if self.stop_event.is_set():
                    self.status_label.after(0, lambda: self.status_label.config(text="Session stopped."))
                    return

                self.status_label.after(0, lambda: self.status_label.config(text="Get ready..."))
                self.wait_for_bar(self.current_beat['bar'] + 1)

                self.status_label.after(0, lambda n=name: self.status_label.config(text=f"Prompt: {n}"))
                self.name_channel.play(self.name_sounds[name])
                self.wait_for_bar(self.current_beat['bar'] + 1)  # Wait for prompt to finish

                self.status_label.after(0, lambda n=name: self.status_label.config(text=f"Your turn: Play {n}"))

                bar_duration = self.bar_duration_sec()
                timeout = bar_duration + 2  # ← define the timeout variable before usage

                detection_queue = self.detect_pitch_async(
                    tonic_freq=self.tonic_freq,
                    semitones=semitones,
                    duration_sec=bar_duration,
                    timeout=timeout  # use the defined variable here
                )

                try:
                    result = detection_queue.get(timeout=timeout)  # use it here as well
                except queue.Empty:
                    result = None

                if result is None:
                    correct = False
                    note = "None"
                else:
                    correct, note = result
                    print(f"[DEBUG] From result queue → correct: {correct}, note: {note}")


                self.status_label.after(0, lambda: self.status_label.config(
                    text=f"Detected: {note if note else 'None'} → {'Correct' if correct else 'Incorrect'}"
                ))
                self.play_feedback(correct)

                next_bar = self.current_beat['bar'] + 1
                self.wait_for_bar(next_bar)

                self.play_interval_sounds(semitones)

        finally:
            self.metronome.stop()
            self.status_label.after(0, lambda: self.status_label.config(text="Session ended."))
            self.start_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)
