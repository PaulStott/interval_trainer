import numpy as np
import sounddevice as sd
import tkinter as tk
from threading import Thread
import time

SAMPLE_RATE = 44100
WINDOW_SIZE = 2048
MIN_FREQ = 70
MAX_FREQ = 350

NOTE_FREQS = {
    'E2': 82.41,
    'A2': 110.00,
    'D3': 146.83,
    'G3': 196.00,
    'B3': 246.94,
    'E4': 329.63,
}

class TunerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Guitar Tuner")
        self.root.geometry("400x300")
        self.root.configure(bg="black")

        self.canvas = tk.Canvas(root, width=400, height=200, bg="black", highlightthickness=0)
        self.canvas.pack()

        self.note_label = tk.Label(root, text="—", font=("Helvetica", 32), fg="lime", bg="black")
        self.note_label.pack()

        self.freq_label = tk.Label(root, text="", font=("Helvetica", 16), fg="white", bg="black")
        self.freq_label.pack()

        self.running = True
        self.audio_buffer = np.zeros(WINDOW_SIZE)
        self.buffer_index = 0
        self.lock = False

        self.stream = sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=1,
            blocksize=WINDOW_SIZE // 2,
            callback=self.audio_callback
        )
        self.stream.start()

        self.update_thread = Thread(target=self.update_loop)
        self.update_thread.daemon = True
        self.update_thread.start()

        self.root.protocol("WM_DELETE_WINDOW", self.stop)

    def audio_callback(self, indata, frames, time_info, status):
        if status:
            print(status)
        if self.lock:
            return
        chunk = indata[:, 0]
        n = len(chunk)
        if n > WINDOW_SIZE:
            chunk = chunk[:WINDOW_SIZE]
            n = WINDOW_SIZE
        self.audio_buffer[:-n] = self.audio_buffer[n:]
        self.audio_buffer[-n:] = chunk

    def autocorrelate(self, signal):
        signal -= np.mean(signal)
        corr = np.correlate(signal, signal, mode='full')
        corr = corr[len(corr)//2:]
        d = np.diff(corr)
        start = np.nonzero(d > 0)[0]
        if len(start) == 0:
            return None
        start = start[0]
        peak = np.argmax(corr[start:]) + start
        period = peak
        freq = SAMPLE_RATE / period
        if MIN_FREQ < freq < MAX_FREQ:
            return freq
        return None

    def find_nearest_note(self, freq):
        if freq is None:
            return "—", None, None
        nearest = min(NOTE_FREQS.items(), key=lambda item: abs(item[1] - freq))
        name, ref = nearest
        cents = 1200 * np.log2(freq / ref)
        return name, freq, cents

    def draw_needle(self, cents):
        self.canvas.delete("all")
        width = 400
        height = 200
        center_x = width // 2
        center_y = height - 20
        radius = 80

        self.canvas.create_arc(center_x - radius, center_y - radius,
                               center_x + radius, center_y + radius,
                               start=30, extent=120, outline="gray", style=tk.ARC, width=2)

        for i in range(-50, 60, 10):
            angle = np.radians(90 - i * 1.2)
            x1 = center_x + (radius - 10) * np.cos(angle)
            y1 = center_y - (radius - 10) * np.sin(angle)
            x2 = center_x + radius * np.cos(angle)
            y2 = center_y - radius * np.sin(angle)
            self.canvas.create_line(x1, y1, x2, y2, fill="white", width=1)

        if cents is not None:
            cents = max(-50, min(50, cents))
            angle = np.radians(90 - cents * 1.2)
            x = center_x + (radius - 20) * np.cos(angle)
            y = center_y - (radius - 20) * np.sin(angle)
            self.canvas.create_line(center_x, center_y, x, y, fill="red", width=3)

    def update_loop(self):
        while self.running:
            self.lock = True
            buffer_copy = self.audio_buffer.copy()
            self.lock = False

            freq = self.autocorrelate(buffer_copy)
            note, detected, cents = self.find_nearest_note(freq)

            self.note_label.config(text=note)
            if detected is not None:
                self.freq_label.config(text=f"{detected:.2f} Hz   Δ {cents:+.1f} cents")
            else:
                self.freq_label.config(text="No signal")
            self.draw_needle(cents)
            time.sleep(0.05)

    def stop(self):
        self.running = False
        self.stream.stop()
        self.stream.close()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = TunerApp(root)
    root.mainloop()
