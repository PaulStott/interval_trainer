#metronome.py

import pygame
import time
import threading

class Metronome(threading.Thread):
    def __init__(self, bpm, beats_per_bar=4):
        super().__init__(daemon=True)  # Daemon thread so it doesn't block program exit
        self.bpm = bpm
        self.beats_per_bar = beats_per_bar
        self.callbacks = []

        # Load metronome sounds once, assuming pygame.
        #  already initialized
        self.high = pygame.mixer.Sound("sounds/click_high.wav")
        self.low = pygame.mixer.Sound("sounds/click_low.wav")
        self.metronome_channel = pygame.mixer.Channel(0)

        # This event is internal; do not call stop() externally if you want infinite run
        self._stop_event = threading.Event()

    def register_callback(self, callback):
        self.callbacks.append(callback)

    def run(self):
        beat_duration = 60.0 / self.bpm
        next_tick = time.time()
        beat_num = 1
        while True:  # Runs forever unless externally stopped
            # Fire callbacks with current beat number
            for callback in self.callbacks:
                try:
                    callback(beat_num)
                except Exception as e:
                    print(f"Metronome callback error: {e}")

            # Play appropriate click sound
            sound = self.high if beat_num == 1 else self.low
            self.metronome_channel.play(sound)

            # Compute next tick and sleep precisely
            next_tick += beat_duration
            sleep_time = next_tick - time.time()
            if sleep_time > 0:
                time.sleep(sleep_time)
            else:
                # We're late; reset next_tick to now to avoid drift
                next_tick = time.time()

            # Increment beat counter with wrap-around
            beat_num = 1 if beat_num == self.beats_per_bar else beat_num + 1

            # Optional stop check for internal usage (comment out if never want to stop)
            if self._stop_event.is_set():
                break

    def stop(self):
        self._stop_event.set()