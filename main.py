#main.py

import tkinter as tk
from tkinter import ttk, messagebox
from interval_trainer import IntervalTrainer
import pygame

pygame.mixer.init(frequency=44100, size=-16, channels=1, buffer=512)

# --- Map note names to frequencies (assume equal temperament, A4 = 440 Hz) ---
NOTE_FREQS = {
    "C4": 261.63,
    "C#4": 277.18,
    "D4": 293.66,
    "D#4": 311.13,
    "E4": 329.63,
    "F4": 349.23,
    "F#4": 369.99,
    "G4": 392.00,
    "G#4": 415.30,
    "A4": 440.00,
    "A#4": 466.16,
    "B4": 493.88,
    "C5": 523.25,
}

INTERVALS = [
    ("Minor Second", 1),
    ("Major Second", 2),
    ("Minor Third", 3),
    ("Major Third", 4),
    ("Perfect Fourth", 5),
    ("Tritone", 6),
    ("Perfect Fifth", 7),
    ("Minor Sixth", 8),
    ("Major Sixth", 9),
    ("Minor Seventh", 10),
    ("Major Seventh", 11),
    ("Octave", 12)
]

def start_training():
    bpm = int(bpm_entry.get())
    note_name = note_var.get()
    tonic_freq = NOTE_FREQS[note_name]
    repeats = int(repeats_entry.get())
    mode = feedback_mode.get()

    selected_intervals = [(name, semitones) for name, semitones in INTERVALS if interval_vars[name].get()]
    if not selected_intervals:
        messagebox.showerror("Error", "Please select at least one interval.")
        return

    trainer = IntervalTrainer(
        bpm=bpm,
        tonic_freq=tonic_freq,
        repeats=repeats,
        status_label=status_label,
        start_button=start_button,
        stop_button=stop_button,
        feedback_mode=mode,
        intervals=selected_intervals
    )
    trainer.start()
    window.trainer = trainer  # hold reference

def stop_training():
    if hasattr(window, 'trainer'):
        window.trainer.stop()

window = tk.Tk()
window.title("Interval Trainer")

# --- BPM Entry ---
ttk.Label(window, text="BPM:").grid(row=0, column=0, sticky="e", padx=5, pady=5)
bpm_entry = ttk.Entry(window)
bpm_entry.insert(0, "60")
bpm_entry.grid(row=0, column=1, padx=5, pady=5)

# --- Tonic Note Dropdown ---
ttk.Label(window, text="Tonic note:").grid(row=1, column=0, sticky="e", padx=5, pady=5)
note_var = tk.StringVar(value="A4")
note_dropdown = ttk.Combobox(window, textvariable=note_var, values=list(NOTE_FREQS.keys()), state="readonly", width=10)
note_dropdown.grid(row=1, column=1, padx=5, pady=5)

# --- Repeats Entry ---
ttk.Label(window, text="Repeats:").grid(row=2, column=0, sticky="e", padx=5, pady=5)
repeats_entry = ttk.Entry(window)
repeats_entry.insert(0, "1")
repeats_entry.grid(row=2, column=1, padx=5, pady=5)

# --- Feedback Mode ---
ttk.Label(window, text="Feedback mode:").grid(row=3, column=0, sticky="e", padx=5, pady=5)
feedback_mode = tk.StringVar(value="SLOW")
mode_dropdown = ttk.Combobox(window, textvariable=feedback_mode, values=["SLOW", "FAST"], state="readonly", width=10)
mode_dropdown.grid(row=3, column=1, padx=5, pady=5)

# --- Interval Selection Checkboxes ---
interval_vars = {name: tk.BooleanVar(value=True) for name, _ in INTERVALS}
interval_frame = ttk.LabelFrame(window, text="Select Intervals")
interval_frame.grid(row=0, column=2, rowspan=5, padx=10, pady=5, sticky="nsew")

for i, name in enumerate(interval_vars):
    cb = ttk.Checkbutton(interval_frame, text=name, variable=interval_vars[name])
    cb.grid(row=i, column=0, sticky="w")

# --- Buttons ---
start_button = ttk.Button(window, text="Start", command=start_training)
start_button.grid(row=5, column=0, padx=5, pady=10)

stop_button = ttk.Button(window, text="Stop", command=stop_training, state=tk.DISABLED)
stop_button.grid(row=5, column=1, padx=5, pady=10)

# --- Status Label ---
status_label = ttk.Label(window, text="Idle", anchor="center")
status_label.grid(row=6, column=0, columnspan=3, pady=10)

window.mainloop()