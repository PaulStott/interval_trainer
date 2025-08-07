# 🎸 Building the Interval Trainer as a Standalone macOS App

This guide explains how to convert your Python-based Interval Trainer (which uses `tkinter`, `sounddevice`, `pyttsx3`, etc.) into a standalone `.app` application on macOS using `py2app`.

---

## Requirements

Ensure the following are installed:

- **Python 3.x** (Python ≤3.11 is recommended for compatibility with `py2app`)
- **macOS**
- **Homebrew** (optional, for creating `.dmg` installers)
- **Virtual environment** for isolation

---

## Setup and Compile

This ensures a clean Python environment for packaging:

```bash
python3 -m venv interval_env
source interval_env/bin/activate
```

Install the necessary packages within your virtual environment:

```bash
pip install py2app
pip install numpy sounddevice pyttsx3
```

Add any additional packages you're using (e.g., scipy, aubio) here.

In the root of your project, create a setup.py file. This tells py2app how to build your .app.

from setuptools import setup

```python
APP = ['interval_trainer.py']  # Your main script
DATA_FILES = []  # Add any audio/images here if needed
OPTIONS = {
    'argv_emulation': True,
    'includes': ['numpy', 'sounddevice', 'pyttsx3'],
    'packages': [],
    'plist': {
        'CFBundleName': 'IntervalTrainer',
        'CFBundleDisplayName': 'Interval Trainer',
        'CFBundleIdentifier': 'com.yourname.intervaltrainer',
        'CFBundleVersion': '0.1.0',
        'CFBundleShortVersionString': '0.1.0',
    }
}

setup(
    app=APP,
    name='IntervalTrainer',
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
```

To build the macOS application:

```bash
python setup.py py2app
```
This creates:

1. dist/IntervalTrainer.app: Your macOS application
2. build/: Intermediate build artifacts

To run the generated .app from the terminal:

```bash
open dist/IntervalTrainer.app
```
To generate a .dmg file for distribution:

1. Install create-dmg:

```bash
brew install create-dmg
```

2. Create the disk image:

```bash
create-dmg 'dist/IntervalTrainer.app'
```

## Troubleshooting

- `sounddevice` issues:

Ensure that `portaudio` is correctly bundled and your Mac has granted microphone permissions to the app.

- TTS (`pyttsx3`) fails:

macOS TTS voices may not work when frozen. You might need to fallback to `os.system("say ...")`.

- Missing libraries:

Ensure all required libraries are declared in includes or packages in `setup.py`.

- Resources not loading:

Use `sys._MEIPASS` or `pkg_resources` to load bundled files when frozen.

## Notes

If you include audio files, images, or fonts:

- Add them to `DATA_FILES`
- Use dynamic path resolution in your Python code to handle both development and frozen modes:

```python
import sys
import os

def resource_path(filename):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, filename)
    return os.path.join(os.path.abspath("."), filename)
```
