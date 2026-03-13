"""py2app build configuration for vvrite."""
import sys
sys.setrecursionlimit(5000)

from setuptools import setup

APP = ["vvrite/main.py"]
DATA_FILES = []
OPTIONS = {
    "argv_emulation": False,
    "plist": {
        "CFBundleName": "vvrite",
        "CFBundleIdentifier": "com.vvrite.app",
        "CFBundleShortVersionString": "1.0.0",  # keep in sync with vvrite/__init__.__version__
        "CFBundleVersion": "1",
        "LSUIElement": True,
        "NSMicrophoneUsageDescription": (
            "vvrite needs microphone access to record and transcribe your speech."
        ),
        "NSHighResolutionCapable": True,
    },
    "packages": [
        "vvrite",
        "mlx",
        "mlx_audio",
        "mlx_lm",
        "transformers",
        "sounddevice",
        "soundfile",
        "numpy",
        "huggingface_hub",
    ],
    "includes": [
        "Quartz",
        "AppKit",
        "Foundation",
        "ApplicationServices",
        "objc",
    ],
    "excludes": [
        "tkinter",
        "unittest",
        "test",
    ],
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={"py2app": OPTIONS},
    setup_requires=["py2app"],
)
