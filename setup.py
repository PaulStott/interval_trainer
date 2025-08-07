from setuptools import setup

APP = ['main.py']
OPTIONS = {
    'argv_emulation': True,
    'includes': ['pygame', 'numpy'],  # your actual needed packages
    'excludes': ['PyQt6', 'PyQt6.uic'],
}

setup(
    app=APP,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
