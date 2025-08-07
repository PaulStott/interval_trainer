import numpy as np
from scipy.io.wavfile import write

def generate_click(filename, frequency, duration_ms=50, sample_rate=44100, amplitude=0.8):
    duration_s = duration_ms / 1000.0
    t = np.linspace(0, duration_s, int(sample_rate * duration_s), endpoint=False)
    
    # Short sine wave burst
    wave = amplitude * np.sin(2 * np.pi * frequency * t)
    
    # Exponential decay envelope
    envelope = np.exp(-60 * t)
    click = (wave * envelope).astype(np.float32)
    
    # Convert to 16-bit PCM
    pcm_click = np.int16(click * 32767)
    write(filename, sample_rate, pcm_click)
    print(f"Saved {filename}")

if __name__ == "__main__":
    generate_click("sounds/click_high.wav", frequency=1600)
    generate_click("sounds/click_low.wav", frequency=1000)
